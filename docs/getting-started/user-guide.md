# User Guide

> **Code Migration Assistant** — Enterprise-grade, security-first code migration with AI-powered analysis.
>
> This guide covers everything from your first migration to advanced production deployments. For installation, see the [Installation Guide](installation.md). For security details, see the [Security Policy](../security/SECURITY.md).

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Command Reference](#command-reference)
3. [Migration Types](#migration-types)
4. [Advanced Features](#advanced-features)
5. [Configuration](#configuration)
6. [Python API](#python-api)
7. [Troubleshooting](#troubleshooting)
8. [Best Practices](#best-practices)

---

## Quick Start

### Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | 3.8+ | CPython recommended |
| Git | 2.x+ | Required for rollback functionality |
| RAM | 8 GB+ | Recommended for large codebases |

> [!TIP]
> See the [Installation Guide](installation.md) for detailed platform-specific setup instructions.

### Install

```bash
git clone https://github.com/anudeepsrib/code-migration-assistant.git
cd code-migration-assistant
pip install -r requirements.txt
pip install -e .
python -m code_migration --version
```

### Your First Migration

```bash
# 1. Analyze — understand the risk before you touch anything
migrate analyze ./my-project --type react-hooks --confidence

# 2. Plan — visualize dependencies and migration waves
migrate visualize ./my-project --output migration-graph.html

# 3. Dry run — preview exactly what will change
migrate run ./my-project --type react-hooks --dry-run

# 4. Execute — migrate with automatic rollback on failure
migrate run ./my-project --type react-hooks --auto-rollback
```

---

## Command Reference

### Analysis

```bash
# Basic analysis
migrate analyze ./project --type react-hooks

# Detailed confidence analysis with risk breakdown
migrate analyze ./project --type react-hooks --confidence --detailed

# Risk assessment
migrate analyze ./project --type react-hooks --risk-analysis

# Export HTML report
migrate analyze ./project --type react-hooks --report-html --output analysis.html
```

### Visual Planning

```bash
# Interactive dependency graph (D3.js)
migrate visualize ./project --output graph.html

# Migration plan with timeline
migrate plan ./project --type react-hooks --timeline --output timeline.html

# Interactive planning mode
migrate plan ./project --type react-hooks --interactive
```

### Execution

```bash
# Dry run (preview changes, no files modified)
migrate run ./project --type react-hooks --dry-run

# Execute migration
migrate run ./project --type react-hooks

# Execute with automatic rollback on error
migrate run ./project --type react-hooks --auto-rollback

# Migrate specific files only
migrate run ./src/components --type react-hooks --files Button.jsx,UserProfile.jsx
```

### Rollback

```bash
# Create a named checkpoint
migrate checkpoint create "Before migration"

# List all checkpoints
migrate checkpoint list

# Rollback to a checkpoint
migrate rollback --to 20250208_143022

# Surgical rollback (specific files only)
migrate rollback --to 20250208_143022 --files src/components/Button.jsx

# Preview rollback without applying
migrate rollback --to 20250208_143022 --dry-run
```

> [!NOTE]
> Checkpoints use Git-based snapshots with SHA-256 integrity verification. See [Time Machine Rollback](#time-machine-rollback) for details.

### Compliance

```bash
# Scan for PII
migrate compliance scan ./project --pii

# Scan for secrets (API keys, tokens, passwords)
migrate compliance scan ./project --secrets

# Generate compliance reports (SOC2, GDPR, HIPAA)
migrate compliance report --soc2 --gdpr --hipaa --output compliance/

# Anonymize sensitive data
migrate compliance anonymize ./project --output anonymized/
```

### AI Co-pilot

```bash
# Start interactive AI assistant
migrate copilot ./my-project
```

### Utility

```bash
# Show help
migrate --help

# Show version
migrate --version

# List available migration types
migrate list-types

# Check system status
migrate status

# Validate configuration
migrate config validate
```

---

## Migration Types

### React Hooks Migration

| | |
|---|---|
| **Source** | React Class Components |
| **Target** | Functional Components + Hooks |
| **Confidence** | 85–95% |
| **Status** | ✅ Enterprise |

```bash
migrate analyze ./react-project --type react-hooks
migrate run ./react-project --type react-hooks
```

**What gets transformed:**
- Class components → functional components
- `componentDidMount` / `componentDidUpdate` / `componentWillUnmount` → `useEffect`
- `this.state` + `this.setState` → `useState`
- Context consumers → `useContext`
- Test files updated to match new component signatures

**Example:**

```jsx
// Before ─────────────────────────────────────
class UserProfile extends Component {
    constructor(props) {
        super(props);
        this.state = { user: null, loading: true };
    }
    
    componentDidMount() {
        this.fetchUser();
    }
    
    async fetchUser() {
        const response = await fetch(`/api/users/${this.props.id}`);
        this.setState({ user: await response.json(), loading: false });
    }
    
    render() {
        const { user, loading } = this.state;
        if (loading) return <div>Loading...</div>;
        return <div>{user.name}</div>;
    }
}

// After ──────────────────────────────────────
const UserProfile = ({ id }) => {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);
    
    useEffect(() => {
        const fetchUser = async () => {
            const response = await fetch(`/api/users/${id}`);
            setUser(await response.json());
            setLoading(false);
        };
        fetchUser();
    }, [id]);
    
    if (loading) return <div>Loading...</div>;
    return <div>{user.name}</div>;
};
```

### Vue 3 Migration

| | |
|---|---|
| **Source** | Vue 2 Options API |
| **Target** | Vue 3 Composition API |
| **Confidence** | 80–90% |
| **Status** | ✅ Enterprise |

```bash
migrate analyze ./vue-project --type vue3
migrate run ./vue-project --type vue3
```

**What gets transformed:**
- Options API (`data`, `methods`, `computed`, `watch`) → Composition API (`ref`, `reactive`, `computed`, `watch`)
- Lifecycle hooks → `onMounted`, `onUpdated`, `onUnmounted`
- Reactivity system upgraded
- Plugin system updates
- Optional TypeScript support

### Python 3 Migration

| | |
|---|---|
| **Source** | Python 2.7 |
| **Target** | Python 3.x |
| **Confidence** | 90–98% |
| **Status** | ✅ Enterprise |

```bash
migrate analyze ./python-project --type python3
migrate run ./python-project --type python3
```

**What gets transformed:**
- `print` statements → `print()` function calls
- Integer division behavior (`/` vs `//`)
- `unicode` / `str` → unified `str`
- Exception syntax (`except E, e:` → `except E as e:`)
- Library imports updated to Python 3 equivalents

### TypeScript Migration

| | |
|---|---|
| **Source** | JavaScript |
| **Target** | TypeScript |
| **Confidence** | 70–85% |
| **Status** | 🧪 Beta |

```bash
migrate analyze ./js-project --type typescript
migrate run ./js-project --type typescript
```

**What gets transformed:**
- Type inference and annotation
- Interface generation from usage patterns
- `tsconfig.json` creation
- JSDoc comments → TypeScript types

---

## Advanced Features

### Migration Confidence Analyzer

Get a quantified risk assessment before committing to any migration:

```bash
migrate analyze ./project --type react-hooks --confidence --detailed
```

**Output example:**

```
🔍 Analyzing Migration Confidence...

Overall Confidence: 87/100 (LOW RISK)
Migration Complexity: MODERATE

Risk Factors:
├─ Test Coverage: 92/100 ✅
├─ Code Complexity: 78/100 ✅
├─ Dependencies: 85/100 ✅
├─ Code Quality: 90/100 ✅
├─ Breaking Changes: 75/100 ⚠️
└─ Team Experience: 80/100 ✅

📊 Estimates:
├─ Time: 24.5 hours
├─ Cost: $2,450 (at $100/hr)
└─ Risk Level: LOW

✅ RECOMMENDATIONS:
1. Create staging environment for testing
2. Plan incremental rollout (not big-bang)
3. Set up monitoring and alerting
4. Add more tests for complex components
```

The confidence score evaluates six dimensions:
- **Test coverage** — are the migration targets well-tested?
- **Code complexity** — cyclomatic complexity across all files
- **Dependency health** — outdated, deprecated, or vulnerable packages
- **Code quality** — linter warnings, dead code, duplication
- **Breaking changes** — API surfaces at risk
- **Team experience** — calibrated to your team's familiarity with the target

### Visual Migration Planner

Interactive dependency visualization using D3.js and NetworkX:

```bash
# Dependency graph
migrate visualize ./project --output graph.html

# Migration timeline (Gantt chart)
migrate plan ./project --type react-hooks --timeline --output timeline.html
```

Features:
- Zoom, pan, and drag on the interactive graph
- Color-coded nodes by migration risk level
- Topological sort produces ordered **migration waves** — leaf nodes first
- Gantt chart export for project management tools

### Time Machine Rollback

Git-based checkpoint system with surgical precision:

```bash
# Create checkpoint
migrate checkpoint create "Before major changes"

# Full rollback
migrate rollback --to 20250208_143022

# Partial rollback (specific files only)
migrate rollback --to 20250208_143022 --files src/components/Button.jsx

# Verify checkpoint integrity
migrate checkpoint verify 20250208_143022
```

Features:
- SHA-256 checksums on every snapshot
- File-level surgical rollback
- Automatic pre-migration checkpoints
- Conflict detection and resolution

### Live Migration Mode

Production-safe migration with traffic management:

```bash
migrate live-migration ./project --type react-hooks --canary --auto-rollback
```

Features:
- **Canary deployments** — gradual traffic splitting (5% → 25% → 100%)
- **Health monitoring** — real-time endpoint checks
- **Auto-rollback** — revert on error rate or latency spikes
- **Structured metrics** — observability throughout

### Compliance Scanning

Enterprise compliance for regulated industries. See the [Security Policy](../security/SECURITY.md) for the full compliance framework.

```bash
# Full compliance scan
migrate compliance scan ./project --pii --secrets

# Generate formatted reports
migrate compliance report --soc2 --gdpr --hipaa --output compliance/

# Anonymize data
migrate compliance anonymize ./project --output anonymized/
```

**PII patterns detected:** email, SSN, phone, credit card, passport, driver's license, IP address, date of birth, physical address

**PHI patterns detected:** medical record numbers, ICD-9/10 diagnosis codes, patient IDs, CPT procedure codes, health insurance IDs

**Regulations mapped:** GDPR, HIPAA, PCI-DSS, CCPA, SOC2

### Cost Estimator & ROI Analyzer

Data-driven migration budgeting for executive stakeholders:

- Per-file and per-module cost estimates
- Projected ROI with break-even timeline
- Executive-ready summary reports
- Resource allocation recommendations by sprint/phase

### Test Generation Engine

Automated test scaffolding for migrated code:

```bash
migrate generate-tests ./src/components --type react-hooks
```

- Unit test generation from function signatures and AST analysis
- Integration test templates
- Mock generation for external dependencies
- Coverage tracking (line, branch, function)

---

## Configuration

### Environment Variables

Create a `.env` file in your project root or set via your shell:

```bash
# Security
MIGRATION_SECURITY_LEVEL="high"      # high | medium | low
MIGRATION_AUDIT_LOGGING="true"       # Enable audit trail

# Performance
MIGRATION_MAX_WORKERS="4"            # Concurrent workers
MIGRATION_TIMEOUT="300"              # Per-operation timeout (seconds)
```

### Security Policy (`config/security_policy.yaml`)

```yaml
security:
  input_validation:
    max_file_size: 10485760  # 10 MB
    max_lines: 1000
    allowed_extensions: ['.py', '.js', '.jsx', '.ts', '.tsx', '.vue']
  
  path_sanitization:
    allowed_base: "./project"
    max_path_length: 4096
  
  rate_limiting:
    migrations_per_hour: 10
    file_ops_per_minute: 100
```

### Compliance Rules (`config/compliance_rules.yaml`)

```yaml
compliance:
  gdpr:
    pii_detection: true
    data_retention_days: 90
  
  hipaa:
    phi_detection: true
    audit_logging: true
  
  soc2:
    audit_trail: true
    encryption_required: true
```

### Migration Rules (`config/migration_rules.yaml`)

```yaml
migrations:
  react-hooks:
    convert_lifecycle: true
    update_tests: true
    preserve_comments: true
  
  vue3:
    update_dependencies: true
    convert_options_api: true
    typescript_support: false
```

---

## Python API

You can use the migration assistant programmatically in your own tools and scripts:

```python
from pathlib import Path
from code_migration.core.confidence import MigrationConfidenceAnalyzer
from code_migration.core.visualizer import VisualMigrationPlanner
from code_migration.core.rollback import TimeMachineRollback
from code_migration.core.compliance import PIIDetector

# ── Confidence Analysis ──────────────────────────────────
analyzer = MigrationConfidenceAnalyzer("./my-project")
confidence = analyzer.calculate_confidence("react-hooks", team_experience=70)
print(f"Confidence: {confidence.overall_score}/100")
print(f"Risk Level: {confidence.risk_level}")
print(f"Estimated Hours: {confidence.estimated_hours}")

# ── Visual Planning ──────────────────────────────────────
planner = VisualMigrationPlanner("./my-project")
planner.build_dependency_graph()
waves = planner.calculate_migration_waves()
planner.generate_d3_visualization("migration-graph.html")

# ── Rollback ─────────────────────────────────────────────
rollback = TimeMachineRollback("./my-project")
checkpoint_id = rollback.create_checkpoint("Pre-migration backup")
# ... execute migration ...
# rollback.rollback(checkpoint_id)  # if something goes wrong

# ── PII Scanning ─────────────────────────────────────────
with PIIDetector(Path("./my-project")) as detector:
    results = detector.scan_directory(file_extensions=['.py', '.js'])
    print(f"Files with PII: {results['files_with_pii']}")
    print(f"Total findings: {results['total_findings']}")
```

---

## Troubleshooting

### Migration Fails with Security Error

**Symptom:** Migration blocked by security controls.

```bash
# Check what's being blocked
migrate analyze ./file.jsx --security-check

# Temporarily adjust security level
MIGRATION_SECURITY_LEVEL=medium migrate run ./project --type react-hooks
```

> [!WARNING]
> Lowering the security level bypasses important safety checks. Only do this if you understand the risk. See the [Security Policy](../security/SECURITY.md) for details on each control.

### Memory Issues with Large Projects

**Symptom:** Out of memory errors on codebases with 1000+ files.

```bash
# Limit concurrent workers
migrate analyze ./large-project --workers 2 --batch-size 50

# Use incremental analysis
migrate analyze ./large-project --incremental
```

### Rollback Fails

**Symptom:** Cannot rollback to checkpoint.

```bash
# Check checkpoint integrity
migrate checkpoint verify 20250208_143022

# Force rollback (bypasses conflict checks)
migrate rollback --to 20250208_143022 --force
```

### Compliance Scan Too Slow

**Symptom:** PII/PHI scanning takes too long on large projects.

```bash
# Limit file types to speed up scanning
migrate compliance scan ./project --pii --extensions .py,.js,.jsx

# Use parallel processing
migrate compliance scan ./project --pii --parallel
```

### Debug Mode

```bash
# Enable verbose logging
MIGRATION_DEBUG=true migrate analyze ./project --type react-hooks --verbose

# Review audit logs
tail -f .migration-logs/security_audit.jsonl
```

---

## Best Practices

### Before Migration

1. **Create a checkpoint** — always have a safety net
   ```bash
   migrate checkpoint create "Pre-migration backup"
   ```

2. **Run confidence analysis** — understand your risk
   ```bash
   migrate analyze ./project --type react-hooks --confidence --risk-analysis
   ```

3. **Test on a small subset** — validate the transformation
   ```bash
   migrate run ./src/components --type react-hooks --dry-run --files Button.jsx
   ```

4. **Run compliance scan** — catch PII before it leaks
   ```bash
   migrate compliance scan ./project --pii --secrets
   ```

### During Migration

1. **Use migration waves** — don't big-bang
   ```bash
   migrate run ./project --type react-hooks --waves --auto-rollback
   ```

2. **Monitor progress** — watch for failures in real-time
   ```bash
   migrate status --watch
   ```

### After Migration

1. **Run your test suite** — verify nothing broke
   ```bash
   pytest    # or npm test, depending on your project
   ```

2. **Verify the migration** — automated post-migration checks
   ```bash
   migrate verify ./project --type react-hooks
   ```

3. **Clean up old checkpoints** — reclaim disk space
   ```bash
   migrate cleanup --keep-checkpoints 5
   ```

### Security Best Practices

- Run compliance scans regularly, not just during migrations
- Monitor audit logs for suspicious activity
- Keep dependencies up to date
- See the full [Security Policy](../security/SECURITY.md) for detailed controls

---

## Related Documentation

| Document | Description |
|----------|-------------|
| [README](../../README.md) | Project overview and quick reference |
| [Installation Guide](installation.md) | Platform-specific setup instructions |
| [Security Policy](../security/SECURITY.md) | Security architecture, threat model, compliance |
| [Contributing Guide](../../CONTRIBUTING.md) | Development setup, coding standards, PR process |

---

**Need Help?**

- **Issues**: [github.com/anudeepsrib/code-migration-assistant/issues](https://github.com/anudeepsrib/code-migration-assistant/issues)
- **Discussions**: [github.com/anudeepsrib/code-migration-assistant/discussions](https://github.com/anudeepsrib/code-migration-assistant/discussions)
