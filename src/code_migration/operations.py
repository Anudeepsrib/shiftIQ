"""Shared local-first operations for API, CLI, and MCP entry points."""

from __future__ import annotations

import difflib
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from code_migration.config import settings
from code_migration.core.rollback import TimeMachineRollback
from code_migration.core.security.input_validator import SecurityError
from code_migration.core.visualizer import VisualMigrationPlanner
from code_migration.registry import create_registry
from code_migration.utils.file_handler import safe_read_file, safe_write_file


SKIP_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "dist",
    "build",
    "htmlcov",
    ".migration-backups",
    ".migration-checkpoints",
    ".migration-logs",
}


def _is_relative_to(path: Path, base: Path) -> bool:
    try:
        path.relative_to(base)
        return True
    except ValueError:
        return False


def resolve_workspace_path(
    path: str,
    *,
    must_exist: bool = True,
    trusted_root: Optional[Path] = None,
) -> Path:
    """Resolve a user path under one of the configured allowed roots."""
    if not path or len(path) > 4096:
        raise SecurityError("Invalid path length")

    raw = Path(path).expanduser()
    roots = settings.resolved_allowed_roots()
    if trusted_root is not None:
        roots.append(trusted_root.resolve())

    for root in roots:
        candidate = raw if raw.is_absolute() else root / raw
        try:
            resolved = candidate.resolve(strict=must_exist)
        except (OSError, RuntimeError):
            continue
        if _is_relative_to(resolved, root):
            if must_exist and not resolved.exists():
                raise SecurityError(f"Path does not exist: {path}")
            return resolved

    raise SecurityError("Path is outside configured allowed workspace roots")


def project_root_for(target: Path) -> Path:
    return target if target.is_dir() else target.parent


def iter_candidate_files(target: Path, extensions: Optional[Iterable[str]] = None) -> List[Path]:
    """Collect regular, in-workspace files while skipping generated/vendor trees."""
    suffixes = {ext.lower() for ext in extensions} if extensions else None
    max_bytes = settings.security.max_file_size_kb * 1024
    files: List[Path] = []

    candidates = [target] if target.is_file() else target.rglob("*")
    for item in candidates:
        if len(files) >= settings.security.max_files:
            break
        if any(part in SKIP_DIRS for part in item.parts):
            continue
        if item.is_symlink() or not item.is_file():
            continue
        if suffixes and item.suffix.lower() not in suffixes:
            continue
        try:
            if item.stat().st_size > max_bytes:
                continue
        except OSError:
            continue
        files.append(item)

    return files


