# ShiftIQ

## Governed software modernization with LangSmith Fleet

ShiftIQ combines an optional **LangSmith Fleet orchestration layer** with a **local-first deterministic migration engine**.

Fleet provides the agent experience: conversation, specialized sub-agents, skills, GitHub workflows, human approvals, identity, channels, schedules, memory, governance, and LangSmith traces. ShiftIQ provides the migration authority: static analysis, deterministic transforms, dry runs, checkpoints, atomic writes, verification, and rollback.

> **Fleet decides what work should happen. ShiftIQ decides how migrations safely happen.**

ShiftIQ remains fully usable without Fleet, LangSmith, a cloud LLM, or external telemetry.

> [!IMPORTANT]
> ShiftIQ is currently alpha software. Review every generated diff before applying it to production code. The only built-in migration currently registered is `react-hooks`.

## Fleet migration workflow

```text
Developer / Architect / Engineering Manager
                       |
          Fleet Chat / Slack / Teams
                       |
        ShiftIQ Migration Commander
                       |
     +-----------------+-----------------+
     |                 |                 |
   Skills          Sub-agents        Memory
     |                 |                 |
     +-----------------+-----------------+
                       |
             Authenticated Remote MCP
                       |
          Managed ShiftIQ Workspace ID
                       |
        Analyze -> Scan -> Plan -> Dry Run
                       |
          Show diff, impact, and risk
                       |
               Human approval
                       |
             Apply -> Verify -> Report
                       |
             Checkpoint / Rollback
```

The normal flow is:

1. Resolve a GitHub repository and ref.
2. Prepare a quota-bound workspace and pin its commit SHA.
3. Analyze supported migration candidates without executing repository code.
4. Run redacted compliance-oriented pattern checks.
5. Produce a risk and dependency-wave plan.
6. Generate an idempotent dry-run diff.
7. Present the SHA, files, impact, findings, and checkpoint plan.
8. Pause `apply_migration` for Fleet approval.
9. Reject the apply if the workspace changed after review.
10. Create a checkpoint, apply deterministic changes, and verify the result.
11. Preview and approve rollback if recovery is needed.

Repository files, README instructions, comments, issues, commits, and package metadata are treated as untrusted data—not agent authority.

## What is implemented

### In this repository

- Authenticated MCP Streamable HTTP endpoint at `/mcp`.
- Server-owned UUID workspaces instead of remote host paths.
- Workspace TTL, size/count quotas, cleanup, and symlink boundaries.
- Restricted GitHub HTTPS ingestion with validated refs and pinned SHAs.
- Static analysis, risk planning, dependency waves, and redacted scans.
- Dry-run-only `run_migration` plus a separate approved `apply_migration` tool.
- Content-revision binding that invalidates stale reviews.
- Durable UUID idempotency records for destructive operations.
- Checkpoint-before-write, atomic writes, static verification, and rollback.
- Request correlation, timeouts, rate limiting, structured logs, and safe errors.
- Local audit records plus optional service-side LangSmith spans.
- Fleet agent instructions, seven sub-agent briefs, nine skills, schedule prompts, and evaluation scenarios.
- Docker Compose and Kubernetes remote MCP deployment examples.

### Configured in LangSmith Fleet

- Agent creation and publishing.
- Tool `Auto`/`Ask` approval modes.
- Sub-agent tool assignment and skill sharing.
- Fixed or per-user agent identity.
- GitHub, Slack, and Microsoft Teams connections.
- Channels, schedules, memory approval, and central approvals.
- Clone, Run, and Edit sharing permissions.
- Workspace secrets, model selection, and spend controls.
- Enterprise RBAC, ABAC, and integration access policies.
- Account-dependent sandbox and self-hosted/BYOC capabilities.

The [Fleet feature matrix](docs/fleet/feature-matrix.md) is the source of truth for implementation and account-managed status.

## Start with Fleet

### 1. Install ShiftIQ

Requires Python 3.11–3.13.

```powershell
git clone https://github.com/Anudeepsrib/shiftIQ.git
cd shiftIQ
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .
```

For development:

```powershell
python -m pip install -r requirements-dev.txt
```

### 2. Start authenticated remote MCP

```powershell
$env:SHIFTIQ_REMOTE_MCP_ENABLED='true'
$env:SHIFTIQ_MCP_API_KEY='<strong-random-secret>'
$env:SHIFTIQ_WORKSPACE_ROOT='.shiftiq-workspaces'
python -m code_migration.mcp_remote
```

