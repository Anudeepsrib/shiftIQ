# Architecture

```mermaid
flowchart TD
  U[Developer / Manager] --> F[Fleet Chat / Slack / Teams]
  F --> C[ShiftIQ Migration Commander]
  C --> S[Skills and sub-agents]
  C --> G[GitHub integration]
  C --> M[Remote MCP over HTTPS]
  M --> A[Auth, correlation, rate limits]
  A --> W[Managed workspace IDs]
  W --> E[ShiftIQ Core]
  E --> D[Static analysis and deterministic migrators]
  E --> R[Checkpoints, atomic writes, rollback]
  C --> L[LangSmith Fleet trace]
  M --> J[ShiftIQ audit and operation ledger]
```

Fleet decides what work should happen. ShiftIQ decides how migrations safely happen. Agent reasoning cannot override dry-run defaults, managed roots, redaction, stale-revision checks, checkpoint-before-write, atomic writes, or idempotency.

Remote callers see a UUID `workspace_id`, repository/ref/SHA metadata, relative filenames, and structured results. Absolute host paths never appear in remote tool schemas.
