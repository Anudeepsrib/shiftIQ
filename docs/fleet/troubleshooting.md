# Troubleshooting

- `/readyz` is 503: set a non-empty `SHIFTIQ_MCP_API_KEY`, or explicitly disable auth only for isolated local testing.
- Fleet cannot discover tools: verify public HTTPS, `/mcp`, header authentication, and the exact stable URL. Re-add tools after changing an MCP URL.
- `source_revision_changed`: files changed after preview; create and review a new dry run/rollback preview.
- `approval_required`: use the dedicated preview first and ensure apply/rollback is configured Ask in Fleet.
- workspace not found: UUID is invalid, expired, deleted, or belongs to another deployment volume.
- GitHub preparation fails: check `owner/name`, ref, outbound HTTPS, Git availability, token scope, timeout, and quota. Tokens must remain runtime secrets.
- tracing absent: Fleet parent traces are in the agent UI; service-side spans additionally require the optional `langsmith` package and tracing environment variables.
