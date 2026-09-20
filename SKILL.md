---
name: code-migration
description: |
  Enterprise-grade code migration assistant with AI-powered risk assessment,
  visual dependency planning, surgical rollback, and regulatory compliance 
  scanning. Trigger when user mentions: migrate, upgrade, convert, modernize, 
  refactor, transform, or asks about moving from one technology to another.
version: 1.0.0
author: Open Source Contributor
license: Apache-2.0
---

# Code Migration Assistant

> For full documentation, see the [README](README.md), [User Guide](docs/getting-started/user-guide.md), and [Installation Guide](docs/getting-started/installation.md).

## When to Use This Skill

Activate when the user wants to:
- **Migrate frameworks** — React class → hooks, Vue 2 → 3, Python 2 → 3, JS → TypeScript
- **Assess migration risk** — confidence scoring, complexity analysis, cost estimation
- **Visualize dependencies** — interactive graphs, migration wave planning
- **Scan for compliance** — PII/PHI detection, secrets scanning, GDPR/HIPAA/SOC2 reports
- **Roll back safely** — Git-based checkpoints, surgical file-level restore

## Supported Migration Types

| Type | Source → Target | Status |
|------|----------------|--------|
| `react-hooks` | React Class Components → Hooks | ✅ Enterprise |
| `vue3` | Vue 2 Options API → Composition API | ✅ Enterprise |
| `python3` | Python 2.7 → Python 3.x | ✅ Enterprise |
| `typescript` | JavaScript → TypeScript | 🧪 Beta |

## Workflow

### 1. Analyze

Always start by analyzing the codebase to understand the migration scope:

```bash
migrate analyze <path> --type <type> --confidence
```

- Review the confidence score and risk level
- Identify breaking changes and dependency issues
- Estimate time and cost

### 2. Plan

Propose a migration plan to the user:

```bash
migrate visualize <path> --output migration-graph.html
migrate plan <path> --type <type> --timeline --output plan.html
```

- Show the dependency graph
- Explain the migration wave ordering
- List affected files

### 3. Execute

Run the migration with safety controls:

```bash
# ALWAYS suggest --dry-run first
migrate run <path> --type <type> --dry-run

# Then execute with auto-rollback
migrate run <path> --type <type> --auto-rollback
```

- Confirm with the user before applying changes
- Create a checkpoint before any modification
- Use `--auto-rollback` to revert on failure

### 4. Verify

After migration, verify the results:

```bash
migrate verify <path> --type <type>
migrate compliance scan <path> --pii --secrets
```

## Security & Safety

- **Zero Code Execution** — all analysis uses `ast.parse()`, never `eval()` or `exec()`
- **Automatic Backups** — checkpoints created in `.migration-backups/` before any write
- **Path Sanitization** — all file paths validated to prevent directory traversal
- **Atomic Writes** — write-then-rename prevents partial file corruption
- **Audit Logging** — every action logged for compliance (GDPR, HIPAA, SOC2)

See the full [Security Policy](docs/security/SECURITY.md) for details.

## Error Handling

If a migration fails:

1. **Check the output** — look for specific error messages and file paths
2. **Rollback** — use `migrate rollback --to <checkpoint-id>` to restore
3. **Diagnose** — use `migrate analyze <path> --type <type> --detailed` for deeper analysis
4. **Report** — open an issue with the error details and `migrate status` output

## Core Modules

| Module | Purpose |
|--------|---------|
| `core/security` | Input validation, path sanitization, audit logging, rate limiting |
| `core/compliance` | PII/PHI detection, data lineage, anonymization, audit reports |
| `core/confidence` | Risk scoring, complexity analysis, cost/time estimation |
| `core/copilot` | AI chat interface with RAG knowledge retrieval |
| `core/cost_estimator` | ROI analysis, budget planning, executive reports |
| `core/live_migration` | Canary deployments, health checks, auto-rollback |
| `core/rollback` | Git-based checkpoints, surgical file restore |
| `core/test_generation` | Automated test scaffolding, mock generation |
| `core/visualizer` | Dependency graphs, migration waves, timelines |
