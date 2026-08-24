# RBAC, ABAC, and sharing

Fleet tool access control is an Enterprise feature. Configure it in Fleet/LangSmith rather than simulating roles inside ShiftIQ.

Recommended roles: Viewer (read reports), Developer (analyze/plan/dry run), Approver (approved apply/rollback), Compliance Reviewer (scan/audit only), Migration Administrator (agent/workspace configuration), Platform Administrator (workspace governance).

Grant developers `mcp-servers:read` and `mcp-servers:invoke`, reserving create/update/delete for administrators. Tag the ShiftIQ MCP server and GitHub integration by business unit/environment. ABAC deny must win for restricted repositories or production risk unless the approved role/policy explicitly matches.

Publish the canonical agent from Platform Engineering; Security reviews tool modes; broader developers get Run/Clone; only the platform team gets Edit. Workspace threads remain user-private even when agent instructions/tools are shared.
