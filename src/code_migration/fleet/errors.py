"""Safe, machine-readable errors for Fleet and remote MCP callers."""

from __future__ import annotations

from typing import Any


class FleetError(Exception):
    code = "fleet_error"

    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def as_dict(self) -> dict[str, Any]:
        return {"code": self.code, "message": self.message, "details": self.details}


class AuthenticationError(FleetError):
    code = "authentication_error"


class AuthorizationError(FleetError):
    code = "authorization_error"


class WorkspaceNotFoundError(FleetError):
    code = "workspace_not_found"


class WorkspaceBoundaryError(FleetError):
    code = "workspace_boundary_error"


class WorkspaceQuotaError(FleetError):
    code = "workspace_quota_error"


class UnsupportedMigrationError(FleetError):
    code = "unsupported_migration"


class MigrationConflictError(FleetError):
    code = "migration_conflict"


class SourceRevisionChangedError(FleetError):
    code = "source_revision_changed"


class ApprovalRequiredError(FleetError):
    code = "approval_required"


class CheckpointNotFoundError(FleetError):
    code = "checkpoint_not_found"


class VerificationFailedError(FleetError):
    code = "verification_failed"


class ComplianceBlockError(FleetError):
    code = "compliance_block"


class RateLimitError(FleetError):
    code = "rate_limit"


class RemoteMCPError(FleetError):
    code = "remote_mcp_error"


class FleetConfigurationError(FleetError):
    code = "fleet_configuration_error"
