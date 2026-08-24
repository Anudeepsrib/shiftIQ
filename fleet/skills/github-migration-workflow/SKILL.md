---
name: github-migration-workflow
description: Prepare an isolated GitHub-backed ShiftIQ workspace and coordinate a branch-and-PR modernization workflow.
---

# GitHub migration workflow

Resolve an `owner/repository` and ref with GitHub read tools, then call `prepare_github_workspace`. Preserve the pinned SHA through analysis and apply. Use a `shiftiq/<migration-type>/<timestamp>` branch for GitHub writes. Never push to the default branch, force-push, merge by default, or pass credentials as arguments.