Verify the service:

```powershell
Invoke-RestMethod http://127.0.0.1:8001/healthz
Invoke-RestMethod http://127.0.0.1:8001/readyz
```

Fleet requires a stable, publicly reachable HTTPS endpoint such as:

```text
https://migrations.example.com/mcp
```

Terminate TLS at a trusted ingress, reverse proxy, or load balancer. Do not expose the development HTTP server directly to the internet.

### 3. Configure ShiftIQ Migration Commander

In LangSmith Fleet:

1. Create an agent named **ShiftIQ Migration Commander**.
2. Copy [fleet/AGENTS.md](fleet/AGENTS.md) into its instructions.
3. Add a custom MCP connection using the public `/mcp` URL.
4. Configure `Authorization: Bearer <SHIFTIQ_MCP_API_KEY>` as a protected connection header.
5. Discover the ShiftIQ tools.
6. Set `apply_migration` and `rollback` to **Ask**.
7. Add the briefs from [fleet/subagents](fleet/subagents).
8. Add or share the skills from [fleet/skills](fleet/skills).
9. Configure identity, GitHub, sharing, channels, schedules, and memory policy.
10. Run the scenarios in [fleet/evaluations/scenarios.jsonl](fleet/evaluations/scenarios.jsonl).

See the complete [Fleet agent setup](docs/fleet/agent-setup.md).

### 4. Try a governed migration

```text
Analyze GitHub repository owner/app for a react-hooks migration.
Do not modify files.

Then run the compliance-oriented scan, prepare a migration plan,
and show me a dry-run diff. Pause for approval before apply.
```

Expected progression:

```text
prepare workspace -> analyze -> scan -> plan -> dry run
-> show impact -> approval -> apply -> verify -> report
```

## Remote MCP tools

| Tool | Effect | Fleet mode | Purpose |
|---|---|---:|---|
| `create_workspace` | Workspace write | Auto | Allocate an empty managed workspace |
| `prepare_github_workspace` | Network/workspace write | Auto | Clone a validated GitHub ref and pin SHA |
| `workspace_status` | Read | Auto | Return state, source revision, and quotas |
| `list_workspace_files` | Read | Auto | List relative paths without source contents |
| `cleanup_workspace` | Workspace delete | Configurable | Remove one managed workspace |
| `list_migrators` | Read | Auto | Return authoritative migration types |
| `analyze` | Read | Auto | Find candidates and calculate static risk |
| `compliance_scan` | Read | Auto | Return redacted pattern findings |
| `visualize` | Read | Auto | Return dependency statistics and waves |
| `plan_migration` | Read | Auto | Build the deterministic migration plan |
| `run_migration` | Read | Auto | Generate an idempotent dry run only |
| `apply_migration` | Source write | **Ask** | Apply an unchanged reviewed dry run |
| `verify_migration` | Read | Auto | Verify that the deterministic transform is a no-op |
| `list_checkpoints` | Read | Auto | List rollback checkpoints |
| `get_checkpoint` | Read | Auto | Read safe checkpoint metadata |
| `preview_rollback` | Read | Auto | Bind rollback impact to the current revision |
| `rollback` | Source write | **Ask** | Restore an unchanged reviewed preview |
| `migration_status` | Read | Auto | Read a durable operation result |

Remote authentication accepts either `Authorization: Bearer <key>` or `X-API-Key: <key>`. Secrets must remain in Fleet connection configuration or a runtime secret store—never in prompts, tool arguments, memories, or source control.

## Run ShiftIQ without Fleet

Fleet is optional. The CLI, API, UI, and local stdio MCP continue to use configured local paths beneath `MIGRATION_SECURITY__ALLOWED_ROOTS`.

### CLI

Both `migrate` and `shiftiq` are installed. `migrate` remains the backward-compatible command.

```powershell
migrate analyze tests/fixtures/sample_project --type react-hooks --confidence
migrate visualize tests/fixtures/sample_project
migrate run tests/fixtures/sample_project --type react-hooks --dry-run
migrate generate-tests tests/fixtures/sample_project
migrate compliance scan tests/fixtures/sample_project
migrate rollback <checkpoint-id> --path tests/fixtures/sample_project
```

Applied migrations require `--apply`; dry run is the default.

