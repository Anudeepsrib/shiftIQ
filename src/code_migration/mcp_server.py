"""MCP server for ShiftIQ local code migration workflows."""

from __future__ import annotations

import json
from typing import Optional

from mcp.server.fastmcp import FastMCP

from code_migration.operations import (
    analyze_project,
    compliance_scan as run_compliance_scan,
    get_checkpoint as get_checkpoint_operation,
    list_checkpoints as list_checkpoints_operation,
    plan_migration as plan_migration_operation,
    rollback_checkpoint,
    run_migration as run_migration_operation,
    verify_migration as verify_migration_operation,
    visualize_project,
)
from code_migration.registry import create_registry


mcp = FastMCP(
    "ShiftIQ",
    instructions=(
        "Local-first code migration tools. Analysis is designed to use static "
        "parsing and filesystem safeguards; migration tools default to dry-run."
    ),
)


def _json(data: object) -> str:
    return json.dumps(data, indent=2, default=str)


def _safe_json(func, *args, **kwargs) -> str:
    try:
        return _json(func(*args, **kwargs))
    except Exception as exc:
        return _json({"error": str(exc)})


@mcp.tool()
def analyze(path: str, migration_type: str = "react-hooks", include_confidence: bool = False) -> str:
    """Analyze candidate files under an allowed workspace root.

    Args:
        path: File or project directory under a configured allowed root.
        migration_type: Migration type identifier, such as react-hooks.
        include_confidence: Include static confidence scoring.
    """
    return _safe_json(analyze_project, path, migration_type=migration_type, include_confidence=include_confidence)


@mcp.tool()
def list_migrators() -> str:
    """List registered migration plugins and supported file extensions."""
    registry = create_registry()
    return _json(
        [
            {
                "name": info.name,
                "description": info.description,
                "version": info.version,
                "supported_extensions": info.supported_extensions,
                "tags": info.tags,
                "source": info.source,
            }
            for info in registry.list_all()
        ]
    )


@mcp.tool()
def run_migration(path: str, migration_type: str = "react-hooks", dry_run: bool = True) -> str:
    """Preview or apply a migration. Dry-run defaults to true.

    Args:
        path: File or project directory under a configured allowed root.
        migration_type: Migration type identifier, such as react-hooks.
        dry_run: Preview changes without writing files when true.
    """
    return _safe_json(run_migration_operation, path, migration_type=migration_type, dry_run=dry_run)


@mcp.tool()
def compliance_scan(path: str, include_raw: bool = False) -> str:
    """Run PII/PHI/PCI pattern scanning with redacted findings by default.

    Args:
        path: Project directory under a configured allowed root.
        include_raw: Include raw sensitive values only when explicitly enabled.
    """
    return _safe_json(run_compliance_scan, path, include_raw=include_raw)


@mcp.tool()
def visualize(path: str) -> str:
    """Return dependency graph statistics and migration waves."""
    return _safe_json(visualize_project, path)


@mcp.tool()
def plan_migration(path: str, migration_type: str = "react-hooks") -> str:
    """Build a static candidate, risk, and dependency-wave plan."""
    return _safe_json(plan_migration_operation, path, migration_type=migration_type)


@mcp.tool()
def verify_migration(path: str, migration_type: str = "react-hooks") -> str:
    """Statically verify whether supported source-pattern candidates remain."""
    return _safe_json(verify_migration_operation, path, migration_type=migration_type)


@mcp.tool()
def list_checkpoints(path: str) -> str:
    """List rollback checkpoints for a local project path."""
    return _safe_json(list_checkpoints_operation, path)


@mcp.tool()
def get_checkpoint(path: str, checkpoint_id: str) -> str:
    """Return local rollback checkpoint metadata."""
    return _safe_json(get_checkpoint_operation, path, checkpoint_id)


@mcp.tool()
def rollback(path: str, checkpoint_id: Optional[str] = None, dry_run: bool = False) -> str:
    """Restore a checkpoint. Creating checkpoints is handled by applied migrations.

    Args:
        path: Project directory under a configured allowed root.
        checkpoint_id: Existing checkpoint ID to restore.
        dry_run: Preview rollback without changing files.
    """
    if not checkpoint_id:
        return _json({"error": "checkpoint_id is required for rollback"})
    return _safe_json(rollback_checkpoint, path, checkpoint_id, dry_run=dry_run)


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
