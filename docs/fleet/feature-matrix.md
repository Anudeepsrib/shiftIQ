# Fleet feature matrix

Status reflects the repository and public Fleet documentation reviewed on 2026-08-23.

| Fleet feature | Applicable? | Implementation | Configuration | Tier/preview | Demo | Status |
|---|---:|---|---|---|---|---|
| Fleet agent | Yes | `fleet/AGENTS.md` | Fleet UI | Fleet plan | Full | Artifact + UI |
| Remote MCP | Yes | Streamable HTTP gateway | Code + Fleet Connections | MCP create permission | All | Implemented |
| Header auth | Yes | Bearer/X-API-Key | Runtime secret + Fleet header | Standard | All | Implemented |
| GitHub | Yes | Safe ingestion + Fleet integration workflow | Runtime/Fleet OAuth | Integration access | Full | Implemented/config |
| Skills | Yes | Nine Agent Skills | Fleet Knowledge | Standard | All | Artifacts + UI |
| Sub-agents | Yes | Seven role briefs | Fleet Advanced | Standard | Full | Artifacts + UI |
| Thread memory | Yes | Policy/instructions | Fleet thread | Standard | All | Fleet-managed |
| Long-term memory | Yes | Policy | Fleet Knowledge | Standard | Scheduled | Fleet-managed |
| Human approval | Yes | Revision-bound apply/rollback | Fleet tool Ask mode | Standard | Full/Rollback | Code + UI |
| Central approvals | Yes | Tool design supports pause | Fleet inbox | Standard | Full | Fleet-managed |
| Agent identity | Yes | Two-model guidance | Fleet identity | Cannot change later | Channels | Fleet-managed |
| Slack | Yes | Safe prompts/policy | Fleet Integrations/Channels | Slack admin | Channel | Fleet-managed |
| Microsoft Teams | Yes | Safe prompts/policy | Fleet Channels | Account availability | Channel | Fleet-managed |
| Schedules | Yes | Three read-only prompts | Fleet Schedule | Fixed identity | Reports | Fleet-managed |
| Custom models | Conditional | Model-neutral tools | Fleet/account team | Enterprise/account | All | Account-managed |
| LangSmith tracing | Yes | Fleet trace + optional spans/audit | Fleet + env | Trace plan | All | Implemented |
| Evaluations | Yes | Scenario dataset + dimensions | LangSmith datasets | LangSmith | Safety | Artifact |
| Programmatic API | Yes | REST client + SDK docs | Env/PAT | Agent owner rules | Analyze | Implemented |
| Idempotency | Yes | Durable UUID records | Workspace volume | None | Full | Implemented |
| Workspace/private agent | Yes | Publishing guidance | Fleet Sharing | Standard | All | Fleet-managed |
| Clone/Run/Edit | Yes | Publishing model | Fleet Sharing | Workspace access | All | Fleet-managed |
| RBAC/ABAC | Yes | Guidance for MCP/integration tags | LangSmith settings/API | Enterprise | Governance | Fleet-managed |
| Workspace integration policy | Yes | Guidance | Settings > Integrations | Enterprise | Governance | Fleet-managed |
| Workspace secrets | Yes | No secrets in prompts/tools | Fleet/runtime secret store | Workspace | All | Fleet-managed |
| Spend controls/LCUs | Yes | Read-only schedule guidance | Fleet workspace | Plan/account | Reports | Fleet-managed |
| Sandbox | Conditional | Static-only default/policy | Fleet account | Account-dependent | Verify | Not assumed |
| Self-updates | Restricted | Immutable security policy | Fleet instructions | Standard | All | Fleet-managed |
| Self-hosted/BYOC Fleet | Conditional | Deployment topology docs | LangChain account | Beta/account-gated | All | Documentation |
