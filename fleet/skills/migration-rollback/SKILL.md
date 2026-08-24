---
name: migration-rollback
description: Preview and restore a ShiftIQ checkpoint with stale-revision and approval protection.
---

# Migration rollback

Use `get_checkpoint`, then `preview_rollback` with a UUID. Explain affected files before calling `rollback` with a second UUID through Fleet Ask approval. After restoration, call verification and report the outcome.
