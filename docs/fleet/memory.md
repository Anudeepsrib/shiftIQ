# Memory policy

Thread context may hold the current repository, workspace ID, source SHA, decisions, and approval state. Long-term memory may retain organization standards, preferred batch size, approved policies, ignored directories, conventions, and lessons that contain no source or sensitive values.

Allowed examples: “all framework migrations require reviewed dry runs”; “batches should contain at most 25 files.”

Prohibited: API/OAuth keys, PATs, raw source, secrets found by scans, PHI, PCI values, customer identifiers, and raw findings.

Fleet requires approval for memory writes by default. Keep it for interactive agents. Scheduled agents can otherwise pause indefinitely; if the organization disables memory approval for schedules, constrain the schedule prompt to non-sensitive policy summaries and review trace output.
