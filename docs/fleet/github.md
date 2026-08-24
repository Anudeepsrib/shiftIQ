# GitHub workflow

Use Fleet's GitHub integration for repository metadata, branches, commits, and pull requests. Use ShiftIQ MCP for the managed analysis workspace and deterministic migration.

`prepare_github_workspace` accepts only a GitHub `owner/name` or HTTPS `github.com` URL and validated ref. It shallow-clones without tags or LFS smudging, disables file/ext protocols and hooks, pins the resulting SHA, applies timeout/quota checks, and obtains private credentials only from `SHIFTIQ_GITHUB_TOKEN`.

Flow: resolve repo/ref, prepare workspace, analyze, scan, plan, dry run, present proposal, Fleet approval, create `shiftiq/<migration>/<timestamp>` branch, apply, verify, commit, and propose a PR. Never push to the default/protected branch, force-push, auto-merge, pass PATs in tool arguments, or weaken protections.
