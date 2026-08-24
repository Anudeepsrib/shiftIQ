# Agent setup

This is Fleet-managed configuration.

1. In LangSmith, switch to Fleet and create an agent named **ShiftIQ Migration Commander** with the description in `fleet/AGENTS.md`.
2. Paste `fleet/AGENTS.md` into Knowledge > Instructions.
3. In Connections, add a custom MCP named `ShiftIQ` with URL `https://<host>/mcp`. Choose Headers and add `Authorization: Bearer <secret>`.
4. Discover the tools. Set `apply_migration` and `rollback` to **Ask**; set read and preview tools to Auto. Set `cleanup_workspace` according to retention policy.
5. Add the seven helpers from `fleet/subagents/` under Advanced settings > Subagents. Give each only the tools named in its instructions.
6. Add/share skills from `fleet/skills/` in Knowledge > Skills.
7. Choose fixed identity for shared/channel/scheduled service agents or user identity for per-user repository access. Identity cannot be changed after it is set.
8. Configure Sharing, channels, schedules, memory approval, GitHub connection, and Enterprise access controls as described in the linked documents.
9. Test the scenarios in `fleet/evaluations/scenarios.jsonl`, especially stale approval and prompt injection.

Managed Fleet currently offers Fast, Pro, and Max model tiers. Custom model requirements are account/enterprise configuration; contact the LangChain account team rather than hard-wiring a provider into ShiftIQ.
