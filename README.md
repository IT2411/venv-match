# Venv Match

**Capture an environment. Compare it with another. Understand what changed.**

Venv Match (`venv-match`) is a zero-dependency Python environment comparison and diagnostic library designed to help developers investigate why the same Python application behaves differently across machines, virtual environments, or CI executions.

## Features

- **Structured Snapshots:** Captures Python runtime details, installed distributions (PEP 503 normalized), OS/platform info, runtime context, and allowlisted environment variables into portable, versioned JSON files.
- **Deterministic Comparison:** Identifies `added`, `removed`, `changed`, and `unknown` (uncollected) fields without false removals.
- **Transparent Diagnostics:** Prioritizes differences (`critical`, `high`, `medium`, `low`) with neutral, actionable explanations.
- **Privacy by Default:** Never collects arbitrary environment variables, hostnames, or usernames by default; excludes and redacts secret-like variable names (`TOKEN`, `SECRET`, `PASSWORD`, `API_KEY`, etc.).
- **CI-Ready CLI & Python API:** Supports human-readable terminal output, machine-readable JSON reports, `--ignore` paths, `--min-severity` thresholds, and stable exit codes.

## Installation

~~~~bash
pip install venv-match
~~~~

Supported Python versions: **3.10, 3.11, 3.12**.

## Quickstart (CLI)

Capture a baseline snapshot:

~~~~bash
venv-match capture --output baseline.json --env TZ --env LANG
~~~~

Inspect a snapshot:

~~~~bash
venv-match inspect baseline.json
~~~~

Compare two snapshots:

~~~~bash
venv-match compare baseline.json current.json
~~~~

Use in CI with severity thresholds and ignored paths:

~~~~bash
venv-match compare baseline.json current.json \
  --format json \
  --min-severity medium \
  --ignore sections.runtime.working_directory
~~~~

## Quickstart (Python API)

~~~~python
from venv_match import capture, compare, load_snapshot

baseline = capture()
baseline.save("baseline.json", overwrite=True)

current = capture()
loaded = load_snapshot("baseline.json")

report = compare(loaded, current)
print(report.has_differences)
print(report.summary())

for diff in report.differences:
    print(diff.path, diff.change_type, diff.severity)
~~~~

## Exit Codes

| Exit Code | Meaning |
|---|---|
| `0` | Command succeeded and no configured failure condition was met. |
| `1` | Comparison completed and met the configured `--fail-on-diff` or `--min-severity` policy. |
| `2` | Invalid command-line arguments or usage. |
| `3` | Snapshot could not be loaded or parsed. |
| `4` | Required collection or filesystem operation failed (including overwrite protection). |
| `5` | Unsupported schema version or incompatible snapshots. |

## Limitations

- Venv Match is a diagnostic comparison tool, not an environment manager; it never installs packages or modifies virtual environments.
- Observed differences indicate areas worth investigating, not definitive proof of what caused an application failure.
- Installed distribution versions (`importlib.metadata`) do not fingerprint editable installs or native C library dependencies.

## License

MIT
