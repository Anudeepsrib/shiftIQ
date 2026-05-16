from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from code_migration.core.security.input_validator import SecurityError
from code_migration.core.test_generation import TestGenerator
from code_migration.operations import (
    analyze_project,
    compliance_scan,
    iter_candidate_files,
    resolve_workspace_path,
    rollback_checkpoint,
    run_migration,
    visualize_project,
)
from code_migration.registry import create_registry


app = typer.Typer(help="ShiftIQ local-first code migration assistant.")
compliance_app = typer.Typer(help="Compliance-oriented pattern scanner commands.")
app.add_typer(compliance_app, name="compliance")
console = Console()


def _exit_on_error(exc: Exception) -> None:
    if isinstance(exc, SecurityError):
        console.print(f"[bold red]Security error:[/bold red] {exc}")
    else:
        console.print(f"[bold red]Error:[/bold red] {exc}")
    raise typer.Exit(code=1) from exc


@app.command()
def migrators() -> None:
    """List installed migration plugins."""
    registry = create_registry()
    table = Table(title="Available Migrators")
    table.add_column("Name")
    table.add_column("Extensions")
    table.add_column("Source")
    table.add_column("Description")
    for info in registry.list_all():
        table.add_row(info.name, ", ".join(info.supported_extensions), info.source, info.description)
    console.print(table)


@app.command()
def analyze(
    path: str = typer.Argument(..., help="File or directory under an allowed workspace root."),
    type: str = typer.Option("react-hooks", "--type", help="Migration type."),
    confidence: bool = typer.Option(False, "--confidence", help="Include static confidence scoring."),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON output."),
) -> None:
    """Analyze a project without modifying files or executing target code."""
    try:
        result = analyze_project(path, migration_type=type, include_confidence=confidence)
    except Exception as exc:
        _exit_on_error(exc)

    if json_output:
        console.print_json(json.dumps(result, default=str))
        return

    console.print(Panel(f"{result['total_candidates']} candidate files found", title="ShiftIQ Analysis"))
    for candidate in result["candidates"]:
        console.print(f"  - {candidate}")
    if confidence and "confidence" in result:
        conf = result["confidence"]
        console.print(
            f"\nConfidence: [bold]{conf['overall_score']}/100[/bold] "
            f"({conf['risk_level']} risk, {conf['migration_complexity']})"
        )


@app.command()
def run(
    path: str = typer.Argument(..., help="File or directory under an allowed workspace root."),
    type: str = typer.Option("react-hooks", "--type", help="Migration type."),
    dry_run: bool = typer.Option(True, "--dry-run/--apply", help="Preview by default; use --apply to write changes."),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON output."),
) -> None:
    """Preview or apply a migration. A checkpoint is created before writes."""
    try:
        result = run_migration(path, migration_type=type, dry_run=dry_run)
    except Exception as exc:
        _exit_on_error(exc)

    if json_output:
        console.print_json(json.dumps(result, default=str))
        return

    mode = "Dry run" if result["dry_run"] else "Applied"
    console.print(Panel(f"{mode}: {result['changed_files']} changed files", title="ShiftIQ Migration"))
    if result.get("checkpoint_id"):
        console.print(f"Checkpoint: {result['checkpoint_id']}")
    for item in result["results"]:
        marker = "changed" if item.get("changed") else "unchanged"
        if item.get("error"):
            marker = f"error: {item['error']}"
        console.print(f"  - {item['file']}: {marker}")


@app.command()
def visualize(
    path: str = typer.Argument(..., help="Project directory under an allowed workspace root."),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON output."),
) -> None:
    """Generate dependency graph statistics and migration waves."""
    try:
        result = visualize_project(path)
    except Exception as exc:
        _exit_on_error(exc)

    if json_output:
        console.print_json(json.dumps(result, default=str))
        return

    console.print(Panel(f"{result['total_nodes']} nodes, {result['total_edges']} edges", title="ShiftIQ Graph"))
    for index, wave in enumerate(result["migration_waves"], start=1):
        console.print(f"Wave {index}: {', '.join(wave) if wave else '(empty)'}")


@app.command("generate-tests")
def generate_tests(
    path: str = typer.Argument(..., help="Project directory under an allowed workspace root."),
    type: str = typer.Option("react-hooks", "--type", help="Migration type."),
    output: Optional[Path] = typer.Option(None, "--output", help="Directory for generated tests."),
) -> None:
    """Generate reviewable test skeletons from static source parsing."""
    try:
        target = resolve_workspace_path(path)
        registry = create_registry()
        migrator = registry.get(type)
        if migrator is None:
            raise ValueError(f"Unknown migration type: {type}")
        files = [
            file_path
            for file_path in iter_candidate_files(target, migrator.supported_extensions)
            if migrator.can_migrate(file_path)
        ]
        generator = TestGenerator(target if target.is_dir() else target.parent)
        tests_by_file = generator.generate_migration_tests(type, files)
        output_dir = output or ((target if target.is_dir() else target.parent) / "generated-tests")
        created = generator.export_tests(output_dir)
    except Exception as exc:
        _exit_on_error(exc)

    console.print(Panel(f"Generated {sum(len(v) for v in tests_by_file.values())} test skeletons", title="ShiftIQ Tests"))
    for path_created in created:
        console.print(f"  - {path_created}")


@compliance_app.command("scan")
def compliance_scan_command(
    path: str = typer.Argument(..., help="Project directory under an allowed workspace root."),
    include_raw: bool = typer.Option(False, "--include-raw", help="Include raw matched values if configured."),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON output."),
) -> None:
    """Scan for PII/PHI/PCI-like patterns. Findings are redacted by default."""
    try:
        result = compliance_scan(path, include_raw=include_raw)
    except Exception as exc:
        _exit_on_error(exc)

    if json_output:
        console.print_json(json.dumps(result, default=str))
        return

    console.print(
        Panel(
            f"{result['total_findings']} findings across {result['files_with_pii']} files",
            title="ShiftIQ Pattern Scan",
        )
    )
    for finding in result["findings"][:25]:
        console.print(
            f"  - {finding['file_path']}:{finding['line']} "
            f"{finding['type']} {finding['severity']} {finding['match']}"
        )


@app.command()
def rollback(
    checkpoint: str = typer.Argument(..., help="Checkpoint ID to restore."),
    path: str = typer.Option(".", "--path", help="Project path under an allowed workspace root."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview rollback without changing files."),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON output."),
) -> None:
    """Restore a checkpoint created before an applied migration."""
    try:
        result = rollback_checkpoint(path, checkpoint, dry_run=dry_run)
    except Exception as exc:
        _exit_on_error(exc)

    if json_output:
        console.print_json(json.dumps(result, default=str))
        return
    console.print(Panel(f"Restored {result.get('files_restored', 0)} files", title="ShiftIQ Rollback"))


def main() -> None:
    app()


if __name__ == "__main__":
    main()
