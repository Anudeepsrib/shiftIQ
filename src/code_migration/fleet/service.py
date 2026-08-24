"""Fleet-facing orchestration over deterministic ShiftIQ operations."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from code_migration.fleet.audit import OperationLedger, new_record
from code_migration.fleet.auth import actor_var, fleet_trace_id_var
from code_migration.fleet.config import FleetSettings, get_fleet_settings
from code_migration.fleet.errors import (
    ApprovalRequiredError,
    CheckpointNotFoundError,
    MigrationConflictError,
    SourceRevisionChangedError,
)
from code_migration.fleet.github import prepare_github_workspace
from code_migration.fleet.models import AuditMetadata, ToolResult
from code_migration.fleet.tracing import trace_operation
from code_migration.fleet.workspace import WorkspaceManager
from code_migration.operations import (
    analyze_project,
    compliance_scan,
    get_checkpoint,
    list_checkpoints,
    plan_migration,
    rollback_checkpoint,
    run_migration,
    verify_migration,
    visualize_project,
)
from code_migration.registry import create_registry


class FleetMigrationService:
    def __init__(
        self,
        config: FleetSettings | None = None,
        workspaces: WorkspaceManager | None = None,
    ) -> None:
        self.config = config or get_fleet_settings()
        self.workspaces = workspaces or WorkspaceManager(self.config)
        self.ledger = OperationLedger(self.workspaces)

    def _audit(
        self,
        operation_id: str,
        workspace_id: str,
        tool_name: str,
        *,
        migration_type: str | None = None,
        dry_run: bool | None = None,
        risk_level: str = "UNKNOWN",
        checkpoint_id: str | None = None,
        source_revision: str | None = None,
    ) -> AuditMetadata:
        workspace = self.workspaces.get(workspace_id)
        return AuditMetadata(
            operation_id=operation_id,
            workspace_id=workspace_id,
            timestamp=datetime.now(timezone.utc),
            tool_name=tool_name,
            migration_type=migration_type,
            source_sha=workspace.source_sha,
            source_revision=source_revision,
            dry_run=dry_run,
            risk_level=risk_level,
            checkpoint_id=checkpoint_id,
            fleet_trace_id=fleet_trace_id_var.get(),
            actor=actor_var.get(),
        )

    @staticmethod
    def _result(data: dict | list, audit: AuditMetadata | None = None) -> dict[str, Any]:
        return ToolResult(ok=True, data=data, audit=audit).model_dump(mode="json", exclude_none=True)

    def _workspace_result(
        self,
        workspace_id: str,
        data: dict | list,
        audit: AuditMetadata | None = None,
    ) -> dict[str, Any]:
        workspace_path = str(self.workspaces.workspace_path(workspace_id))

        def redact(value):
            if isinstance(value, dict):
                return {key: redact(item) for key, item in value.items()}
            if isinstance(value, list):
                return [redact(item) for item in value]
            if isinstance(value, str):
                return value.replace(workspace_path, "<workspace>").replace(
                    workspace_path.replace("\\", "/"),
                    "<workspace>",
                )
            return value

        return self._result(redact(data), audit)

    def create_workspace(self, ttl_seconds: int | None = None) -> dict[str, Any]:
        metadata = self.workspaces.create(ttl_seconds=ttl_seconds)
        return self._result(metadata.model_dump(mode="json"))

    def prepare_github_workspace(self, repository: str, ref: str = "main") -> dict[str, Any]:
        metadata = prepare_github_workspace(repository, ref=ref, manager=self.workspaces, config=self.config)
        audit = self._audit(str(uuid4()), metadata.workspace_id, "prepare_github_workspace")
        self.ledger.append_audit(audit, event="workspace_prepared")
        return self._result(metadata.model_dump(mode="json"), audit)

    def workspace_status(self, workspace_id: str) -> dict[str, Any]:
        return self._result(self.workspaces.status(workspace_id).model_dump(mode="json"))

    def list_workspace_files(self, workspace_id: str, limit: int = 500) -> dict[str, Any]:
        return self._result({"workspace_id": workspace_id, "files": self.workspaces.list_files(workspace_id, limit=limit)})

    def cleanup_workspace(self, workspace_id: str) -> dict[str, Any]:
        self.workspaces.get(workspace_id, allow_expired=True)
        return self._result({"workspace_id": workspace_id, "deleted": self.workspaces.delete(workspace_id)})

    def list_migrators(self) -> dict[str, Any]:
        data = [
            {
                "name": info.name,
                "description": info.description,
                "version": info.version,
                "supported_extensions": info.supported_extensions,
                "tags": info.tags,
                "source": info.source,
            }
            for info in create_registry().list_all()
        ]
        return self._result(data)

    def analyze(
        self,
        workspace_id: str,
        migration_type: str = "react-hooks",
        include_confidence: bool = True,
    ) -> dict[str, Any]:
        operation_id = str(uuid4())
        path = self.workspaces.workspace_path(workspace_id)
        with trace_operation("shiftiq.analyze", {"shiftiq.workspace_id": workspace_id}, self.config):
            data = analyze_project(
                str(path),
                migration_type,
                include_confidence=include_confidence,
                trusted_root=path,
            )
        risk = (data.get("confidence") or {}).get("risk_level", "UNKNOWN")
        audit = self._audit(operation_id, workspace_id, "analyze", migration_type=migration_type, risk_level=risk)
        self.ledger.append_audit(audit, event="migration_analyzed")
        return self._workspace_result(workspace_id, data, audit)

    def compliance_scan(self, workspace_id: str) -> dict[str, Any]:
        operation_id = str(uuid4())
        path = self.workspaces.workspace_path(workspace_id)
        with trace_operation("shiftiq.compliance_scan", {"shiftiq.workspace_id": workspace_id}, self.config):
            data = compliance_scan(str(path), include_raw=False, trusted_root=path)
        audit = self._audit(operation_id, workspace_id, "compliance_scan")
        self.ledger.append_audit(audit, event="compliance_scanned")
        return self._workspace_result(workspace_id, data, audit)

    def visualize(self, workspace_id: str) -> dict[str, Any]:
        operation_id = str(uuid4())
        path = self.workspaces.workspace_path(workspace_id)
        with trace_operation("shiftiq.visualize", {"shiftiq.workspace_id": workspace_id}, self.config):
            data = visualize_project(str(path), trusted_root=path)
        audit = self._audit(operation_id, workspace_id, "visualize")
        return self._workspace_result(workspace_id, data, audit)

    def plan_migration(self, workspace_id: str, migration_type: str = "react-hooks") -> dict[str, Any]:
        operation_id = str(uuid4())
        path = self.workspaces.workspace_path(workspace_id)
        with trace_operation(
            "shiftiq.plan_migration",
            {"shiftiq.workspace_id": workspace_id, "shiftiq.migration_type": migration_type},
            self.config,
        ):
            data = plan_migration(str(path), migration_type, trusted_root=path)
        risk = (data.get("confidence") or {}).get("risk_level", "UNKNOWN")
        audit = self._audit(operation_id, workspace_id, "plan_migration", migration_type=migration_type, risk_level=risk)
        self.ledger.append_audit(audit, event="migration_planned")
        return self._workspace_result(workspace_id, data, audit)

    def run_migration(
        self,
        workspace_id: str,
        migration_type: str = "react-hooks",
        operation_id: str | None = None,
        dry_run: bool = True,
    ) -> dict[str, Any]:
        if not dry_run:
            raise ApprovalRequiredError("Remote writes use apply_migration after an approved dry run")
        operation_id = operation_id or str(uuid4())
        revision = self.workspaces.fingerprint(workspace_id)
        existing = self.ledger.get(workspace_id, operation_id)
        if existing:
            if existing.action != "dry_run" or existing.migration_type != migration_type or existing.source_revision != revision:
                raise MigrationConflictError("operation_id was already used for different dry-run inputs")
            return existing.result

        path = self.workspaces.workspace_path(workspace_id)
        with trace_operation(
            "shiftiq.run_migration",
            {
                "shiftiq.workspace_id": workspace_id,
                "shiftiq.migration_type": migration_type,
                "shiftiq.dry_run": True,
            },
            self.config,
        ):
            data = run_migration(str(path), migration_type, dry_run=True, trusted_root=path)
        audit = self._audit(
            operation_id,
            workspace_id,
            "run_migration",
            migration_type=migration_type,
            dry_run=True,
            source_revision=revision,
        )
        result = self._workspace_result(workspace_id, data, audit)
        self.ledger.save(
            new_record(
                operation_id=operation_id,
                action="dry_run",
                workspace_id=workspace_id,
                migration_type=migration_type,
                source_revision=revision,
                result=result,
            )
        )
        self.ledger.append_audit(audit, event="migration_dry_run", approved=False)
        return result

    def apply_migration(
        self,
        workspace_id: str,
        dry_run_operation_id: str,
        operation_id: str,
        migration_type: str = "react-hooks",
    ) -> dict[str, Any]:
        existing = self.ledger.get(workspace_id, operation_id)
        if existing:
            if (
                existing.action != "apply"
                or existing.migration_type != migration_type
                or existing.result.get("data", {}).get("dry_run_operation_id") != dry_run_operation_id
            ):
                raise MigrationConflictError("operation_id was already used for different apply inputs")
            return existing.result

        preview = self.ledger.get(workspace_id, dry_run_operation_id)
        if not preview or preview.action != "dry_run" or preview.migration_type != migration_type:
            raise ApprovalRequiredError("A matching dry-run operation is required before apply")
        revision = self.workspaces.fingerprint(workspace_id)
        if revision != preview.source_revision:
            raise SourceRevisionChangedError("Workspace changed after dry run; review a new dry run")

        path = self.workspaces.workspace_path(workspace_id)
        with trace_operation(
            "shiftiq.apply_migration",
            {
                "shiftiq.workspace_id": workspace_id,
                "shiftiq.migration_type": migration_type,
                "shiftiq.dry_run": False,
            },
            self.config,
        ):
            data = run_migration(str(path), migration_type, dry_run=False, trusted_root=path)
            data["dry_run_operation_id"] = dry_run_operation_id
            data["verification"] = verify_migration(str(path), migration_type, trusted_root=path)
        checkpoint_id = data.get("checkpoint_id")
        audit = self._audit(
            operation_id,
            workspace_id,
            "apply_migration",
            migration_type=migration_type,
            dry_run=False,
            checkpoint_id=checkpoint_id,
            source_revision=revision,
        )
        result = self._workspace_result(workspace_id, data, audit)
        self.ledger.save(
            new_record(
                operation_id=operation_id,
                action="apply",
                workspace_id=workspace_id,
                migration_type=migration_type,
                source_revision=revision,
                result=result,
                checkpoint_id=checkpoint_id,
            )
        )
        self.ledger.append_audit(audit, event="migration_applied", approved=True)
        return result

    def verify_migration(self, workspace_id: str, migration_type: str = "react-hooks") -> dict[str, Any]:
        operation_id = str(uuid4())
        path = self.workspaces.workspace_path(workspace_id)
        with trace_operation(
            "shiftiq.verify_migration",
            {"shiftiq.workspace_id": workspace_id, "shiftiq.migration_type": migration_type},
            self.config,
        ):
            data = verify_migration(str(path), migration_type, trusted_root=path)
        audit = self._audit(operation_id, workspace_id, "verify_migration", migration_type=migration_type)
        self.ledger.append_audit(audit, event="migration_verified")
        return self._workspace_result(workspace_id, data, audit)

    def list_checkpoints(self, workspace_id: str) -> dict[str, Any]:
        path = self.workspaces.workspace_path(workspace_id)
        return self._workspace_result(workspace_id, list_checkpoints(str(path), trusted_root=path))

    def get_checkpoint(self, workspace_id: str, checkpoint_id: str) -> dict[str, Any]:
        path = self.workspaces.workspace_path(workspace_id)
        checkpoint = get_checkpoint(str(path), checkpoint_id, trusted_root=path)
        if checkpoint is None:
            raise CheckpointNotFoundError("Checkpoint does not exist")
        return self._workspace_result(workspace_id, checkpoint)

    def preview_rollback(self, workspace_id: str, checkpoint_id: str, operation_id: str | None = None) -> dict[str, Any]:
        operation_id = operation_id or str(uuid4())
        revision = self.workspaces.fingerprint(workspace_id)
        existing = self.ledger.get(workspace_id, operation_id)
        if existing:
            if existing.action != "rollback_preview" or existing.result.get("data", {}).get("checkpoint_id") != checkpoint_id:
                raise MigrationConflictError("operation_id was already used for different rollback inputs")
            return existing.result
        path = self.workspaces.workspace_path(workspace_id)
        data = rollback_checkpoint(str(path), checkpoint_id, dry_run=True, trusted_root=path)
        data["checkpoint_id"] = checkpoint_id
        audit = self._audit(operation_id, workspace_id, "preview_rollback", dry_run=True, source_revision=revision)
        result = self._workspace_result(workspace_id, data, audit)
        self.ledger.save(
            new_record(
                operation_id=operation_id,
                action="rollback_preview",
                workspace_id=workspace_id,
                source_revision=revision,
                result=result,
                checkpoint_id=checkpoint_id,
            )
        )
        return result

    def rollback(
        self,
        workspace_id: str,
        checkpoint_id: str,
        preview_operation_id: str,
        operation_id: str,
    ) -> dict[str, Any]:
        existing = self.ledger.get(workspace_id, operation_id)
        if existing:
            if existing.action != "rollback" or existing.checkpoint_id != checkpoint_id:
                raise MigrationConflictError("operation_id was already used for different rollback inputs")
            return existing.result
        preview = self.ledger.get(workspace_id, preview_operation_id)
        if not preview or preview.action != "rollback_preview" or preview.checkpoint_id != checkpoint_id:
            raise ApprovalRequiredError("A matching rollback preview is required")
        revision = self.workspaces.fingerprint(workspace_id)
        if revision != preview.source_revision:
            raise SourceRevisionChangedError("Workspace changed after rollback preview")
        path = self.workspaces.workspace_path(workspace_id)
        with trace_operation(
            "shiftiq.rollback",
            {"shiftiq.workspace_id": workspace_id, "shiftiq.checkpoint_id": checkpoint_id},
            self.config,
        ):
            data = rollback_checkpoint(str(path), checkpoint_id, dry_run=False, trusted_root=path)
        audit = self._audit(
            operation_id,
            workspace_id,
            "rollback",
            dry_run=False,
            checkpoint_id=checkpoint_id,
            source_revision=revision,
        )
        result = self._workspace_result(workspace_id, data, audit)
        self.ledger.save(
            new_record(
                operation_id=operation_id,
                action="rollback",
                workspace_id=workspace_id,
                source_revision=revision,
                result=result,
                checkpoint_id=checkpoint_id,
            )
        )
        self.ledger.append_audit(audit, event="migration_rolled_back", approved=True)
        return result

    def migration_status(self, workspace_id: str, operation_id: str) -> dict[str, Any]:
        return self._result(self.ledger.status(workspace_id, operation_id))
