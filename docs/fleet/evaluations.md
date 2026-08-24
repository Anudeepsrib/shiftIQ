# Evaluations

`fleet/evaluations/scenarios.jsonl` covers analysis-only behavior, required workflow, dry-run bypass, path escape, repository prompt injection, redaction, recovery, rollback, invented migrators, protected branches, permission boundaries, and stale approval.

Use these as LangSmith dataset examples with expected behavior labels. Score tool-selection accuracy, unauthorized-write rate, dry-run/approval compliance, unsupported-migration detection, hallucination rate, rollback correctness, leakage rate, latency, and model cost. Normal CI tests deterministic gateway behavior without Fleet credentials; credentialed Fleet evaluations should run only in a separately gated environment.
