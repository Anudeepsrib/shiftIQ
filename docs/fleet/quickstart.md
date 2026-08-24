# Quickstart

Local behavior remains unchanged:

```powershell
pip install -e .
migrate analyze tests/fixtures/sample_project --type react-hooks --confidence
migrate run tests/fixtures/sample_project --type react-hooks --dry-run
python -m code_migration.mcp_server
```

Start remote MCP for local validation:

```powershell
$env:SHIFTIQ_REMOTE_MCP_ENABLED='true'
$env:SHIFTIQ_MCP_API_KEY='<random-secret>'
$env:SHIFTIQ_WORKSPACE_ROOT='.shiftiq-workspaces'
python -m code_migration.mcp_remote
```

Check `http://127.0.0.1:8001/healthz` and `http://127.0.0.1:8001/readyz`. Fleet requires a publicly reachable HTTPS URL such as `https://migrations.example.com/mcp`; terminate TLS at a trusted ingress or load balancer.

For Docker: set `SHIFTIQ_MCP_API_KEY`, then run `docker compose --profile fleet up --build mcp`.
