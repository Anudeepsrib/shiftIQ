"""Server-owned, quota-bound workspaces for remote agents."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID, uuid4

from code_migration.fleet.config import FleetSettings, get_fleet_settings
from code_migration.fleet.errors import WorkspaceBoundaryError, WorkspaceNotFoundError, WorkspaceQuotaError
from code_migration.fleet.models import WorkspaceMetadata


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _atomic_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            json.dump(data, stream, indent=2, sort_keys=True)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_name, path)
    except Exception:
        try:
            os.unlink(temp_name)
        except OSError:
            pass
        raise


class WorkspaceManager:
    def __init__(self, config: FleetSettings | None = None) -> None:
        self.config = config or get_fleet_settings()
        self.root = self.config.resolved_workspace_root
        self.workspaces_dir = self.root / "workspaces"
        self.metadata_dir = self.root / "metadata"

    @staticmethod
    def validate_id(workspace_id: str) -> str:
        try:
            parsed = UUID(workspace_id)
        except (ValueError, TypeError) as exc:
            raise WorkspaceBoundaryError("Invalid workspace ID") from exc
        if str(parsed) != workspace_id.lower():
            raise WorkspaceBoundaryError("Workspace ID must use canonical UUID form")
        return str(parsed)

    def create(
        self,
        *,
        source_repository: str | None = None,
        source_ref: str | None = None,
        ttl_seconds: int | None = None,
        status: str = "empty",
    ) -> WorkspaceMetadata:
        self.sweep_expired()
        if len(list(self.metadata_dir.glob("*.json"))) >= self.config.workspace_max_count:
            raise WorkspaceQuotaError("Workspace count quota reached")

        workspace_id = str(uuid4())
        created = _utcnow()
        ttl = ttl_seconds or self.config.workspace_ttl_seconds
        metadata = WorkspaceMetadata(
            workspace_id=workspace_id,
            status=status,
            created_at=created,
            expires_at=created + timedelta(seconds=ttl),
            source_repository=source_repository,
            source_ref=source_ref,
        )
        self.workspace_path(workspace_id, must_exist=False).mkdir(parents=True)
        self.save(metadata)
        return metadata

    def workspace_path(self, workspace_id: str, *, must_exist: bool = True) -> Path:
        canonical = self.validate_id(workspace_id)
        self.workspaces_dir.mkdir(parents=True, exist_ok=True)
        root = self.workspaces_dir.resolve()
        candidate = (root / canonical).resolve(strict=False)
        try:
            candidate.relative_to(root)
        except ValueError as exc:
            raise WorkspaceBoundaryError("Workspace path escaped the managed root") from exc
        if must_exist and (not candidate.exists() or not candidate.is_dir()):
            raise WorkspaceNotFoundError("Workspace does not exist")
        return candidate

    def metadata_path(self, workspace_id: str) -> Path:
        return self.metadata_dir / f"{self.validate_id(workspace_id)}.json"

    def get(self, workspace_id: str, *, allow_expired: bool = False) -> WorkspaceMetadata:
        path = self.metadata_path(workspace_id)
        if not path.is_file():
            raise WorkspaceNotFoundError("Workspace does not exist")
        try:
            metadata = WorkspaceMetadata.model_validate_json(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise WorkspaceNotFoundError("Workspace metadata is unavailable") from exc
        if metadata.expires_at <= _utcnow() and not allow_expired:
            metadata.status = "expired"
            self.save(metadata)
            raise WorkspaceNotFoundError("Workspace has expired")
        return metadata

    def save(self, metadata: WorkspaceMetadata) -> None:
        _atomic_json(self.metadata_path(metadata.workspace_id), metadata.model_dump(mode="json"))

    def status(self, workspace_id: str) -> WorkspaceMetadata:
        metadata = self.get(workspace_id)
        workspace = self.workspace_path(workspace_id)
        file_count = 0
        size_bytes = 0
        for path in workspace.rglob("*"):
            if path.is_symlink() or not path.is_file() or ".git" in path.parts:
                continue
            try:
                size_bytes += path.stat().st_size
                file_count += 1
            except OSError:
                continue
        metadata.file_count = file_count
        metadata.size_bytes = size_bytes
        if size_bytes > self.config.workspace_max_mb * 1024 * 1024:
            raise WorkspaceQuotaError("Workspace size quota exceeded")
        self.save(metadata)
        return metadata

    def list_files(self, workspace_id: str, *, limit: int = 500) -> list[str]:
        workspace = self.workspace_path(workspace_id)
        files: list[str] = []
        for path in sorted(workspace.rglob("*")):
            if len(files) >= limit:
                break
            if path.is_symlink() or not path.is_file() or ".git" in path.parts:
                continue
            files.append(path.relative_to(workspace).as_posix())
        return files

    def fingerprint(self, workspace_id: str) -> str:
        """Hash managed file paths and contents to bind approval to a revision."""
        workspace = self.workspace_path(workspace_id)
        digest = hashlib.sha256()
        for path in sorted(workspace.rglob("*")):
            if path.is_symlink() or not path.is_file():
                continue
            relative = path.relative_to(workspace)
            if ".git" in relative.parts or any(part.startswith(".migration-") for part in relative.parts):
                continue
            digest.update(relative.as_posix().encode("utf-8"))
            try:
                with path.open("rb") as stream:
                    for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                        digest.update(chunk)
            except OSError as exc:
                raise WorkspaceBoundaryError("Workspace changed while calculating its revision") from exc
        return digest.hexdigest()

    def delete(self, workspace_id: str) -> bool:
        workspace = self.workspace_path(workspace_id, must_exist=False)
        root = self.workspaces_dir.resolve()
        try:
            workspace.relative_to(root)
        except ValueError as exc:
            raise WorkspaceBoundaryError("Refusing to delete outside the workspace root") from exc
        if workspace.exists():
            shutil.rmtree(workspace)
        metadata = self.metadata_path(workspace_id)
        metadata.unlink(missing_ok=True)
        operations = self.root / "operations" / workspace_id
        if operations.exists():
            shutil.rmtree(operations)
        return True

    def sweep_expired(self) -> int:
        removed = 0
        if not self.metadata_dir.exists():
            return removed
        for path in self.metadata_dir.glob("*.json"):
            try:
                metadata = WorkspaceMetadata.model_validate_json(path.read_text(encoding="utf-8"))
                if metadata.expires_at <= _utcnow():
                    self.delete(metadata.workspace_id)
                    removed += 1
            except (OSError, ValueError, WorkspaceBoundaryError):
                continue
        return removed
