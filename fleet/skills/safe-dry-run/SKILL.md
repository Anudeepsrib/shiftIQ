---
name: safe-dry-run
description: Produce and review an idempotent ShiftIQ migration preview before any apply request.
---

# Safe dry run

Call `run_migration` with `dry_run=true` and a UUID operation ID. Summarize changed files and diffs from the result; never manufacture omitted content. Retain the dry-run operation ID because apply is cryptographically bound to its workspace revision.
