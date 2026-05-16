from pathlib import Path

from typer.testing import CliRunner

from code_migration.cli import app


runner = CliRunner()


def test_cli_rejects_path_traversal():
    result = runner.invoke(app, ["analyze", "../", "--type", "react-hooks"])

    assert result.exit_code == 1
    assert "Security error" in result.output


def test_cli_dry_run_does_not_modify_fixture():
    fixture = Path("tests/fixtures/sample_project/src/LegacyButton.jsx")
    original = fixture.read_text(encoding="utf-8")

    result = runner.invoke(app, ["run", "tests/fixtures/sample_project", "--type", "react-hooks", "--dry-run"])

    assert result.exit_code == 0
    assert fixture.read_text(encoding="utf-8") == original
    assert "Dry run" in result.output
