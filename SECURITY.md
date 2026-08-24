# Security Policy

ShiftIQ is a local-first development tool for code migration workflows. It is designed to avoid executing target project code during analysis, and protected API routes require `X-API-Key`.

## Supported Posture

- Static analysis and AST parsing by default.
- Dry-run migration mode by default.
- Rollback checkpoints before applied migrations.
- Path traversal and symlink escape protections for CLI/API/MCP operations.
- Redacted PII/PHI/PCI pattern-scan findings by default.
- Production startup validation for strong API keys and explicit CORS origins.
- Optional remote MCP header authentication, rate limiting, request correlation, and safe errors.
- UUID-only remote workspaces with quotas, expiry, path/symlink checks, and GitHub URL/ref validation.
- Revision-bound, idempotent remote apply and rollback in addition to Fleet approval policy.

## Not Guaranteed

ShiftIQ is not a sandbox for running untrusted code, not a formal compliance system, and not a substitute for security or legal review. Review generated diffs before applying migrations.

Fleet is an optional orchestration layer. Configure `apply_migration` and `rollback` as Ask tools; never place MCP/GitHub/LangSmith secrets in agent prompts, tool arguments, memory, or source control. See the [Fleet threat model](docs/fleet/security.md).

## Reporting

Open a private security advisory or contact the repository maintainer with reproduction steps, affected versions, and impact. Do not include real secrets or proprietary source code in reports.
