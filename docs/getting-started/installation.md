# Installation Guide

> Step-by-step setup for the **Code Migration Assistant** on all major platforms.
>
> After installation, see the [User Guide](user-guide.md) for usage instructions and the [Security Policy](../security/SECURITY.md) for security configuration.

---

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Quick Install (Recommended)](#quick-install-recommended)
3. [Platform-Specific Instructions](#platform-specific-instructions)
4. [Development Setup](#development-setup)
5. [Configuration](#configuration)
6. [Verifying Your Installation](#verifying-your-installation)
7. [Troubleshooting](#troubleshooting)

---

## System Requirements

### Minimum Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| Python | 3.8 | 3.11+ |
| RAM | 4 GB | 8 GB+ |
| Storage | 500 MB | 2 GB+ |
| Git | 2.x+ | Latest stable |

### Supported Platforms

| Platform | Support Level | Notes |
|----------|---------------|-------|
| **Linux** (Ubuntu 18.04+, Debian 10+, CentOS 7+) | ✅ Full | Primary CI/CD target |
| **macOS** 10.15+ (Catalina) | ✅ Full | Intel and Apple Silicon |
| **Windows** 10+ | ✅ Full | Native or WSL2 |

### Python Version Compatibility

| Version | Status |
|---------|--------|
| 3.8 | ✅ Supported (minimum) |
| 3.9 | ✅ Supported |
| 3.10 | ✅ Supported |
| 3.11 | ✅ Supported |
| 3.12 | ✅ Supported |
| 3.13 | 🧪 Experimental |

---

## Quick Install (Recommended)

This is the fastest way to get up and running from source:

```bash
# 1. Clone the repository
git clone https://github.com/anudeepsrib/code-migration-assistant.git
cd code-migration-assistant

# 2. (Recommended) Create a virtual environment
python -m venv .venv
# Linux/macOS:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate

# 3. Install runtime dependencies
pip install -r requirements.txt

# 4. Install the package in editable mode
pip install -e .

# 5. Verify
python -m code_migration --version
```

### What Gets Installed

| Package | Purpose |
|---------|---------|
| `typer[all]` | CLI framework with autocompletion |
| `rich` | Terminal formatting and progress bars |
| `pyyaml` | YAML configuration parsing |
| `python-dotenv` | `.env` file support |
| `networkx` | Dependency graph construction |
| `psutil` | System resource monitoring |

---

## Platform-Specific Instructions

### Linux (Ubuntu / Debian)

```bash
# Install Python if not already present
sudo apt update
sudo apt install python3 python3-pip python3-venv git

# Clone and install
git clone https://github.com/anudeepsrib/code-migration-assistant.git
cd code-migration-assistant
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

### macOS

```bash
# Install Python via Homebrew (if needed)
brew install python git

# Clone and install
git clone https://github.com/anudeepsrib/code-migration-assistant.git
cd code-migration-assistant
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

### Windows

```powershell
# Install Python from https://python.org (check "Add to PATH")
# Install Git from https://git-scm.com

# Clone and install
git clone https://github.com/anudeepsrib/code-migration-assistant.git
cd code-migration-assistant
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pip install -e .
```

> [!TIP]
> On Windows, if `migrate` is not found after installation, use `python -m code_migration` as an alternative.

---

## Development Setup

If you plan to contribute or run the test suite, install with development dependencies:

```bash
# Clone and create environment (same as Quick Install)
git clone https://github.com/anudeepsrib/code-migration-assistant.git
cd code-migration-assistant
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install with dev extras
pip install -e ".[dev]"
```

This installs additional tools:

| Package | Purpose |
|---------|---------|
| `pytest` | Test runner |
| `pytest-cov` | Coverage reporting |
| `pytest-timeout` | Per-test timeout enforcement |
| `black` | Code formatter |
| `isort` | Import sorter |
| `bandit` | Security linter |
| `pre-commit` | Git hook manager |

### Running Tests After Installation

```bash
# Run the full test suite
pytest tests/ -v

# Run only fast tests (skip performance/stress)
pytest -m "not slow"

# Run with coverage
pytest tests/ --cov=src/code_migration --cov-report=term-missing
```

> [!NOTE]
> Performance tests generate large temporary projects and can take several minutes. See the [Testing section in the README](../../README.md#testing) for full details including timeout configuration.

### Pre-commit Hooks

```bash
# Install hooks (runs Black, isort, Bandit on every commit)
pre-commit install

# Run manually against all files
pre-commit run --all-files
```

---

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# Security
MIGRATION_SECURITY_LEVEL="high"      # high | medium | low
MIGRATION_AUDIT_LOGGING="true"       # Enable audit trail

# Performance
MIGRATION_MAX_WORKERS="4"            # Concurrent analysis workers
MIGRATION_TIMEOUT="300"              # Per-operation timeout (seconds)

# Logging
MIGRATION_LOG_LEVEL="INFO"           # DEBUG | INFO | WARNING | ERROR
```

### Configuration Files

After installation, you can create optional YAML configuration files. See the [User Guide — Configuration](user-guide.md#configuration) for full details on:

- `config/security_policy.yaml` — input validation, path sanitization, rate limiting
- `config/compliance_rules.yaml` — GDPR, HIPAA, SOC2 settings
- `config/migration_rules.yaml` — per-migration-type behavior

---

## Verifying Your Installation

Run these checks after installation to confirm everything is working:

### 1. Version Check

```bash
python -m code_migration --version
```

Expected output: version number (e.g., `0.1.0`).

### 2. CLI Help

```bash
migrate --help
```

Expected output: list of available commands.

### 3. Quick Smoke Test

```bash
# Run a fast subset of tests
pytest tests/security/ -v --timeout=60
```

Expected output: all tests passing.

### 4. Security Controls Verification

```bash
# Verify input validation catches injection
# Verify path sanitization blocks traversal
pytest tests/security/test_input_validation.py -v
pytest tests/security/test_path_sanitizer.py -v
```

---

## Troubleshooting

### Python Version Incompatible

**Symptom:** `ERROR: Package requires a different Python`

```bash
# Check your version
python --version

# Install a compatible version
# Ubuntu/Debian:
sudo apt install python3.11
# macOS:
brew install python@3.11

# Create a venv with the right version
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

### Permission Denied

**Symptom:** Permission errors during `pip install`

```bash
# Use a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Or install to user site-packages
pip install --user -r requirements.txt
```

### Dependency Conflicts

**Symptom:** Package version conflicts

```bash
# Create a clean virtual environment
python -m venv clean-env
source clean-env/bin/activate

# Install fresh
pip install -r requirements.txt
pip install -e .
```

### `migrate` Command Not Found

**Symptom:** Command not recognized after installation

```bash
# Use Python module invocation instead
python -m code_migration --version

# Or ensure the venv Scripts directory is on PATH
# Windows:
echo $env:PATH
# Linux/macOS:
echo $PATH
```

### Tests Timing Out

**Symptom:** Performance tests exceed the 300s default timeout

```bash
# Increase timeout for slower machines
pytest tests/ --timeout=600

# Or skip slow tests entirely
pytest -m "not slow"
```

---

## Related Documentation

| Document | Description |
|----------|-------------|
| [README](../../README.md) | Project overview, architecture, and quick reference |
| [User Guide](user-guide.md) | Complete usage documentation with examples |
| [Security Policy](../security/SECURITY.md) | Security architecture, threat model, compliance |
| [Contributing Guide](../../CONTRIBUTING.md) | Development workflow, coding standards, PR process |
