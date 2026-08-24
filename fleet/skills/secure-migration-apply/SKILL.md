---
name: secure-migration-apply
description: Apply a reviewed ShiftIQ dry run through Fleet's human-approval gate.
---

# Secure migration apply

Before the approval pause, show repository/ref/SHA, workspace, migration, affected files, diff summary, risk, findings, dry-run operation ID, and checkpoint plan. Call `apply_migration` with a new UUID only through Fleet Ask approval. Stop if the source revision changed or no checkpoint is returned.