### Local stdio MCP

```powershell
python -m code_migration.mcp_server
```

Example `mcp.json`:

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

Local MCP exposes path-based analysis, planning, dry-run/apply, verification, checkpoint, compliance-scan, visualization, and rollback operations within configured allowed roots.

### FastAPI

Copy the environment template and set a unique API key:

```powershell
Copy-Item .env.example .env
$env:MIGRATION_API_KEY='<local-api-key>'
uvicorn code_migration.api.app:app --host 127.0.0.1 --port 8000
```

Unauthenticated:

- `GET /healthz`

Authenticated with `X-API-Key`:

- `GET /api/v1/migrators`
- `POST /api/v1/analyze`
- `POST /api/v1/run`
- `POST /api/v1/compliance/scan`
- `POST /api/v1/visualize`
- `POST /api/v1/rollback`

Production mode rejects missing, weak, and demonstration API keys. Production CORS origins must be explicit.

### Web UI

```powershell
Set-Location ui
npm ci
npm run lint
npm run build
npm run dev
```

Set `VITE_API_BASE_URL` when the API is hosted separately. Browser API-key storage is intended for local development convenience, not a production identity system.

## Configuration

Copy [.env.example](.env.example) for the full set of options.

Core settings use the `MIGRATION_` prefix:

```text
MIGRATION_API_KEY
MIGRATION_SERVER__ENVIRONMENT
MIGRATION_SERVER__CORS_ORIGINS
MIGRATION_SECURITY__ALLOWED_ROOTS
MIGRATION_SECURITY__MAX_FILE_SIZE_KB
MIGRATION_SECURITY__MAX_FILES
MIGRATION_OBSERVABILITY__LOG_FORMAT
```

Fleet-facing settings use `SHIFTIQ_` plus optional LangSmith variables:

```text
SHIFTIQ_REMOTE_MCP_ENABLED
SHIFTIQ_REMOTE_MCP_HOST
SHIFTIQ_REMOTE_MCP_PORT
SHIFTIQ_REMOTE_MCP_PATH
SHIFTIQ_REMOTE_MCP_AUTH_ENABLED
SHIFTIQ_MCP_API_KEY
SHIFTIQ_WORKSPACE_ROOT
SHIFTIQ_WORKSPACE_TTL_SECONDS
SHIFTIQ_WORKSPACE_MAX_MB
SHIFTIQ_REMOTE_RATE_LIMIT_PER_MINUTE
SHIFTIQ_GITHUB_TOKEN
SHIFTIQ_LANGSMITH_TRACING
LANGSMITH_API_KEY
LANGSMITH_PROJECT
LANGSMITH_FLEET_AGENT_ID
LANGSMITH_FLEET_API_URL
```

`SHIFTIQ_GITHUB_TOKEN` is optional and is read only from protected runtime configuration. It is never a tool parameter.

## Docker

Run the local API:

```powershell
Copy-Item .env.example .env
docker compose up --build api
```

Run the optional Fleet MCP gateway:

```powershell
$env:SHIFTIQ_MCP_API_KEY='<strong-random-secret>'
docker compose --profile fleet up --build mcp
```

The MCP container runs non-root, drops capabilities, uses a read-only base filesystem, and writes only to its workspace volume and temporary filesystem. Kubernetes deployment scaffolding is available at [deploy/kubernetes/shiftiq-mcp.yaml](deploy/kubernetes/shiftiq-mcp.yaml).

## Safety model

ShiftIQ preserves these controls regardless of what an agent requests:

- Static analysis does not import or execute target repository code.
- Allowed local roots remain enforced.
- Remote callers use server-owned workspace IDs, not absolute paths.
- Symlink escape, path traversal, and unsafe Git protocols are rejected.
- Generated/vendor directories, file-count limits, and file-size limits apply.
- Dry run is the default and remote preview cannot perform writes.
- A checkpoint is created before every applied migration.
- File replacement is atomic.
- Compliance-oriented findings are redacted remotely.
- Repeated destructive requests use durable idempotency records.
- A changed workspace invalidates its previous apply or rollback review.
- Unexpected remote errors do not expose stack traces in responses.
- Agent prompts, skills, memory, or self-updates cannot disable these safeguards.

ShiftIQ provides compliance-oriented scanning, sensitive-data detection, and control-supporting auditability. It does **not** automatically make a system GDPR compliant, HIPAA compliant, SOC 2 compliant, or PCI-DSS certified.