def _relative(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return path.name


def analyze_project(
    path: str,
    migration_type: str = "react-hooks",
    *,
    include_confidence: bool = False,
    trusted_root: Optional[Path] = None,
) -> Dict[str, Any]:
    target = resolve_workspace_path(path, trusted_root=trusted_root)
    root = project_root_for(target)
    registry = create_registry()
    migrator = registry.get(migration_type)
    if migrator is None:
        raise ValueError(f"Unknown migration type: {migration_type}")

    candidates = [
        file_path
        for file_path in iter_candidate_files(target, migrator.supported_extensions)
        if migrator.can_migrate(file_path)
    ]
    result: Dict[str, Any] = {
        "migration_type": migration_type,
        "target": _relative(target, root),
        "total_candidates": len(candidates),
        "candidates": [_relative(file_path, root) for file_path in candidates],
    }

    if include_confidence:
        from code_migration.core.confidence import MigrationConfidenceAnalyzer

        with MigrationConfidenceAnalyzer(root, allowed_base=root) as analyzer:
            score = analyzer.calculate_confidence(migration_type=migration_type)
        result["confidence"] = {
            "overall_score": score.overall_score,
            "risk_level": score.risk_level,
            "estimated_hours": score.estimated_hours,
            "estimated_cost": score.estimated_cost,
            "migration_complexity": score.migration_complexity,
            "warnings": score.warnings,
            "blockers": score.blockers,
            "recommendations": score.recommendations,
        }

    return result


def run_migration(
    path: str,
    migration_type: str = "react-hooks",
    *,
    dry_run: bool = True,
    trusted_root: Optional[Path] = None,
) -> Dict[str, Any]:
    target = resolve_workspace_path(path, trusted_root=trusted_root)
    root = project_root_for(target)
    registry = create_registry()
    migrator = registry.get(migration_type)
    if migrator is None:
        raise ValueError(f"Unknown migration type: {migration_type}")

    candidates = [
        file_path
        for file_path in iter_candidate_files(target, migrator.supported_extensions)
        if migrator.can_migrate(file_path)
    ]

    checkpoint_id = None
    changed_files = 0
    results = []
    if candidates and not dry_run:
        with TimeMachineRollback(root, allowed_base=root) as rollback:
            checkpoint_id = rollback.create_checkpoint(f"Pre-migration checkpoint for {migration_type}")

    for file_path in candidates:
        rel_path = _relative(file_path, root)
        try:
            content = safe_read_file(str(file_path), str(root))
            new_content = migrator.migrate(content, file_path)
            changed = content != new_content
            diff = ""
            if changed:
                changed_files += 1
                diff = "\n".join(
                    difflib.unified_diff(
                        content.splitlines(),
                        new_content.splitlines(),
                        fromfile=rel_path,
                        tofile=rel_path,
                        lineterm="",
                    )
                )
                if not dry_run:
                    safe_write_file(str(file_path), new_content, str(root))
            results.append(
                {
                    "file": rel_path,
                    "changed": changed,
                    "applied": changed and not dry_run,
                    "diff": diff[:20_000],
                }
            )
        except Exception as exc:
            results.append({"file": rel_path, "changed": False, "applied": False, "error": str(exc)})

    return {
        "migration_type": migration_type,
        "dry_run": dry_run,
        "checkpoint_id": checkpoint_id,
        "total_candidates": len(candidates),
        "changed_files": changed_files,
        "results": results,
    }


def compliance_scan(
    path: str,
    *,
    include_raw: bool = False,
    trusted_root: Optional[Path] = None,
) -> Dict[str, Any]:
    from code_migration.core.compliance import PIIDetector

    target = resolve_workspace_path(path, trusted_root=trusted_root)
    root = project_root_for(target)
    with PIIDetector(root, expose_raw=include_raw) as detector:
        return detector.scan_directory()


def visualize_project(path: str, *, trusted_root: Optional[Path] = None) -> Dict[str, Any]:
    target = resolve_workspace_path(path, trusted_root=trusted_root)
    root = project_root_for(target)
    planner = VisualMigrationPlanner(root, allowed_base=root)
    planner.build_dependency_graph()
    waves = planner.calculate_migration_waves()
    return {
        "total_nodes": planner.graph.number_of_nodes(),
        "total_edges": planner.graph.number_of_edges(),
        "migration_waves": waves,
        "statistics": planner.get_graph_statistics(),
    }


def rollback_checkpoint(
    path: str,
    checkpoint_id: str,
    *,
    dry_run: bool = False,
    trusted_root: Optional[Path] = None,
) -> Dict[str, Any]:
    target = resolve_workspace_path(path, trusted_root=trusted_root)
    root = project_root_for(target)
    with TimeMachineRollback(root, allowed_base=root) as rollback:
        return rollback.rollback(checkpoint_id, dry_run=dry_run)


def list_checkpoints(path: str, *, trusted_root: Optional[Path] = None) -> List[Dict[str, Any]]:
    target = resolve_workspace_path(path, trusted_root=trusted_root)
    root = project_root_for(target)
    with TimeMachineRollback(root, allowed_base=root) as rollback:
        return rollback.list_checkpoints()


def get_checkpoint(
    path: str,
    checkpoint_id: str,
    *,
    trusted_root: Optional[Path] = None,
) -> Optional[Dict[str, Any]]:
    target = resolve_workspace_path(path, trusted_root=trusted_root)
    root = project_root_for(target)
    with TimeMachineRollback(root, allowed_base=root) as rollback:
        return rollback.get_checkpoint_details(checkpoint_id)


def plan_migration(
    path: str,
    migration_type: str = "react-hooks",
    *,
    trusted_root: Optional[Path] = None,
) -> Dict[str, Any]:
    """Build a deterministic candidate and dependency-wave plan."""
    analysis = analyze_project(path, migration_type, include_confidence=True, trusted_root=trusted_root)
    graph = visualize_project(path, trusted_root=trusted_root)
    return {
        "migration_type": migration_type,
        "total_candidates": analysis["total_candidates"],
        "candidates": analysis["candidates"],
        "confidence": analysis.get("confidence"),
        "migration_waves": graph["migration_waves"],
        "graph": {
            "total_nodes": graph["total_nodes"],
            "total_edges": graph["total_edges"],
        },
    }


def verify_migration(
    path: str,
    migration_type: str = "react-hooks",
    *,
    trusted_root: Optional[Path] = None,
) -> Dict[str, Any]:
    """Statically verify that rerunning the deterministic transform is a no-op."""
    preview = run_migration(path, migration_type, dry_run=True, trusted_root=trusted_root)
    remaining = [item["file"] for item in preview["results"] if item.get("changed")]
    return {
        "migration_type": migration_type,
        "verification": "passed" if not remaining else "failed",
        "remaining_candidates": remaining,
        "remaining_count": len(remaining),
        "execution_performed": False,
    }
