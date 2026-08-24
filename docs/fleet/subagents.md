# Sub-agents

The canonical briefs live in `fleet/subagents/`.

| Agent | Purpose | Write access |
|---|---|---:|
| Repository Discovery | Identify repository shape and supported scope | No |
| Migration Architect | Interpret analysis and dependency waves | No |
| Security & Compliance Reviewer | Interpret redacted findings and policy blockers | No |
| Migration Executor | Dry run; approved apply only | Apply only |
| Verification Engineer | Static post-apply verification | No |
| Recovery Agent | Preview and approved rollback | Rollback only |
| Executive Migration Reporter | Evidence-based stakeholder reporting | No |

Sub-agent creation and tool selection occur in Fleet's Advanced settings. A role's prompt is not an authorization boundary; the MCP server and Fleet tool approval/access configuration remain authoritative.
