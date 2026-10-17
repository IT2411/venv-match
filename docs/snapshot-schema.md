# Snapshot Schema Specification (`1.0`)

## Overview

Venv Match snapshots are portable, versioned UTF-8 JSON documents describing a Python runtime environment at a point in time.

## Top-Level Fields

| Field | Type | Required | Description |
|---|---|---|---|
| `schema_version` | `string` | Yes | Format version (`"1.0"`). Validated independently of package version. |
| `venv_match_version` | `string` | Yes | Version of `venv-match` that produced the snapshot. |
| `captured_at` | `string` | Yes | UTC ISO 8601 timestamp (e.g. `"2026-09-28T10:00:00Z"`). Ignored during comparisons. |
| `sections` | `object` | Yes | Collected environment sections. |
| `collection` | `object` | Yes | Collection completion and error metadata. |

## Sections (`sections`)

### `sections.python` (Required)

- `implementation` (`string`): e.g. `"CPython"`, `"PyPy"`.
- `version` (`string`): e.g. `"3.12.5"`.
- `version_info` (`list[int]`): Version components, e.g. `[3, 12, 5]`.
- `executable` (`string`): Path to the Python interpreter executable.
- `prefix` (`string`): `sys.prefix`.
- `base_prefix` (`string`): `sys.base_prefix`.
- `is_venv` (`bool`): `True` if running inside a virtual environment.

### `sections.platform` (Optional)

- `system` (`string | null`): Operating system family.
- `release` (`string | null`): OS release version.
- `machine` (`string | null`): Hardware architecture.

### `sections.packages` (Optional)

Mapping of PEP 503 normalized package distribution names (`string`) to installed version strings (`string`), sorted lexicographically by package name.

### `sections.runtime` (Optional)

- `working_directory` (`string | null`): Current working directory.
- `timezone` (`string | null`): Detected timezone name.
- `locale` (`string | null`): Detected locale identifier.

### `sections.environment` (Optional)

Mapping of explicitly allowlisted environment variable names to objects:

- `present` (`bool`): Whether the variable is set in the environment.
- `value` (`string | null`, optional): Recorded value if value collection was enabled and permitted by privacy policy. Must be `null` or omitted if `present` is `false`.

## Collection Metadata (`collection`)

- `completed_sections` (`list[string]`): Sections that were collected successfully. Must include `"python"`.
- `errors` (`list[object]`): Non-fatal collection errors for optional sections, each with `section` (`string`), `message` (`string`), and optional `error_type` (`string`).

## Missing vs. Empty Data

- If an optional section (`packages`, `platform`, `runtime`, `environment`) was not collected or failed collection, it is omitted from `sections` and omitted from `collection.completed_sections`.
- An omitted section is distinct from an empty section (such as `"packages": {}`).
