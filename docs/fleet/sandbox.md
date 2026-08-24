# Sandbox policy

ShiftIQ static verification is on; execution verification is off. The repository does not assume Fleet sandbox entitlement or execute target code through MCP.

If the account provides an approved sandbox, use it only for disposable clones, diff inspection, CLI/report generation, and separately approved validation commands. Enforce CPU/memory/time limits, non-root execution, no privileged mode or Docker socket, no host-sensitive mounts, and restricted network. Label every such validation as execution of untrusted repository code.

Sandbox execution is Fleet/account-managed and remains optional; it does not replace ShiftIQ path, dry-run, checkpoint, or atomic-write controls.
