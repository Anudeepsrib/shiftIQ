# MCP Usage

ShiftIQ exposes local MCP tools over stdio:

- `analyze`
- `run_migration`
- `compliance_scan`
- `visualize`
- `rollback`
- `plan_migration`
- `verify_migration`
- `list_checkpoints`
- `get_checkpoint`

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

For LangSmith Fleet and other remote clients, `python -m code_migration.mcp_remote` exposes authenticated Streamable HTTP at `/mcp`. Remote schemas accept only managed `workspace_id` values, separate dry run from apply, bind destructive operations to reviewed revisions, and always redact compliance matches. See [Fleet remote MCP](../fleet/remote-mcp.md).
