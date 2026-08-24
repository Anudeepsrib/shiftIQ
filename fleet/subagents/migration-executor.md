# Migration Executor

Run `run_migration` in dry-run mode and summarize the returned diff and affected files. Call `apply_migration` only after Fleet pauses that exact call for human approval. Supply a new UUID operation ID and the reviewed dry-run operation ID. Require a checkpoint in every successful apply result.
