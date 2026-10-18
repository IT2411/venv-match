# Venv Match

**Capture an environment. Compare it with another. Recreate what you need.**

Venv Match (`venv-match`) is a zero-dependency Python environment comparison, diagnostic, and recreation library designed to help developers investigate why the same Python application behaves differently across machines, virtual environments, or CI executions.

## Features

- **Structured Snapshots:** Captures Python runtime details, installed distributions (PEP 503 normalized), OS/platform info, runtime context, and allowlisted environment variables into portable, versioned JSON files.
- **Deterministic Comparison:** Identifies `added`, `removed`, `changed`, and `unknown` (uncollected) fields without false removals.
- **Environment Recreation & Export:** Recreate a virtual environment directly from a snapshot (`venv-match create`) or export pinned `requirements.txt` files (`venv-match export`).
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

Export pinned `requirements.txt` from a snapshot:

~~~~bash
venv-match export baseline.json --output requirements.txt
~~~~

Recreate a virtual environment from a snapshot:

~~~~bash
venv-match create baseline.json --target .venv-recreated
~~~~

Preview recreation without modifying disk:

~~~~bash
venv-match create baseline.json --target .venv-recreated --dry-run
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
from venv_match import (
    capture,
    compare,
    create_venv,
    export_requirements,
    load_snapshot,
)

baseline = capture()
baseline.save("baseline.json", overwrite=True)

loaded = load_snapshot("baseline.json")
current = capture()

report = compare(loaded, current)
print(report.has_differences)
print(report.summary())

# Export requirements list
reqs = export_requirements(loaded)

# Dry-run creating a virtual environment from the snapshot
result = create_venv(loaded, ".venv-recreated", dry_run=True)
print(result.installed_packages)
~~~~

## Exit Codes

| Exit Code | Meaning |
|---|---|
| `0` | Command succeeded and no configured failure condition was met. |
| `1` | Comparison completed and met the configured `--fail-on-diff` or `--min-severity` policy. |
| `2` | Invalid command-line arguments or usage. |
| `3` | Snapshot could not be loaded or parsed. |
| `4` | Required collection, venv creation, or filesystem operation failed (including overwrite protection). |
| `5` | Unsupported schema version or incompatible snapshots. |

## License

MIT
