# Migration Safety

ShiftIQ migrations are dry-run by default across CLI, API, and MCP.

## Apply Flow

1. Resolve the target path under an allowed workspace root.
2. Skip generated/vendor directories and symlinks.
3. Read candidate files as text without executing them.
4. Generate diffs for review.
5. Create a rollback checkpoint before applied writes.
6. Write through a temporary file and atomically replace the original.

## Rollback

Applied migrations create checkpoint IDs. Use:

```bash
migrate rollback <checkpoint-id> --path <project>
```

Rollback behavior is covered by tests for checkpoint creation and file restoration. Review checkpoint storage size before running large migrations.

## Limits

Encoding and line-ending preservation is best effort for rewritten files. Review diffs before applying changes to production branches.
