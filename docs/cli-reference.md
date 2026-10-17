# CLI Reference (`venv-match`)

## Synopsis

```bash
venv-match [--version] [--help] <command> [options]
```

## Commands

### `venv-match capture`

Captures the current Python runtime environment and writes a validated JSON snapshot.

```bash
venv-match capture --output baseline.json [options]
```

**Options:**
- `--output PATH`, `-o PATH` (required): Output snapshot JSON file path.
- `--include-packages` / `--no-packages`: Enable or disable package collection (enabled by default).
- `--env NAME`: Allowlist an environment variable name for collection (repeatable).
- `--env-values`: Opt in to recording values for allowlisted non-secret environment variables. Emits a privacy warning to `stderr`.
- `--overwrite`: Permit overwriting an existing output file.

### `venv-match compare`

Compares two snapshot files and prints a human-readable or JSON report.

```bash
venv-match compare baseline.json current.json [options]
```

**Options:**
- `--format text|json`: Output format (`text` by default).
- `--fail-on-diff`: Exit with code `1` if any non-ignored difference is found.
- `--min-severity low|medium|high|critical`: Exit with code `1` if any non-ignored difference meets or exceeds the specified severity.
- `--ignore PATH`: Exclude an exact field path (e.g., `sections.runtime.working_directory` or `sections.packages.numpy`) from comparison (repeatable).

### `venv-match inspect`

Displays snapshot metadata, completed sections, and a formatted environment summary.

```bash
venv-match inspect baseline.json
```

## Exit Codes

| Exit Code | Meaning |
|---|---|
| `0` | Command succeeded and no configured failure condition was met. |
| `1` | Comparison completed and met the configured `--fail-on-diff` or `--min-severity` threshold. |
| `2` | Invalid command-line arguments or usage. |
| `3` | Snapshot file could not be loaded, parsed, or validated. |
| `4` | Required environment collection or filesystem write operation failed (including overwrite protection). |
| `5` | Unsupported snapshot `schema_version`. |