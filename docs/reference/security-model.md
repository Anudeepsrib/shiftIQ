# Security Model

ShiftIQ is local-first by default. Runtime dependencies do not include cloud LLM clients, analytics SDKs, or telemetry services.

## Boundaries

- Allowed workspace roots are configured by `MIGRATION_SECURITY__ALLOWED_ROOTS`.
- Paths are resolved before use and must stay inside an allowed root.
- Symlink targets outside the workspace are rejected.
- File scans enforce maximum file size and file count limits.
- Protected API routes require `X-API-Key`.

## Static Analysis

Analysis is designed to parse source text and ASTs without importing target modules or running target test suites. Dependency and code-quality scoring use static heuristics by default.

## Production Settings

Production mode requires:

- A strong non-demo `MIGRATION_API_KEY`.
- Explicit CORS origins.
- Debug/development behavior disabled.
- API docs disabled unless intentionally enabled.

## Limitations

Optional live-migration modules can make HTTP health checks when explicitly invoked. ShiftIQ does not claim formal isolation against every adversarial repository; use OS/container controls for untrusted codebases.
