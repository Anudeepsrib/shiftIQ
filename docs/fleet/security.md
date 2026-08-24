# Threat model

| Threat | Boundary | Mitigation | Residual risk |
|---|---|---|---|
| Prompt injection | Repo/Fleet | Agent policy treats repository text as data; tools expose facts | Model may summarize malicious text poorly |
| Path traversal/symlink | MCP/workspace | UUID-only schemas, resolved-root checks, symlink skipping | Host compromise is out of scope |
| SSRF/malicious URL | Git ingestion | Constructed HTTPS GitHub URL; validated owner/name/ref | GitHub-hosted content can be huge/malicious |
| Credential leakage | Fleet/MCP | Workspace header secret; tokens absent from args/results/logs | Runtime administrator can access process secrets |
| Unauthorized repo | GitHub | Fleet identity/OAuth plus protected runtime token scope | Mis-scoped service token remains dangerous |
| Approval bypass/stale approval | Fleet/apply | Ask mode plus required preview/revision fingerprint | Admin can misconfigure Ask mode |
| Duplicate destructive call | MCP | UUID idempotency ledger | Shared storage needs external coordination if horizontally scaled |
| Poisoned memory | Fleet | Memory policy/approval; no raw repo or findings | Human-approved bad policy can persist |
| Malicious tool output | Fleet | Typed results and agent policy; no source authority | Model can still misinterpret valid output |
| Source exfiltration | MCP | Relative file listing; no raw-source read tool | Diffs contain changed source excerpts |
| Dependency attack | Build/runtime | Locked ranges, CI audit, non-root image | Upstream compromise remains possible |
| Sandbox escape | Verification | Execution disabled by default; isolated opt-in only | Isolation depends on deployment platform |
| Log leakage | MCP/audit | Selected metadata and generic unexpected errors | Diff/tool traces need retention/access policy |

Compliance checks support controls but do not make ShiftIQ GDPR, HIPAA, SOC 2, or PCI-DSS certified.
