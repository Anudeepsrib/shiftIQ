# ShiftIQ + LangSmith Fleet

Fleet is ShiftIQ's optional agent experience, collaboration, approval, identity, and governance layer. ShiftIQ remains the deterministic static-analysis and migration engine. Local CLI, API, and stdio MCP workflows require neither Fleet nor a cloud model.

Implemented in this repository: authenticated Streamable HTTP MCP, workspace IDs, GitHub ingestion, typed results, dry-run/apply revision binding, idempotency, audit records, optional tracing, programmatic Fleet invocation, agent/sub-agent/skill artifacts, tests, and deployment examples.

Fleet-managed configuration: agent creation, tool Ask/Auto modes, sub-agent tool assignment, memory approvals, identity, integrations, GitHub/Slack/Teams connections, schedules, sharing, RBAC/ABAC, workspace secrets, model tier, spend controls, and self-hosting entitlement.

Start with [quickstart](quickstart.md), then follow [agent setup](agent-setup.md). The [feature matrix](feature-matrix.md) is the source of truth for implementation status.
