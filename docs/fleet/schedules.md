# Schedules

Fleet-managed schedules should use fixed identity and the prompts in `fleet/schedules/`:

- Daily health check: failed validation, stale workspace, unresolved risk; read-only.
- Weekly modernization report: aggregate confirmed progress and blockers; read-only.
- Memory maintenance: consolidate non-sensitive guidance only.

Do not schedule apply, rollback, branch deletion, merge, or arbitrary repository execution. Set spend limits and inspect early runs/traces before widening frequency.