Read the [Fleet threat model](docs/fleet/security.md), [core security model](docs/security-model.md), and [migration safety guide](docs/migration-safety.md).

## Observability and audit

Fleet traces the parent agent, sub-agents, reasoning, approvals, and MCP tool calls in LangSmith. ShiftIQ returns operation, workspace, source SHA/revision, dry-run, checkpoint, and verification metadata inside tool results and records durable local operation/audit events beneath `SHIFTIQ_WORKSPACE_ROOT`.

Optional ShiftIQ-side LangSmith spans are disabled by default. Enable them only after installing and configuring the approved LangSmith client and retention policy.

See [observability.md](docs/fleet/observability.md) and [evaluations.md](docs/fleet/evaluations.md).

## Programmatic Fleet invocation

Set `LANGSMITH_FLEET_API_URL`, `LANGSMITH_FLEET_AGENT_ID`, and `LANGGRAPH_API_KEY` or `LANGSMITH_API_KEY`:

```python
import asyncio

from code_migration.fleet.client import ShiftIQFleetClient

result = asyncio.run(
    ShiftIQFleetClient().analyze_repository(
        "owner/repository",
        "react-hooks",
    )
)
```

The included helper uses a stateless Agent Server run and intentionally exposes no destructive retry helper. See [api-invocation.md](docs/fleet/api-invocation.md).

## Development and verification

```powershell
python -m pip install -r requirements-dev.txt
python -m compileall -q src tests
ruff check .
python -m pytest
python -m build

Set-Location ui
npm ci
npm run lint
npm run build
```

The suite covers local safety plus remote MCP discovery/authentication, workspace boundaries, malicious repository inputs, redaction, dry-run defaults, checkpoint-before-write, idempotency, stale approval, verification, rollback, and disabled-cloud behavior. Normal CI requires no Fleet credentials.

## Project map

```text
fleet/                         Fleet agent, sub-agents, skills, schedules, evals
src/code_migration/fleet/     Optional Fleet integration and workspace services
src/code_migration/mcp_remote.py
                               Authenticated Streamable HTTP MCP server
src/code_migration/mcp_server.py
                               Local stdio MCP server
src/code_migration/operations.py
                               Shared deterministic operations
src/code_migration/core/      Analysis, security, compliance, rollback, verification
tests/fleet/                   Fleet gateway and safety tests
docs/fleet/                    Fleet setup, governance, security, and deployment
deploy/kubernetes/            Remote MCP Kubernetes example
ui/                           React/Vite local interface
```

## Current limitations

- `react-hooks` is the only built-in registered migrator.
- Verification is static; execution of untrusted repository code remains disabled by default.
- Remote OAuth authorization-server support is not implemented; Fleet-managed headers are used.
- Rate limiting and operation records are single-instance. Horizontal deployments need a shared gateway and transactional store.
- Fleet UI configuration, identities, integrations, schedules, RBAC/ABAC, sandboxes, and self-hosting depend on the connected LangSmith account.
- A live GitHub credential is required for private-repository ingestion.
- ShiftIQ does not automatically create, push, or merge GitHub branches and pull requests; Fleet's GitHub integration owns those user-facing operations.

## Documentation

- [Fleet integration overview](docs/fleet/README.md)
- [Fleet architecture](docs/fleet/architecture.md)
- [Fleet quickstart](docs/fleet/quickstart.md)
- [Remote MCP](docs/fleet/remote-mcp.md)
- [Agent setup](docs/fleet/agent-setup.md)
- [Approvals](docs/fleet/approvals.md)
- [Memory policy](docs/fleet/memory.md)
- [Identity](docs/fleet/identity.md)
- [GitHub workflow](docs/fleet/github.md)
- [Channels and schedules](docs/fleet/channels.md)
- [RBAC and ABAC](docs/fleet/rbac-abac.md)
- [Deployment](docs/fleet/deployment.md)
- [Troubleshooting](docs/fleet/troubleshooting.md)
- [Feature matrix](docs/fleet/feature-matrix.md)
- [Core MCP usage](docs/mcp-usage.md)
- [Compliance scanner](docs/compliance-scanner.md)
- [Audit report](AUDIT_REPORT.md)

## License

Apache-2.0. See [LICENSE](LICENSE).
