"""Typed contracts crossing the Fleet/ShiftIQ boundary."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


RiskLevel = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL", "UNKNOWN"]


class WorkspaceMetadata(BaseModel):
    workspace_id: str
    status: Literal["empty", "preparing", "ready", "failed", "expired"] = "empty"
    created_at: datetime
    expires_at: datetime
    source_repository: Optional[str] = None
    source_ref: Optional[str] = None
    source_sha: Optional[str] = None
    file_count: int = 0
    size_bytes: int = 0


class AuditMetadata(BaseModel):
    operation_id: str
    workspace_id: str
    timestamp: datetime
    tool_name: str
    migration_type: Optional[str] = None
    source_sha: Optional[str] = None
    source_revision: Optional[str] = None
    dry_run: Optional[bool] = None
    risk_level: RiskLevel = "UNKNOWN"
    checkpoint_id: Optional[str] = None
    fleet_trace_id: Optional[str] = None
    actor: Optional[str] = None
    agent_name: str = "ShiftIQ Migration Commander"


class ToolResult(BaseModel):
    ok: bool = True
    data: dict[str, Any] | list[Any] | None = None
    audit: Optional[AuditMetadata] = None
    error: Optional[dict[str, Any]] = None


class OperationRecord(BaseModel):
    operation_id: str
    action: str
    workspace_id: str
    migration_type: Optional[str] = None
    source_revision: str
    created_at: datetime
    result: dict[str, Any]
    checkpoint_id: Optional[str] = None


class MigrationCard(BaseModel):
    repository: Optional[str] = None
    migration: str
    source_version: Optional[str] = None
    target_version: Optional[str] = None
    commit_sha: Optional[str] = None
    readiness: str
    risk: RiskLevel = "UNKNOWN"
    confidence: Optional[float] = None
    files: list[str] = Field(default_factory=list)
    candidates: int = 0
    compliance_findings: int = 0
    dry_run_operation_id: Optional[str] = None
    approval: str = "not_requested"
    checkpoint_id: Optional[str] = None
    verification: Optional[str] = None
    recommended_next_action: str
