# Approval matrix

Fleet-managed tool modes are a mandatory layer; ShiftIQ's deterministic controls remain active beneath them.

| Action | Mode |
|---|---|
| Repository metadata, analyze, visualize, list migrators, compliance scan, plan, report | Auto |
| Dry run, test proposal | Auto |
| Apply/write source | **Ask** |
| Create/modify branch, commit | **Ask** |
| Open pull request | Ask or organization policy |
| Merge pull request | **Ask, always** |
| Rollback | **Ask** |
| Delete workspace | Auto or organization policy |
| Delete remote branch | **Ask, always** |
| Memory write | Fleet memory policy |

Before approval, show repository, branch/ref, SHA, workspace, dry-run operation, affected files, diff summary, risk, redacted findings, and checkpoint plan. Ordinary replies such as “yes” are not a substitute for the Fleet approval pause. Apply/rollback additionally reject mismatched or stale previews.
