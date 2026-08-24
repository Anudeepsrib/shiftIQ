---
name: migration-verification
description: Verify an applied ShiftIQ migration using non-executing static checks.
---

# Migration verification

Call `verify_migration`, report remaining candidates and `execution_performed`, and connect the result to the apply operation/checkpoint. On failure, do not repair automatically; hand off to recovery for a rollback decision.
