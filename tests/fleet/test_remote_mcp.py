import asyncio

from fastapi.testclient import TestClient

from code_migration.fleet.config import FleetSettings
from code_migration.fleet.service import FleetMigrationService
from code_migration.fleet.workspace import WorkspaceManager
from code_migration.mcp_remote import create_remote_app, create_remote_mcp


def _components(tmp_path):
    config = FleetSettings(
        _env_file=None,
        workspace_root=tmp_path / "fleet",
        remote_mcp_auth_enabled=True,
        mcp_api_key="a-strong-test-key",
    )
    workspaces = WorkspaceManager(config)
    return config, FleetMigrationService(config, workspaces)


def test_remote_tool_discovery_uses_workspace_ids_not_paths(tmp_path):
    config, service = _components(tmp_path)
    server = create_remote_mcp(config, service)
    tools = asyncio.run(server.list_tools())
    by_name = {tool.name: tool for tool in tools}

    assert {
        "analyze",
        "run_migration",
        "apply_migration",
        "compliance_scan",
        "plan_migration",
        "verify_migration",
        "rollback",
        "prepare_github_workspace",
    }.issubset(by_name)
    assert "workspace_id" in by_name["analyze"].inputSchema["properties"]
    assert "path" not in by_name["analyze"].inputSchema["properties"]


def test_remote_auth_protects_mcp_but_not_health(tmp_path):
    config, service = _components(tmp_path)
    app = create_remote_app(config, service)

    with TestClient(app) as client:
        assert client.get("/healthz").status_code == 200
        assert client.get("/readyz").status_code == 200
        assert client.get("/mcp").status_code == 401
        assert client.get("/mcp", headers={"Authorization": "Bearer wrong"}).status_code == 401
        assert client.get("/mcp", headers={"X-API-Key": "a-strong-test-key"}).status_code != 401


def test_remote_server_is_not_ready_when_auth_secret_is_missing(tmp_path):
    config = FleetSettings(
        _env_file=None,
        workspace_root=tmp_path / "fleet",
        remote_mcp_auth_enabled=True,
        mcp_api_key=None,
    )
    app = create_remote_app(config, FleetMigrationService(config, WorkspaceManager(config)))

    with TestClient(app) as client:
        assert client.get("/readyz").status_code == 503
        assert client.get("/mcp").status_code == 503
