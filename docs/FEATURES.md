# Table of Features — ShiftIQ

This document tabulates the features that are fully implemented and present in the codebase. It separates core execution functionality, enterprise security features, developer capabilities, and integrations.

## 🛠️ Core Capabilities

| Feature Name | Description | Source Module |
|---|---|---|
| **Plugin Architecture** | Decentralized, dynamically loadable migrators via Python `entry_points`. | `src/code_migration/registry.py` |
| **React Hooks Migrator** | Transforms legacy class-based React components to modern functional components with hooks. | `src/code_migration/migrators/react_hooks.py` |
| **Confidence Scoring** | Pre-migration AI and static analysis to score risk based on complexity, dependencies, test coverage, and breaking changes. | `src/code_migration/core/confidence/scorer.py` |
| **Cost Estimator** | Calculates the time and financial budget required for a migration based on team experience, LOC, and code complexity. | `src/code_migration/core/cost_estimator/` |
| **AST Parsing** | Advanced static analysis engine traversing Abstract Syntax Trees without executing risky application code. | `src/code_migration/core/ast_parser.py` |

## 🛡️ Enterprise Security & Compliance

| Feature Name | Description | Source Module |
|---|---|---|
| **Code Sandbox** | Restricts all file IO to safe boundaries using strict path sanitization. Enforces file size limits and extension blocks. | `src/code_migration/core/security/code_sandbox.py` |
| **PII & PHI Detector** | Pattern-matches user code against GDPR (Personally Identifiable Information) and HIPAA (Protected Health Information) signatures. | `src/code_migration/core/compliance/pii_detector.py` |
| **Data Anonymizer** | Automatically tokenizes sensitive data in scanned codebases to prevent exfiltration. | `src/code_migration/core/compliance/anonymizer.py` |
| **Audit Logging** | Tamper-evident, dual-layer JSON logging (via `structlog` and standalone `security_audit.jsonl`) for compliance traceability. | `src/code_migration/core/security/audit_logger.py` |
| **Compliance Reporter** | Parsers for generating SOC2, HIPAA, and GDPR readiness reports based on logged codebase interactions. | `src/code_migration/core/compliance/audit_reporter.py` |
| **Input Validation** | Defends against malicious user payloads with strict sanitizers and rate-limiters. | `src/code_migration/core/security/input_validator.py` |

## 🤖 Advanced Code Manipulations

| Feature Name | Description | Source Module |
|---|---|---|
| **Live Migration & Canary Deployments** | Framework for running progressive, health-checked deployments that can automatically roll back upon failure. | `src/code_migration/core/live_migration/` |
| **Rollback & Snapshot Management** | Manages system checkpoints and provides partial AST reversion mechanisms. | `src/code_migration/core/rollback/` |
| **Test Generation** | Creates unit test stubs, mocks (`pytest`), and analyzes existing test coverage. | `src/code_migration/core/test_generation/` |
| **Visualizer** | Converts architectural dependencies and AST representations into visual Mermaid diagrams. | `src/code_migration/core/visualizer/` |

## 🌐 AI & Integrations

| Feature Name | Description | Source Module |
|---|---|---|
| **Copilot & RAG Engine** | Integrated Retrieval-Augmented Generation (RAG) knowledge base to converse with the codebase context. | `src/code_migration/core/copilot/` |
| **Plugin Marketplace** | Subsystem for finding, installing, and managing 3rd-party community migrator plugins. | `src/code_migration/core/marketplace/` |
| **MCP Server Binding** | Model Context Protocol integration, exposing migrators, analyzers, and scanners as AI Agent tools to external hosts (like Claude). | `src/code_migration/mcp_server.py` |

## 🚀 Deployment & Operations

| Feature Name | Description | Source Module |
|---|---|---|
| **FastAPI REST Server** | Modular Application Programming Interface equipped with `v1` routers, API key interception, streaming SSE, and OpenAPI typing. | `src/code_migration/api/` |
| **Unified Configuration Engine** | Pydantic `BaseSettings` cascading inheritance from `config.defaults.yaml`, overridable by environment variables. | `src/code_migration/config.py` |
| **Docker Containerization** | Multi-stage Dockerfile packing the Python backend and React Vite UI into a highly constrained, prod-ready bundle. | `Dockerfile`, `docker-compose.yml` |
| **OpenTelemetry Integration** | Traces critical execution paths to remote OTLP collectors. | `src/code_migration/telemetry.py` |
| **CI/CD Validation** | Matrix automated testing covering security pipelines (`bandit`, `pip-audit`), semantic releases, and Python cross-platform verification. | `.github/workflows/` |
| **React Hooks UI** | React DOM application designed to track migration visual states directly in the browser via backend hooks. | `ui/` |
