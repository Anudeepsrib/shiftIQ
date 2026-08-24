# Remote MCP

ShiftIQ uses MCP Streamable HTTP at `/mcp`, stateless JSON responses, and the same deterministic operations used by local interfaces. `GET /healthz` is liveness; `GET /readyz` verifies authentication configuration.

Authentication accepts either `Authorization: Bearer <SHIFTIQ_MCP_API_KEY>` or `X-API-Key`. Store this value in Fleet's MCP connection headers; never include it in instructions, tools, memories, or chat. OAuth 2.1 is a later extension point—this deployment implements workspace-managed headers because it has no user authorization server.

| Tool | Mode | Approval | Purpose |
|---|---|---:|---|
| `create_workspace` | Write workspace | Auto | Allocate an empty managed workspace |
| `prepare_github_workspace` | Network/write workspace | Auto | Clone a validated GitHub ref and pin SHA |
| `workspace_status` | Read | Auto | Return state and quotas |
| `list_workspace_files` | Read | Auto | Return relative paths only |
| `cleanup_workspace` | Delete workspace | Auto/configurable | Delete one managed workspace |
| `list_migrators` | Read | Auto | Authoritative migration types |
| `analyze` | Read | Auto | Static candidate/risk analysis |
| `compliance_scan` | Read | Auto | Redacted pattern findings |
| `visualize` | Read | Auto | Dependency waves/statistics |
| `plan_migration` | Read | Auto | Candidate/risk/wave plan |
| `run_migration` | Read | Auto | Dry run only; rejects remote apply |
| `apply_migration` | Source write | **Ask** | Apply unchanged reviewed dry run |
| `verify_migration` | Read | Auto | Static no-op verification |
| `list_checkpoints` / `get_checkpoint` | Read | Auto | Checkpoint metadata |
| `preview_rollback` | Read | Auto | Bind rollback impact to revision |
| `rollback` | Source write | **Ask** | Restore unchanged reviewed preview |
| `migration_status` | Read | Auto | Durable operation status |

Request IDs are returned as `X-Request-ID`. Optional `X-Fleet-Trace-ID` and `X-Fleet-Actor` headers are recorded when a caller supplies them; secrets are not logged.
