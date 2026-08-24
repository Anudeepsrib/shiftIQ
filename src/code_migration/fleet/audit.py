"""Idempotency records and redacted Fleet/ShiftIQ audit events."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

from code_migration.fleet.errors import MigrationConflictError
from code_migration.fleet.models import AuditMetadata, OperationRecord
from code_migration.fleet.workspace import WorkspaceManager, _atomic_json


class OperationLedger:
    def __init__(self, workspaces: WorkspaceManager) -> None:
        self.workspaces = workspaces
        self.root = workspaces.root / "operations"
        self.audit_path = workspaces.root / "audit.jsonl"

    @staticmethod
    def validate_operation_id(operation_id: str) -> str:
        try:
            parsed = UUID(operation_id)
        except (ValueError, TypeError) as exc:
            raise MigrationConflictError("operation_id must be a UUID") from exc
        if str(parsed) != operation_id.lower():
            raise MigrationConflictError("operation_id must use canonical UUID form")
        return str(parsed)

    def path(self, workspace_id: str, operation_id: str) -> Path:
        workspace_id = self.workspaces.validate_id(workspace_id)
        operation_id = self.validate_operation_id(operation_id)
        return self.root / workspace_id / f"{operation_id}.json"

    def get(self, workspace_id: str, operation_id: str) -> OperationRecord | None:
        path = self.path(workspace_id, operation_id)
        if not path.is_file():
            return None
        return OperationRecord.model_validate_json(path.read_text(encoding="utf-8"))

    def save(self, record: OperationRecord) -> None:
        path = self.path(record.workspace_id, record.operation_id)
        existing = self.get(record.workspace_id, record.operation_id)
        if existing and (
            existing.action != record.action
            or existing.migration_type != record.migration_type
            or existing.source_revision != record.source_revision
        ):
            raise MigrationConflictError("operation_id was already used for different inputs")
        _atomic_json(path, record.model_dump(mode="json"))

    def append_audit(self, audit: AuditMetadata, *, event: str, approved: bool | None = None) -> None:
        self.audit_path.parent.mkdir(parents=True, exist_ok=True)
        data = {"event": event, **audit.model_dump(mode="json"), "approved": approved}
        with self.audit_path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(data, sort_keys=True) + "\n")

    def status(self, workspace_id: str, operation_id: str) -> dict:
        record = self.get(workspace_id, operation_id)
        if record is None:
            return {"operation_id": operation_id, "status": "not_found"}
        return {
            "operation_id": record.operation_id,
            "action": record.action,
            "status": "completed",
            "created_at": record.created_at.isoformat(),
            "checkpoint_id": record.checkpoint_id,
        }


def new_record(
    *,
    operation_id: str,
    action: str,
    workspace_id: str,
    source_revision: str,
    result: dict,
    migration_type: str | None = None,
    checkpoint_id: str | None = None,
) -> OperationRecord:
    return OperationRecord(
        operation_id=operation_id,
        action=action,
        workspace_id=workspace_id,
        migration_type=migration_type,
        source_revision=source_revision,
        created_at=datetime.now(timezone.utc),
        result=result,
        checkpoint_id=checkpoint_id,
    )
