import asyncio
import json
from pathlib import Path

from code_migration.mcp_server import mcp


def _call_tool(name: str, arguments: dict):
    content, structured = asyncio.run(mcp.call_tool(name, arguments))
    if structured and "result" in structured:
        return json.loads(structured["result"])
    return json.loads(content[0].text)


def test_mcp_tool_registration():
    tools = asyncio.run(mcp.list_tools())
    tool_names = {tool.name for tool in tools}

    assert {"analyze", "run_migration", "compliance_scan", "visualize", "rollback"}.issubset(tool_names)


def test_mcp_rejects_invalid_path():
    result = _call_tool("run_migration", {"path": "../", "migration_type": "react-hooks"})

    assert "error" in result or result.get("total_candidates") == 0


def test_mcp_run_migration_defaults_to_dry_run():
    fixture = Path("tests/fixtures/sample_project/src/LegacyButton.jsx")
    original = fixture.read_text(encoding="utf-8")

    result = _call_tool("run_migration", {"path": "tests/fixtures/sample_project", "migration_type": "react-hooks"})

    assert result["dry_run"] is True
    assert result["results"][0]["applied"] is False
    assert fixture.read_text(encoding="utf-8") == original


def test_mcp_compliance_scan_redacts_sensitive_values(tmp_path, monkeypatch):
    project = tmp_path / "project"
    project.mkdir()
    (project / "config.py").write_text('API_KEY = "sk_test_1234567890abcdef"\n', encoding="utf-8")
    monkeypatch.setattr(
        "code_migration.config.settings.security.allowed_roots",
        [str(tmp_path)],
    )

    result = _call_tool("compliance_scan", {"path": str(project)})

    assert result["total_findings"] >= 1
    assert "sk_test_1234567890abcdef" not in json.dumps(result)
