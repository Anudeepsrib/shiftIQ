# Security Policy

> Security architecture, threat model, and compliance framework for the **Code Migration Assistant**.
>
> For usage instructions, see the [User Guide](../USER_GUIDE.md). For setup, see the [Installation Guide](../INSTALLATION.md). For contributing security improvements, see the [Contributing Guide](../../CONTRIBUTING.md).

---

## Table of Contents

1. [Security Philosophy](#security-philosophy)
2. [Security Controls](#security-controls)
3. [Threat Model](#threat-model)
4. [Compliance Framework](#compliance-framework)
5. [Security Testing](#security-testing)
6. [Incident Response](#incident-response)
7. [Security Configuration](#security-configuration)
8. [Reporting Vulnerabilities](#reporting-vulnerabilities)
9. [Best Practices](#best-practices)

---

## Security Philosophy

The Code Migration Assistant follows a **zero-trust, defense-in-depth** architecture built on three principles:

### 1. Zero Code Execution

All analysis is performed using Python's `ast` module (Abstract Syntax Tree parsing). **No user-supplied code is ever executed.** This eliminates the most dangerous class of injection attacks — remote code execution — by design.

### 2. Defense in Depth

Every request passes through multiple independent security layers before touching the filesystem:

```
User Input → Input Validation → Path Sanitization → Rate Limiting → AST-Only Analysis → Audit Logging
```

A failure in any single layer does not compromise the system because every subsequent layer independently enforces its own constraints.

### 3. Audit Everything

Every file access, migration event, and security-relevant action is logged to immutable, append-only JSON structured logs with compliance metadata for GDPR, HIPAA, and SOC2.

---

## Security Controls

### Input Validation

**Module:** `src/code_migration/core/security/input_validator.py`

| Control | Details |
|---------|---------|
| Forbidden keywords | `eval`, `exec`, `__import__`, `open`, `globals()`, `locals()` |
| Forbidden modules | `os`, `sys`, `subprocess`, `socket`, `urllib`, `http`, `ftplib`, `smtplib` |
| File size limit | 10 MB max (`SafeCodeAnalyzer.MAX_FILE_SIZE`) |
| Line count limit | Configurable (`SafeCodeAnalyzer.MAX_LINES`) |
| Syntax validation | All code must parse via `ast.parse()` |
| Pattern matching | Regex-based detection of dangerous constructs |

### Path Sanitization

**Module:** `src/code_migration/core/security/path_sanitizer.py`

| Control | Details |
|---------|---------|
| Traversal prevention | Blocks `../`, `..\\`, and encoded variants |
| Canonicalization | Resolves symlinks and relative paths to absolute |
| Extension whitelist | `.py`, `.js`, `.jsx`, `.ts`, `.tsx`, `.vue`, `.html`, `.css`, `.json`, `.yaml`, `.yml`, `.md`, `.txt`, `.xml`, `.sql`, `.env` |
| Path length limit | 4096 characters max |
| Base path enforcement | All paths must resolve within the allowed project directory |

### Code Sandbox

**Module:** `src/code_migration/core/security/code_sandbox.py`

| Control | Details |
|---------|---------|
| AST-only analysis | `ast.parse()` + `ast.walk()` — no `eval`, no `exec` |
| Resource limits | Configurable timeout and memory limits |
| Complexity metrics | Cyclomatic and cognitive complexity calculation |
| Safe error handling | Malformed code returns structured error, never crashes |

### Secrets Detection

**Module:** `src/code_migration/core/security/secrets_detector.py`

| Capability | Details |
|------------|---------|
| Pattern library | 20+ patterns for API keys, passwords, tokens, certificates, connection strings |
| Severity levels | CRITICAL, HIGH, MEDIUM, LOW |
| Context analysis | Reports surrounding lines for manual review |
| Compliance mapping | Each finding tagged with relevant regulation (GDPR, HIPAA, PCI-DSS) |

### Cryptographic Operations

**Module:** `src/code_migration/core/security/crypto_handler.py`

| Control | Details |
|---------|---------|
| Atomic file writes | Write-then-rename prevents partial corruption |
| Integrity verification | SHA-256 checksums on all checkpoints |
| Automatic backups | Created before any file modification |
| Permission preservation | Original file permissions maintained on write |

### Audit Logging

**Module:** `src/code_migration/core/security/audit_logger.py`

| Control | Details |
|---------|---------|
| Format | Structured JSON (`.jsonl`), machine-readable |
| Compliance fields | GDPR, HIPAA, SOC2 metadata on every event |
| Rotation | `RotatingFileHandler`, 50 MB max per file, 10 backups |
| Retention | Configurable (default 90 days) |
| Log search | Query by time range, user, event type |
| Tamper protection | Append-only files with hash verification |

### Rate Limiting

**Module:** `src/code_migration/core/security/rate_limiter.py`

| Control | Details |
|---------|---------|
| Algorithm | Token bucket |
| Granularity | Per-operation limits (migrations, file ops, analysis) |
| Thread safety | Lock-protected concurrent access |
| Abuse detection | Automatic blocking on pattern violations |

---

## Threat Model

### Threat Matrix

| # | Threat | Risk | Mitigation | Controls |
|---|--------|------|------------|----------|
| 1 | **Code injection** | Malicious code executed via user input | AST-only parsing; forbidden keyword/module detection | `input_validator.py`, `code_sandbox.py` |
| 2 | **Path traversal** | Access files outside the project directory | Path canonicalization + base directory enforcement | `path_sanitizer.py` |
| 3 | **Information disclosure** | Sensitive data exposed in logs or output | Data anonymization; secrets detection; PII masking | `secrets_detector.py`, `audit_logger.py`, `anonymizer.py` |
| 4 | **Denial of service** | Resource exhaustion via large/complex inputs | Rate limiting; file size/line count limits; timeouts | `rate_limiter.py`, `code_sandbox.py` |
| 5 | **Data corruption** | Partial or incorrect file modifications | Atomic write-rename; SHA-256 checksums; auto-backups | `crypto_handler.py`, rollback engine |

### Attack Vector Examples

**Input injection (blocked):**
```python
eval('malicious_code()')        # Forbidden keyword
exec('system("rm -rf /")')      # Forbidden keyword
__import__('os').system('...')   # Forbidden module
```

**Path traversal (blocked):**
```python
"../../../etc/passwd"              # Traversal via ../
"..\\..\\windows\\system32\\sam"   # Windows traversal
"~/.ssh/id_rsa"                    # Home directory access
```

**Resource exhaustion (mitigated):**
```python
# Large files (>10 MB)             → Rejected by MAX_FILE_SIZE
# Complex files (>MAX_LINES)       → Rejected by line count check
# Long-running analysis (>timeout) → Killed by pytest-timeout / rate limiter
```

---

## Compliance Framework

### GDPR (General Data Protection Regulation)

| Article | Requirement | Implementation |
|---------|-------------|---------------|
| Art. 5 | Data processing principles | PII detection, data minimization |
| Art. 25 | Privacy by design | PII masking built into scan pipeline |
| Art. 32 | Security of processing | Input validation, encryption, audit logging |
| Art. 33 | Breach notification | Structured audit logs for incident response |
| Art. 35 | Data protection impact assessment | Compliance reports with risk scoring |

### HIPAA (Health Insurance Portability and Accountability Act)

| Safeguard | Requirement | Implementation |
|-----------|-------------|---------------|
| Administrative | Security policies and access management | Role-based audit logging |
| Technical | Access control, audit controls, integrity | PHI detection, SHA-256 checksums, structured logs |
| Physical | Device and facility security | N/A (software tool, not hosted infrastructure) |

### SOC2 (Service Organization Control 2)

| Trust Criteria | Implementation |
|----------------|---------------|
| Security | Input validation, path sanitization, rate limiting |
| Availability | Health monitoring in live migration mode |
| Processing Integrity | Atomic operations, checksum verification |
| Confidentiality | Secrets detection, PII anonymization |
| Privacy | GDPR-compliant PII handling |

### PCI-DSS (Payment Card Industry)

| Requirement | Implementation |
|-------------|---------------|
| Req. 3 — Protect stored data | Credit card pattern detection, data masking |
| Req. 7 — Restrict access | Path-based access control |
| Req. 10 — Track access | Comprehensive audit logging |

---

## Security Testing

### Automated Tests

The test suite includes dedicated security tests in `tests/security/`:

```bash
# Run all security tests
pytest tests/security/ -v

# Run specific test files
pytest tests/security/test_input_validation.py -v
pytest tests/security/test_path_sanitizer.py -v
```

### Static Analysis

```bash
# Security linter
bandit -r src/code_migration/

# Dependency vulnerability scanning
pip-audit

# General code quality
flake8 src/code_migration/
black --check src/code_migration/
```

### Security Review Checklist

For every pull request:

- [ ] No code execution (`eval`, `exec`, `__import__`)
- [ ] Input validation for all external inputs
- [ ] Path traversal prevention on all file operations
- [ ] Proper error handling without information disclosure
- [ ] Audit logging for security-relevant events
- [ ] Rate limiting where appropriate

---

## Incident Response

### Severity Classification

| Level | Criteria | Response Time |
|-------|----------|---------------|
| **Critical** | Data breach involving PII/PHI; system compromise; successful injection | Immediate |
| **High** | Failed bypass attempts; large-scale rate limit violations | 1 hour |
| **Medium** | Individual security control failures; minor compliance gaps | 4 hours |
| **Low** | Configuration issues; logging problems; documentation updates | 24 hours |

### Response Process

1. **Detection** — automated monitoring and alerting via audit logs
2. **Assessment** — impact analysis and severity classification
3. **Containment** — isolate affected systems or paths
4. **Eradication** — remove vulnerability; deploy patch
5. **Recovery** — restore normal operations; verify integrity
6. **Post-mortem** — update controls, tests, and documentation

---

## Security Configuration

### Default Settings

```yaml
# config/security_policy.yaml
security:
  input_validation:
    max_file_size: 10485760  # 10 MB
    max_lines: 1000
    max_line_length: 1000
    forbidden_keywords:
      - eval
      - exec
      - __import__
      - open
    forbidden_modules:
      - os
      - sys
      - subprocess
  
  path_sanitization:
    max_path_length: 4096
    allowed_extensions:
      - .py
      - .js
      - .jsx
      - .ts
      - .tsx
      - .vue
  
  rate_limiting:
    migrations_per_hour: 10
    file_ops_per_minute: 100
    analysis_timeout: 300
```

### Environment-Specific Tuning

| Setting | Development | Staging | Production |
|---------|-------------|---------|------------|
| Rate limits | Relaxed | Production-like | Strict |
| Logging | Verbose (DEBUG) | Comprehensive (INFO) | Minimal (WARNING) |
| Debug info | Enabled | Limited | Disabled |

---

## Reporting Vulnerabilities

### Responsible Disclosure

If you discover a security vulnerability, please report it responsibly:

1. **Email:** Open a [GitHub Security Advisory](https://github.com/Anudeepsrib/shiftIQ/security/advisories/new)
2. **Response time:** Within 48 hours
3. **Patch timeline:** Critical issues within 7 days

> [!CAUTION]
> Do **not** open a public GitHub issue for security vulnerabilities. Use the Security Advisory feature or email for responsible disclosure.

### Patch Management

| Severity | Patch Timeline |
|----------|---------------|
| Critical | 24 hours |
| High | 72 hours |
| Medium | 7 days |
| Low | Next release cycle |

---

## Best Practices

### For Users

1. Always use the latest release — security patches are applied promptly
2. Review audit logs periodically for unusual activity
3. Create checkpoints before major migrations
4. Run compliance scans before and after migration
5. Report anything suspicious

### For Contributors

1. Security is a first-class design constraint, not an afterthought
2. Never trust user input — validate everything
3. Use `PathSanitizer` for all file operations
4. Write security tests for every new feature
5. See the [Contributing Guide](../../CONTRIBUTING.md#security-requirements) for the full security review checklist

### For CI/CD

1. Run `bandit -r src/code_migration/` in the pipeline
2. Run `pytest tests/security/` on every PR
3. Use `pip-audit` to catch dependency vulnerabilities
4. Enable strict markers to prevent test configuration drift

---

## Related Documentation

| Document | Description |
|----------|-------------|
| [README](../../README.md) | Project overview and architecture |
| [User Guide](../USER_GUIDE.md) | Complete usage documentation |
| [Installation Guide](../INSTALLATION.md) | Setup instructions |
| [Contributing Guide](../../CONTRIBUTING.md) | Development workflow and security requirements |

---

**Last Updated:** 2026-02-11
**Version:** 3.0
**Next Review:** 2026-05-11
