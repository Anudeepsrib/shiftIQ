from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from code_migration.api.deps import get_registry
from code_migration.api.schemas import (
    AnalyzeRequest,
    ComplianceScanRequest,
    MigrateRequest,
    PluginInfoSchema,
    RollbackRequest,
)
from code_migration.core.security.input_validator import SecurityError
from code_migration.operations import (
    analyze_project,
    compliance_scan,
    rollback_checkpoint,
    run_migration,
    visualize_project,
)
from code_migration.registry import MigratorRegistry

router = APIRouter()


def _api_failure(exc: Exception) -> HTTPException:
    if isinstance(exc, SecurityError):
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    if isinstance(exc, ValueError):
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Operation failed")


@router.get("/migrators", response_model=List[PluginInfoSchema])
async def list_migrators(registry: MigratorRegistry = Depends(get_registry)):
    """List available migration plugins."""
    return registry.list_all()


@router.post("/analyze")
async def analyze(request: AnalyzeRequest):
    """Analyze candidate files without modifying or executing target code."""
    try:
        return analyze_project(
            request.path,
            migration_type=request.migration_type,
            include_confidence=request.include_confidence,
        )
    except Exception as exc:
        raise _api_failure(exc) from exc


@router.post("/run")
async def migrate(request: MigrateRequest):
    """Preview or apply a migration. Dry-run defaults to true."""
    try:
        return run_migration(
            request.path,
            migration_type=request.migration_type,
            dry_run=request.dry_run,
        )
    except Exception as exc:
        raise _api_failure(exc) from exc


@router.post("/compliance/scan")
async def scan_compliance(request: ComplianceScanRequest):
    """Run PII/PHI/PCI pattern scanning with redacted findings by default."""
    try:
        return compliance_scan(request.path, include_raw=request.include_raw)
    except Exception as exc:
        raise _api_failure(exc) from exc


@router.post("/visualize")
async def visualize(request: AnalyzeRequest):
    """Return dependency graph statistics and migration waves."""
    try:
        return visualize_project(request.path)
    except Exception as exc:
        raise _api_failure(exc) from exc


@router.post("/rollback")
async def rollback(request: RollbackRequest):
    """Restore a checkpoint or preview the rollback."""
    try:
        return rollback_checkpoint(
            request.path,
            request.checkpoint_id,
            dry_run=request.dry_run,
        )
    except Exception as exc:
        raise _api_failure(exc) from exc
