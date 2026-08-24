# Observability and audit

Fleet records each agent run, decision, and tool call in a LangSmith trace. ShiftIQ returns operation/workspace/source/checkpoint metadata inside the traced MCP result and writes a local `audit.jsonl` plus durable operation records under `SHIFTIQ_WORKSPACE_ROOT`.

Optional service-side spans are disabled by default. Install `langsmith`, set `SHIFTIQ_LANGSMITH_TRACING=true`, `LANGSMITH_API_KEY`, and `LANGSMITH_PROJECT`. Do not trace source contents or raw sensitive findings.

Correlation fields: operation ID, workspace ID, repository, source SHA/revision, migration, dry-run state, risk, checkpoint, tool, agent, actor, trace ID, and timestamp. Fleet supplies the parent tool trace automatically; a caller may also send `X-Fleet-Trace-ID`/`X-Fleet-Actor` for explicit audit correlation.
