# Architecture Overview

Venv Match is organized into six decoupled layers:

1. **Interfaces (`venv_match.__init__`, `venv_match.cli`):** Public Python API and CLI entry point.
2. **Application Services (`venv_match.snapshot`, `venv_match.config`):** Snapshot capture orchestration, configuration (`CaptureConfig`), and UTF-8 JSON file persistence (`Snapshot`, `capture`, `load_snapshot`).
3. **Collectors (`venv_match.collectors`):** Independent collectors for Python runtime metadata, OS/platform metadata, installed packages (`importlib.metadata`), runtime context, and allowlisted environment variables.
4. **Snapshot Schema (`venv_match.schema`):** Versioned (`1.0`), validated, normalized JSON representation.
5. **Comparison and Diagnostics (`venv_match.compare`, `venv_match.rules`):** Deterministic structural comparison (`Difference`, `ComparisonReport`) and transparent diagnostic prioritization (`Diagnostic`).
6. **Reporting (`venv_match.reporting`):** Privacy-redacted human-readable terminal formatting and machine-readable JSON formatting.

## Component Boundaries

- Collectors gather facts only and do not depend on reporting or CLI code.
- The comparison engine operates strictly on validated `Snapshot` objects and does not depend on the CLI.
- Diagnostic rules interpret observed differences deterministically without executing code or collecting data.
