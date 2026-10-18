# Changelog

All notable changes to this project will be documented in this file.

## [0.2.0] - 2026-04-06

### Added

- `venv-match create` CLI command and `create_venv()` Python API to create a virtual environment and install pinned packages from a snapshot JSON file (with `--target`, `--python`, `--include-build-tools`, `--overwrite`, and `--dry-run` options).
- `venv-match export` CLI command and `export_requirements()` Python API to export pinned `requirements.txt` specs from a snapshot.
- Strict package specifier validation to prevent `pip` option injection from untrusted snapshot files.

## [0.1.0] - 2026-04-06

### Added

- Structured environment snapshot collection (`python`, `platform`, `packages`, `runtime`, `environment`).
- Versioned (`1.0`), validated, deterministic UTF-8 JSON snapshot schema.
- `Snapshot`, `CaptureConfig`, `capture()`, and `load_snapshot()` public API.
- Deterministic comparison engine (`compare()`, `ComparisonReport`, `Difference`) with `added`, `removed`, `changed`, and `unknown` change detection.
- Built-in diagnostic rules prioritizing differences across `critical`, `high`, `medium`, and `low` severities.
- Allowlist-based environment variable collection and automatic secret redaction.
- Command-line interface (`venv-match capture`, `venv-match compare`, `venv-match inspect`) with documented CI exit codes (`0`–`5`).
