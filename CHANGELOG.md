# Changelog

All notable changes to this project will be documented in this file.

## [0.2.1] - 2026-04-06

### Changed

- Atomic file writes (`write_text_atomically`) with automatic parent directory creation for `Snapshot.save()` and `venv-match export --output`.
- Added 10 MiB snapshot input size guard (`MAX_SNAPSHOT_BYTES`) for safe untrusted file loading.
- Added strict validation for `--ignore` paths against known snapshot sections.
- Added subprocess timeouts and automatic partial-directory cleanup when `create_venv()` fails mid-installation.
- Deterministic sorting when resolving duplicate `.dist-info` distributions in `collect_packages_metadata()`.
- Expanded CI matrix to Linux, macOS, and Windows, and added automated `.github/workflows/release.yml` for GitHub Releases and PyPI Trusted Publishing.

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
