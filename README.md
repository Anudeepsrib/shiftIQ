# ShiftIQ

ShiftIQ is a local-first code migration assistant for static analysis, dry-run migrations, MCP tool use, rollback checkpoints, and PII/PHI/PCI-oriented pattern scanning.

It is a development tool. Review all generated migrations before applying them to production code.

## What It Does

- Finds migration candidates without importing or executing target project code.
- Provides a FastAPI backend with API-key protected migration endpoints.
- Exposes MCP tools for `analyze`, `run_migration`, `compliance_scan`, `visualize`, and `rollback`.
- Runs migrations in dry-run mode by default.
- Creates rollback checkpoints before applied migrations.
- Scans for sensitive-data patterns with redacted findings by default.

ShiftIQ includes compliance-oriented checks, not formal GDPR, HIPAA, SOC2, or PCI-DSS compliance certification.

## Install

```bash
git clone https://github.com/Anudeepsrib/shiftIQ.git
cd shiftIQ
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
```

For development tools:

```bash
pip install -r requirements-dev.txt
```

## Configuration

Copy the example file and set a unique API key before using protected API or UI actions:

```bash
copy .env.example .env
```

Production mode rejects missing, weak, and demo API keys. CORS origins must be explicit in production.

## CLI

Both `migrate` and `shiftiq` are installed. `migrate` is kept as the backward-compatible command.

```bash
migrate analyze tests/fixtures/sample_project --type react-hooks --confidence
migrate visualize tests/fixtures/sample_project
migrate run tests/fixtures/sample_project --type react-hooks --dry-run
migrate generate-tests tests/fixtures/sample_project
migrate compliance scan tests/fixtures/sample_project
migrate rollback <checkpoint-id> --path tests/fixtures/sample_project
```

Use `--apply` on `migrate run` only after reviewing the dry-run output.

## API

```bash
uvicorn code_migration.api.app:app --host 127.0.0.1 --port 8000
```

Unauthenticated:

- `GET /healthz`

API-key protected:

- `POST /api/v1/analyze`
- `POST /api/v1/run`
- `POST /api/v1/compliance/scan`
- `POST /api/v1/visualize`
- `POST /api/v1/rollback`
- `GET /api/v1/migrators`

Send the key as `X-API-Key`.

## UI

```bash
cd ui
npm install
npm run lint
npm run build
npm run dev
```

Set `VITE_API_BASE_URL` if the API is not served from the same origin. The UI stores the API key in local browser storage for local development convenience.

## MCP

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

Migration tools default to dry-run. Filesystem access is constrained by `MIGRATION_SECURITY__ALLOWED_ROOTS`.

## Docker

```bash
copy .env.example .env
docker compose config
docker compose build
docker compose up api
```

The Compose file does not hardcode a production API key. For container analysis, mount projects under `./projects`, which maps to `/data/projects`.

## Security Model

ShiftIQ is local-first by default. The core analysis path is designed around static file parsing and AST inspection, with no cloud LLM dependency or telemetry client in runtime requirements. Some optional modules can perform HTTP health checks when explicitly used for live migration workflows.

See:

- [Security model](docs/security-model.md)
- [MCP usage](docs/mcp-usage.md)
- [Migration safety](docs/migration-safety.md)
- [Compliance scanner](docs/compliance-scanner.md)
- [Audit report](AUDIT_REPORT.md)
