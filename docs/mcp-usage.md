# MCP Usage

ShiftIQ exposes MCP tools over stdio:

- `analyze`
- `run_migration`
- `compliance_scan`
- `visualize`
- `rollback`

Run locally:

```bash
python -m code_migration.mcp_server
```

MCP client config:

```json
{
  "mcpServers": {
    "shiftiq": {
      "command": "python",
      "args": ["-m", "code_migration.mcp_server"],
      "cwd": "."
    }
  }
}
```

`run_migration` defaults to `dry_run=true`. All path arguments must resolve under `MIGRATION_SECURITY__ALLOWED_ROOTS`.
