from pathlib import Path

from code_migration.core.compliance import PIIDetector
from code_migration.core.confidence import MigrationConfidenceAnalyzer
from code_migration.operations import resolve_workspace_path


def test_requirements_do_not_depend_on_cloud_llm_or_telemetry_clients():
    dependency_text = Path("requirements.txt").read_text(encoding="utf-8").lower()

    for package in ("openai", "anthropic", "langsmith", "sentry", "posthog"):
        assert package not in dependency_text


def test_static_analysis_does_not_execute_top_level_python(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    marker = project / "executed.txt"
    (project / "danger.py").write_text(
        f"from pathlib import Path\nPath({str(marker)!r}).write_text('executed')\n",
        encoding="utf-8",
    )

    with MigrationConfidenceAnalyzer(project, allowed_base=tmp_path) as analyzer:
        analyzer.calculate_confidence("python3")

    assert not marker.exists()


def test_operations_reject_symlink_escape(tmp_path, monkeypatch):
    project = tmp_path / "project"
    outside = tmp_path / "outside"
    project.mkdir()
    outside.mkdir()
    secret = outside / "secret.py"
    secret.write_text("print('outside')\n", encoding="utf-8")
    link = project / "escape.py"

    try:
        link.symlink_to(secret)
    except OSError:
        return

    monkeypatch.setattr("code_migration.config.settings.security.allowed_roots", [str(project)])

    try:
        resolve_workspace_path(str(link))
    except Exception as exc:
        assert "outside" in str(exc) or "allowed workspace" in str(exc)
    else:
        raise AssertionError("symlink escape was accepted")


def test_compliance_scan_skips_binary_and_large_files(tmp_path, monkeypatch):
    project = tmp_path / "project"
    project.mkdir()
    (project / "binary.py").write_bytes(b"\x00AKIA1234567890123456")
    large = project / "large.py"
    large.write_text("x = 'user@example.com'\n" * 10_000, encoding="utf-8")
    monkeypatch.setattr("code_migration.config.settings.security.max_file_size_kb", 1)

    with PIIDetector(project) as detector:
        result = detector.scan_directory(file_extensions=[".py"])

    assert result["files_scanned"] == 2
    assert result["total_findings"] == 0
