# Venv Match — Project Specification

**Project name:** Venv Match  
**PyPI distribution name:** `venv-match`  
**Python import name:** `venv_match`  
**CLI command:** `venv-match`  
**Initial release:** `0.1.0`  
**Supported Python versions:** 3.10, 3.11, 3.12  
**License:** MIT (proposed)  
**Runtime dependencies:** Python standard library only (target)  
**Status:** Pre-development specification

---

# 1. Project Overview

## 1.1 What is Venv Match?

Venv Match is a Python environment comparison and diagnostic library designed to help developers investigate why the same Python application behaves differently across machines, virtual environments, or executions.

It captures structured snapshots of Python runtime environments, compares two snapshots, identifies differences, and prioritizes those differences using transparent diagnostic rules.

The project provides both a Python API and a command-line interface (CLI).

## 1.2 Problem Statement

A common problem in Python development is that code works in one environment but fails or behaves differently in another.

Examples include:

- An application works locally but fails in CI.
- A teammate encounters an error that cannot be reproduced on another machine.
- A dependency update introduces a regression.
- Two virtual environments contain different package versions.
- A deployment uses a different Python interpreter or implementation.
- Locale, timezone, or environment-variable differences affect application behavior.
- A machine has a different platform or architecture.

Developers often investigate these issues by manually checking Python versions, running `pip freeze`, inspecting environment variables, and comparing configuration output.

This process is repetitive, error-prone, and difficult to standardize.

Venv Match aims to automate the comparison and make the differences easy to understand.

## 1.3 Core Value Proposition

**Capture an environment. Compare it with another. Understand what changed.**

Venv Match should answer:

1. What is different between these two environments?
2. Which packages were added, removed, or changed?
3. Did the Python runtime or platform change?
4. Which differences deserve investigation first?
5. Can the comparison be reproduced and consumed by a CI pipeline?

The tool must distinguish observed differences from possible explanations. A difference may be relevant to a failure, but the tool must not claim that it caused the failure without supporting evidence.

---

# 2. Goals and Non-Goals

## 2.1 Goals for Version 0.1.0

The initial release must provide:

- Structured environment snapshot collection.
- Versioned JSON snapshots.
- Snapshot saving and loading.
- Deterministic environment comparison.
- Detection of added, removed, and changed fields.
- Package-version comparison.
- Transparent diagnostic rules.
- Human-readable terminal reports.
- Machine-readable JSON reports.
- A usable Python API.
- A command-line interface.
- Environment-variable allowlisting and privacy controls.
- Stable exit codes suitable for CI.
- Unit, integration, privacy, and CLI tests.
- Documentation and a reproducible release process.

## 2.2 Non-Goals for Version 0.1.0

Venv Match will not:

- Install, uninstall, upgrade, or downgrade packages.
- Modify virtual environments.
- Automatically fix detected differences.
- Reconstruct or clone another machine's environment.
- Execute commands or code from a snapshot.
- Upload environment data to a remote service.
- Collect arbitrary environment variables by default.
- Inventory running processes.
- Compare application outputs, logs, or stack traces.
- Claim to identify the definitive cause of a failure.
- Guarantee that two environments behave identically just because their snapshots match.
- Replace `pip`, `venv`, `pip-tools`, `uv`, Poetry, or other dependency-management tools.

The initial product is a **diagnostic and comparison tool**, not an environment manager.

---

# 3. Target Users and Use Cases

## 3.1 Target Users

- Python developers.
- Backend engineers.
- DevOps and CI engineers.
- Data engineers.
- Machine learning engineers.
- Teams maintaining Python applications across multiple environments.

## 3.2 Primary Use Cases

### Use Case A: Local versus CI

Capture the local environment and the CI environment. Compare their snapshots to find differences in Python versions, packages, platform information, and selected configuration.

### Use Case B: Developer-to-developer debugging

A developer who can reproduce a problem captures a snapshot and shares the JSON file with another developer.

The recipient compares it against their own environment without needing to share the entire virtual environment.

### Use Case C: Before and after a dependency update

Capture a baseline before upgrading dependencies, then capture another snapshot afterward.

The comparison reveals package additions, removals, and version changes.

### Use Case D: CI environment checks

Compare a current environment against a committed baseline. Configure the command to return a nonzero exit code when differences of a specified severity are detected.

### Use Case E: Reproducibility investigation

Compare environments across machines or executions to identify differences worth investigating when behavior is inconsistent.

---

# 4. Supported Platforms and Compatibility

## 4.1 Python Support

Venv Match 0.1.x officially supports:

- Python 3.10
- Python 3.11
- Python 3.12

Python 3.10 is the minimum supported version.

Python 3.13 and later are outside the initial release's supported range. Support may be added in a future release after compatibility testing.

The package metadata must declare:

```toml
requires-python = ">=3.10,<3.13"
```

All source code must remain compatible with Python 3.10 syntax and APIs.

## 4.2 Platform Support

The initial implementation should avoid operating-system-specific assumptions.

The intended environments are:

- Linux
- Windows
- macOS

CI must cover the supported Python versions. Additional operating-system matrix testing should be introduced before claiming full cross-platform support.

## 4.3 Snapshot Compatibility

The Python version running Venv Match and the Python version recorded in a snapshot are separate concepts.

For example, Venv Match running on Python 3.12 must be able to load and compare a valid snapshot describing Python 3.10.

Snapshot comparison must not require both snapshots to have been created by the same Python version.

The implementation should also distinguish between:

- The Python version used to execute Venv Match.
- The Python version recorded by a captured environment.
- The snapshot schema version.
- The Venv Match package version that created the snapshot.

A snapshot describing a newer or older Python runtime may be inspected and compared if its schema is supported. This does not imply that Venv Match itself supports execution on that Python version.

---

# 5. Functional Requirements

## FR-01: Capture Environment

The library must capture structured information about a Python environment.

## FR-02: Persist Snapshots

Snapshots must be serializable to portable JSON files.

## FR-03: Load and Validate Snapshots

The library must load snapshots, validate their structure, and reject unsupported schema versions with clear errors.

## FR-04: Compare Snapshots

The comparison engine must identify fields that were added, removed, changed, or could not be compared reliably.

## FR-05: Diagnose Differences

Built-in rules must prioritize observed differences and explain why they may deserve investigation.

## FR-06: Provide a CLI

Users must be able to capture, inspect, and compare snapshots from a terminal.

## FR-07: Provide a Python API

Developers must be able to use snapshot collection and comparison directly from Python code.

## FR-08: Protect Privacy

Environment collection and report generation must minimize sensitive data exposure.

## FR-09: Support Automation

The CLI must support machine-readable output, stable exit codes, and configurable failure thresholds.

## FR-10: Work Offline

Core snapshot collection, loading, comparison, and reporting must work locally without a network connection.

---

# 6. Non-Functional Requirements

## 6.1 Determinism

The same pair of snapshots must produce the same differences, diagnostic rules, and JSON report, excluding explicitly nondeterministic metadata such as generation timestamps.

## 6.2 Portability

Snapshot files must be readable JSON, independent of operating system and Python process.

## 6.3 Safety

Snapshots must be treated as untrusted input.

Loading a snapshot must never execute code, deserialize arbitrary Python objects, or invoke commands.

## 6.4 Privacy

Only explicitly approved environment-variable names and values may be collected. Reports must respect collection and redaction policies.

## 6.5 Maintainability

Collection, schema validation, comparison, diagnostic rules, and reporting must be separate components.

## 6.6 Clear Failure Handling

Invalid files, unsupported schemas, and failed collection operations must produce useful, predictable errors.

---

# 7. Architecture

## 7.1 High-Level Architecture

The system consists of six layers:

1. **Interfaces:** Python API and CLI.
2. **Application services:** capture, load, inspect, and compare operations.
3. **Collectors:** Python, packages, platform, runtime, and selected environment variables.
4. **Snapshot schema:** versioned, normalized JSON representation.
5. **Comparison and diagnostics:** difference detection and prioritization rules.
6. **Reporting:** terminal output, JSON output, and exit status.

Conceptual data flow:

```text
Python API / CLI
       |
       v
Application Services
       |
       +------> Environment Collectors
       |                 |
       |                 v
       |          Snapshot Model
       |                 |
       |                 v
       |          JSON Persistence
       |
       +------> Snapshot Loader
                       |
                       v
                Schema Validation
                       |
                       v
                 Comparator
                       |
                       v
                Diagnostic Rules
                       |
                       v
                   Reporting
                       |
                       v
                Text / JSON / Exit
```

## 7.2 Component Boundaries

- Collectors gather facts only.
- The schema defines the snapshot representation.
- Persistence handles JSON serialization and loading.
- The comparator identifies structural differences.
- Diagnostic rules interpret observed differences.
- Reporters format results.
- The CLI connects application services to command-line arguments and process exit codes.

The comparator must not depend on the CLI.

Collectors must not depend on report formatting.

Diagnostic rules must not collect environment data themselves.

This separation will make the library easier to test and extend.

---

# 8. Repository Structure

Use a `src` layout to avoid accidentally importing the source tree instead of the installed package.

```text
venv-match/
├── .github/
│   └── workflows/
│       └── ci.yml
├── docs/
│   ├── architecture.md
│   ├── snapshot-schema.md
│   ├── privacy.md
│   └── cli-reference.md
├── examples/
│   ├── capture_compare.py
│   └── compare_ci.sh
├── src/
│   └── venv_match/
│       ├── __init__.py
│       ├── __main__.py
│       ├── cli.py
│       ├── config.py
│       ├── exceptions.py
│       ├── snapshot.py
│       ├── schema.py
│       ├── compare.py
│       ├── rules.py
│       ├── reporting.py
│       └── collectors/
│           ├── __init__.py
│           ├── python.py
│           ├── packages.py
│           ├── platform.py
│           ├── runtime.py
│           └── environment.py
├── tests/
│   ├── fixtures/
│   │   ├── baseline.json
│   │   └── changed.json
│   ├── test_schema.py
│   ├── test_snapshot.py
│   ├── test_collectors.py
│   ├── test_compare.py
│   ├── test_rules.py
│   ├── test_privacy.py
│   └── test_cli.py
├── .gitignore
├── CHANGELOG.md
├── LICENSE
├── PROJECT_SPEC.md
├── README.md
└── pyproject.toml
```

Additional modules may be introduced when justified, but avoid unnecessary abstractions in the initial release.

---

# 9. Snapshot Schema

## 9.1 Design Principles

Snapshots must be:

- Versioned.
- Validated.
- Portable.
- Human-readable.
- Safe to load.
- Deterministically serialized.
- Independent of Python object serialization.

Use JSON only. Do not use pickle.

## 9.2 Example Snapshot

The following is an illustrative schema, not a claim about a particular machine.

```json
{
  "schema_version": "1.0",
  "venv_match_version": "0.1.0",
  "captured_at": "2026-09-28T10:00:00Z",
  "sections": {
    "python": {
      "implementation": "CPython",
      "version": "3.12.5",
      "version_info": [3, 12, 5],
      "executable": "/project/.venv/bin/python",
      "prefix": "/project/.venv",
      "base_prefix": "/usr",
      "is_venv": true
    },
    "platform": {
      "system": "Linux",
      "release": "6.x",
      "machine": "x86_64"
    },
    "packages": {
      "requests": "2.32.3",
      "numpy": "2.1.1"
    },
    "runtime": {
      "working_directory": "/project",
      "timezone": "UTC",
      "locale": "C.UTF-8"
    },
    "environment": {
      "TZ": {
        "present": true,
        "value": "UTC"
      },
      "LANG": {
        "present": true,
        "value": "C.UTF-8"
      }
    }
  },
  "collection": {
    "completed_sections": [
      "python",
      "platform",
      "packages",
      "runtime",
      "environment"
    ],
    "errors": []
  }
}
```

Values are examples. Optional fields must be documented, and the implementation must define which fields are required.

## 9.3 Schema Rules

1. `schema_version` identifies the snapshot format, not the package release.
2. `venv_match_version` records the version of Venv Match that created the snapshot.
3. `captured_at` uses a UTC ISO 8601 timestamp.
4. The timestamp is metadata and must not create an environment difference by itself.
5. Package names must be normalized before comparison.
6. Package collections must be serialized in deterministic order.
7. Paths may be recorded but must not be treated as proof of a meaningful environment difference.
8. A missing section must not be interpreted as an empty section.
9. Uncollected data, unavailable values, and collection failures must be distinguishable.
10. Unknown fields should be handled according to the documented schema-compatibility policy.
11. Unsupported schema versions must result in a clear error rather than a misleading comparison.

## 9.4 Missing and Unknown Data

The implementation must distinguish:

- A field that was collected and has a value.
- A field that was collected and is explicitly absent.
- A field that was not collected.
- A section that failed to collect.
- A field that does not exist in an older schema.

Do not report every missing field as a removal.

For example, if the baseline contains package information but the current snapshot did not collect packages, the comparison must report that the package comparison is unavailable rather than claiming every package was removed.

## 9.5 Schema Evolution

Version 1.0 is the initial snapshot schema.

The schema must be versioned independently of the Python package.

Incompatible changes require an appropriate schema-version change. Snapshot loading must validate the version before attempting comparison.

Future schema migrations may be added, but they are not required for version 0.1.0.

---

# 10. Environment Collectors

Each collector must be independent, testable, and responsible only for collecting its own category of information.

## 10.1 Python Collector

Use the standard library, primarily `sys` and `sysconfig`.

Collect:

- Python implementation.
- Python version.
- Version components.
- Executable path.
- `sys.prefix`.
- `sys.base_prefix`.
- Whether the interpreter appears to be running inside a virtual environment.

Virtual-environment detection should be based on documented interpreter properties, not on assumptions about directory names.

The collector must not assume that every virtual environment is created by `venv`.

## 10.2 Package Collector

Use `importlib.metadata`.

Collect installed distribution names and versions.

Requirements:

- Normalize distribution names according to Python package-name normalization rules.
- Sort package entries deterministically.
- Handle incomplete or malformed package metadata safely.
- Avoid importing every installed package.
- Record collection failures where appropriate.

Limitations must be documented:

- An installed package is not necessarily imported or used by the application.
- The same package version can contain different code in editable installations.
- Distribution metadata does not reveal every native library dependency.
- Package versions alone do not establish full reproducibility.

The initial implementation will not attempt to fingerprint every installed file or resolve all transitive dependencies.

## 10.3 Platform Collector

Use `platform` and `sysconfig`.

Collect relevant information such as:

- Operating-system family.
- OS release, when available.
- Machine architecture.
- Python implementation details relevant to the platform.

Do not collect hostnames, IP addresses, usernames, or other identifying machine information by default.

Platform values may be unavailable or formatted differently across operating systems. Handle this without failing the entire capture.

## 10.4 Runtime Collector

Collect selected runtime context, such as:

- Current working directory.
- Timezone information, where available.
- Locale information, where available.

The collector must not modify the working directory, locale, or timezone.

Timezone and locale representations can vary between systems. Reports should avoid treating formatting differences as conclusive evidence of behavioral differences.

Absolute path changes should normally have low diagnostic priority.

## 10.5 Environment Variable Collector

Environment variables may contain credentials, tokens, private URLs, and other sensitive data.

Therefore:

- Do not collect arbitrary variables by default.
- Require explicit variable names for collection.
- Do not support wildcard collection in version 0.1.0.
- Support presence-only collection.
- Record values only when explicitly opted in.
- Never print selected values without respecting the configured reporting policy.
- Exclude known secret-like variable names by default, including names containing terms such as `TOKEN`, `SECRET`, `PASSWORD`, `PASSWD`, `API_KEY`, and `PRIVATE_KEY`.
- Do not provide a general secret-collection override in the initial release.
- Redact or omit values in both terminal and JSON reports when policy requires it.

Environment-variable names and their presence can still reveal information. Users must be able to inspect exactly what is included in a snapshot.

---

# 11. Snapshot Persistence

Provide a `Snapshot` model with serialization and deserialization support.

Required operations:

- Serialize to a JSON-compatible structure.
- Save to a file.
- Load from a file.
- Validate the schema.
- Report invalid files with clear errors.

Persistence requirements:

- Use UTF-8 JSON.
- Do not execute or evaluate snapshot content.
- Do not use pickle.
- Provide deterministic key ordering.
- Avoid unnecessarily exposing sensitive information in exception messages.
- Avoid overwriting an existing snapshot from the CLI unless the user explicitly requests it.

The library should make file-writing behavior predictable and document whether writes are atomic.

---

# 12. Comparison Engine

## 12.1 Purpose

The comparison engine compares two validated snapshots and produces a structured report.

It must not depend on the CLI or terminal formatting.

## 12.2 Change Types

Support the following change types:

| Type | Meaning |
|---|---|
| `added` | A field or package exists only in the current snapshot. |
| `removed` | A field or package exists only in the baseline snapshot. |
| `changed` | A field exists in both snapshots but has a different value. |
| `unknown` | The comparison cannot be made reliably because information is missing or incompatible. |

`unknown` is a comparison status, not a claim that the environment changed.

## 12.3 Difference Representation

Each difference should contain:

- Stable field path.
- Category.
- Change type.
- Baseline value, when available.
- Current value, when available.
- Severity.
- Applicable diagnostic rule IDs.
- Human-readable explanation.

Example:

```json
{
  "path": "sections.packages.numpy",
  "category": "packages",
  "change_type": "changed",
  "baseline": "1.26.4",
  "current": "2.1.1",
  "severity": "medium",
  "rule_ids": [
    "PACKAGE_VERSION_CHANGED"
  ],
  "explanation": "The installed NumPy distribution version changed."
}
```

This is an illustrative output format.

## 12.4 Normalization

The comparison engine must:

- Normalize package names.
- Sort unordered collections.
- Ignore capture timestamps.
- Exclude Venv Match's own version from environment-difference results by default.
- Avoid false removals when a section was not collected.
- Handle missing values explicitly.
- Use stable paths and deterministic sorting.
- Avoid lowercasing values unless the field's comparison semantics require it.

## 12.5 Ignore Rules

Support exact field-path exclusions through the CLI.

Ignore rules should be applied consistently and documented. They must not silently change the original snapshots.

The comparison report should make it possible to understand which paths were excluded, particularly in machine-readable output.

---

# 13. Diagnostic Rules

## 13.1 Purpose

Diagnostic rules prioritize observed differences for investigation.

They do not prove that a particular difference caused an application failure.

Severity represents investigation priority, not a probability or statistical confidence score.

## 13.2 Severity Levels

| Severity | Meaning |
|---|---|
| `critical` | A potentially major incompatibility that merits immediate investigation. |
| `high` | A substantial difference that may affect runtime behavior. |
| `medium` | A difference that could matter depending on the application. |
| `low` | A difference that is usually contextual or less directly relevant. |

Severity assignments must be documented and configurable where appropriate.

## 13.3 Initial Rules

| Rule ID | Condition | Default severity |
|---|---|---|
| `PYTHON_VERSION_CHANGED` | Python version differs. | High |
| `PYTHON_IMPLEMENTATION_CHANGED` | Python implementation differs. | High |
| `PACKAGE_MISSING` | A baseline package is missing from the current snapshot. | High |
| `PACKAGE_VERSION_CHANGED` | An installed package version differs. | Medium |
| `PLATFORM_CHANGED` | Relevant platform information differs. | Medium |
| `TIMEZONE_CHANGED` | Collected timezone information differs. | Medium |
| `LOCALE_CHANGED` | Collected locale information differs. | Medium |
| `ENVIRONMENT_VARIABLE_CHANGED` | An approved environment variable differs. | Rule-dependent |
| `WORKING_DIRECTORY_CHANGED` | Working directory differs. | Low |
| `INTERPRETER_PATH_CHANGED` | Interpreter path differs. | Low |

These are initial defaults, not universal claims about the impact of each difference.

Rule implementations must be transparent, deterministic, and independently testable.

No rule may execute arbitrary code from a snapshot.

## 13.4 Diagnostic Output

Each diagnostic should explain:

- Which condition was detected.
- Which fields triggered the rule.
- Why the difference may deserve attention.
- What the user could investigate next, where appropriate.

Use neutral language such as “may be relevant” and “consider investigating.” Do not say “this caused the failure” based solely on an environment difference.

---

# 14. Public Python API

## 14.1 Proposed Usage

```python
from venv_match import capture, compare, load_snapshot

baseline = capture()
baseline.save("baseline.json")

current = capture()
report = compare(baseline, current)

print(report.has_differences)
print(report.summary())

loaded = load_snapshot("baseline.json")
report = compare(loaded, current)

for difference in report.differences:
    print(
        difference.path,
        difference.change_type,
        difference.severity,
    )
```

This is the intended interface. Final signatures must be confirmed during implementation.

## 14.2 Public Types

Keep the public API small.

Proposed public objects:

- `capture`
- `load_snapshot`
- `compare`
- `Snapshot`
- `CaptureConfig`
- `Difference`
- `ComparisonReport`
- `VenvMatchError`
- `SnapshotFormatError`
- `CollectionError`
- `ComparisonError`

Do not expose internal collector classes as stable public APIs in version 0.1.0 unless there is a concrete need.

## 14.3 Capture Configuration

A configuration object should control:

- Whether package information is collected.
- Whether platform information is collected.
- Whether runtime information is collected.
- Which environment-variable names are included.
- Whether explicitly approved values are recorded.
- Collection behavior when optional sections fail.

Use safe defaults.

Optional collector failures may be recorded in the snapshot. Required collection failures must raise a documented exception.

The API must make the distinction explicit rather than silently returning incomplete data.

## 14.4 Comparison Report

`ComparisonReport` should provide:

- Whether differences exist.
- A list of differences.
- A list of diagnostics.
- A concise summary.
- Deterministic JSON-compatible serialization.

It should also expose enough information for CI integrations to determine whether the configured failure threshold has been met.

---

# 15. Command-Line Interface

The executable command is `venv-match`.

## 15.1 Capture

```bash
venv-match capture --output baseline.json
```

Captures the current environment and writes a snapshot.

Options to support:

- `--output PATH`
- `--include-packages` / `--no-packages`
- Repeatable `--env NAME`
- `--env-values`, with an explicit privacy warning
- `--overwrite`, to permit replacing an existing output file

The CLI must not overwrite an existing snapshot by default.

## 15.2 Compare

```bash
venv-match compare baseline.json current.json
```

Compares two snapshots and prints a human-readable report.

Options:

```text
--format text|json
--fail-on-diff
--min-severity low|medium|high|critical
--ignore PATH
```

`--ignore` should be repeatable.

By default, the command reports differences but does not fail merely because differences exist.

If `--fail-on-diff` is provided, any non-ignored difference should trigger the configured failure policy.

When a severity threshold is configured, only differences meeting the documented threshold policy should trigger the severity-based failure condition.

## 15.3 Inspect

```bash
venv-match inspect baseline.json
```

Displays snapshot metadata, collected sections, and a readable environment summary.

Inspection must respect privacy rules and must not automatically expose secret values.

## 15.4 Help

```bash
venv-match --help
venv-match capture --help
venv-match compare --help
venv-match inspect --help
```

The CLI must work on all three supported Python versions.

## 15.5 Exit Codes

Define and test stable exit codes.

| Exit code | Meaning |
|---|---|
| `0` | Command succeeded and no configured failure condition was met. |
| `1` | Comparison completed and met the configured difference/severity failure policy. |
| `2` | Invalid command-line arguments or usage. |
| `3` | Snapshot could not be loaded or parsed. |
| `4` | Required collection or filesystem operation failed. |
| `5` | Unsupported schema version or incompatible snapshots. |

Document the precedence of error conditions and test it.

JSON output must remain valid JSON when `--format json` is selected. Diagnostics and errors must not be mixed into standard output in a way that corrupts the JSON document.

---

# 16. Privacy and Security

Privacy is a core product requirement.

## 16.1 Data Minimization

Collect only the information needed for environment comparison.

Do not collect by default:

- API keys.
- Passwords.
- Authentication tokens.
- Private keys.
- Arbitrary environment-variable values.
- Hostnames or IP addresses.
- Usernames.
- Home-directory contents.
- Running process information.
- Application source code.

## 16.2 Explicit Consent

Environment-variable collection must be allowlist-based.

Recording values must require explicit opt-in. Known secret-like variable names should remain excluded from value collection in version 0.1.0.

## 16.3 Safe Snapshot Loading

Snapshots are untrusted input.

- Parse them as JSON.
- Validate types and required fields.
- Reject unsupported schemas.
- Do not execute content.
- Do not use unsafe object deserialization.
- Handle malformed or excessively large inputs predictably.

## 16.4 Report Redaction

Redaction must apply to:

- Terminal output.
- JSON reports.
- Error messages.
- Summary output.

A value excluded by the privacy policy must not reappear through an alternative reporting path.

## 16.5 Privacy Tests

Tests must confirm that:

- Unapproved environment variables are not collected.
- Secret-like names are handled according to policy.
- Environment values do not leak into reports when excluded.
- Malformed snapshots cannot execute code.
- Snapshot parsing does not reveal sensitive information in error messages.

---

# 17. Error Handling

Use a small exception hierarchy.

Proposed structure:

```text
VenvMatchError
├── SnapshotFormatError
├── CollectionError
└── ComparisonError
```

Specific errors may be added if they improve clarity.

Requirements:

- Error messages should identify the failed operation.
- Invalid input should produce actionable messages.
- Expected collection failures should not expose full tracebacks by default.
- Debug logging, if introduced, must respect privacy requirements.
- CLI errors must map to documented exit codes.
- Library users must be able to catch the documented exception types.

Do not silently convert serious failures into empty snapshots.

---

# 18. Dependencies and Development Tooling

## 18.1 Runtime Dependencies

Target zero third-party runtime dependencies.

Use the Python standard library wherever practical.

Recommended modules include:

- `sys`
- `sysconfig`
- `platform`
- `locale`
- `time`
- `os`
- `json`
- `pathlib`
- `datetime`
- `importlib.metadata`
- `argparse`

## 18.2 Development Dependencies

Use:

- `pytest` for testing.
- `ruff` for linting and formatting.
- `mypy` for static type checking.
- `build` for building distributions.
- `twine` for validating and publishing distributions.

Keep development dependencies separate from runtime dependencies.

## 18.3 Initial `pyproject.toml`

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "venv-match"
version = "0.1.0"
description = "Compare Python runtime environments and investigate environment drift"
readme = "README.md"
requires-python = ">=3.10,<3.13"
license = "MIT"
authors = [
    { name = "Your Name" }
]
dependencies = []

[project.optional-dependencies]
dev = [
    "pytest>=8",
    "ruff",
    "mypy",
    "build",
    "twine",
]

[project.scripts]
venv-match = "venv_match.cli:main"

[tool.hatch.build.targets.wheel]
packages = ["src/venv_match"]

[tool.pytest.ini_options]
testpaths = ["tests"]

[tool.ruff]
line-length = 88
target-version = "py310"

[tool.mypy]
python_version = "3.10"
strict = true
mypy_path = "src"
```

Before publishing, confirm that the distribution name is available and that the project metadata, license, author details, and repository URL are correct.

The CLI entry point must not be considered complete until `venv_match.cli:main` has actually been implemented and tested.

---

# 19. Continuous Integration

Use GitHub Actions to run automated checks.

The initial Python test matrix must include:

- Python 3.10
- Python 3.11
- Python 3.12

A minimal workflow:

```yaml
name: CI

on:
  push:
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest

    strategy:
      fail-fast: false
      matrix:
        python-version: ["3.10", "3.11", "3.12"]

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install project
        run: |
          python -m pip install --upgrade pip
          python -m pip install -e ".[dev]"

      - name: Run tests
        run: pytest -q

      - name: Lint
        if: matrix.python-version == '3.10'
        run: ruff check .

      - name: Check formatting
        if: matrix.python-version == '3.10'
        run: ruff format --check .

      - name: Type check
        if: matrix.python-version == '3.10'
        run: mypy src/
```

This is a starting workflow. Expand the CI matrix to Windows and macOS before claiming those platforms have been fully validated.

---

# 20. Testing Strategy

## 20.1 Unit Tests

Test:

- Schema validation.
- Snapshot normalization.
- Serialization and deserialization.
- Package-name normalization.
- Difference detection.
- Missing-section handling.
- Diagnostic rule selection.
- Severity thresholds.
- Ignore paths.
- Stable output ordering.

## 20.2 Collector Tests

Test:

- Python metadata collection.
- Package metadata collection.
- Platform information collection.
- Runtime information collection.
- Environment-variable allowlisting.
- Optional collector failure behavior.
- Required collector failure behavior.

Avoid tests that rely on the developer's actual machine configuration. Mock unstable system values where appropriate.

## 20.3 Integration Tests

Test the full flow:

1. Capture a snapshot.
2. Save it to JSON.
3. Load it into a new object.
4. Capture or load a second snapshot.
5. Compare both snapshots.
6. Generate terminal and JSON reports.

## 20.4 CLI Tests

Test:

- Help output.
- Valid and invalid arguments.
- Capture command.
- Inspect command.
- Compare command.
- JSON output validity.
- Output-file overwrite protection.
- Ignore paths.
- Severity thresholds.
- Every documented exit code.

## 20.5 Privacy Tests

Test every path by which collected information could reach output.

A secret excluded from collection or reporting must not leak into terminal output, JSON output, summaries, or error messages.

## 20.6 Compatibility Tests

Run the test suite on Python 3.10, 3.11, and 3.12.

Also test snapshot interoperability: snapshots captured on different supported Python versions must be loadable and comparable when their schema versions are supported.

---

# 21. Acceptance Criteria

Version 0.1.0 is ready for release only when all required acceptance criteria pass.

## Core Behavior

- [ ] A snapshot can be captured and saved.
- [ ] A saved snapshot can be loaded and validated.
- [ ] Two snapshots can be compared.
- [ ] Added, removed, and changed packages are detected.
- [ ] Python-version differences are detected.
- [ ] Missing sections are not incorrectly treated as empty.
- [ ] Capture timestamps do not create false environment differences.
- [ ] Results are deterministic.
- [ ] Unsupported schema versions produce clear errors.

## Privacy and Safety

- [ ] Arbitrary environment variables are not collected by default.
- [ ] Environment-variable allowlisting works.
- [ ] Value collection requires explicit opt-in.
- [ ] Excluded values do not leak into reports.
- [ ] Snapshot loading never executes snapshot content.
- [ ] Malformed JSON is handled safely.

## CLI and API

- [ ] The Python API works.
- [ ] `venv-match capture` works.
- [ ] `venv-match inspect` works.
- [ ] `venv-match compare` works.
- [ ] JSON output is valid.
- [ ] Exit codes match the documentation.
- [ ] Output overwrite protection works.

## Compatibility and Release

- [ ] CI passes on Python 3.10.
- [ ] CI passes on Python 3.11.
- [ ] CI passes on Python 3.12.
- [ ] Installation works in a clean virtual environment.
- [ ] The wheel and source distribution build successfully.
- [ ] The README quickstart works as written.
- [ ] TestPyPI installation succeeds.
- [ ] The final PyPI installation and CLI smoke test succeed.

---

# 22. Development Roadmap

Implement the project in phases. Each phase should have a clear completion gate.

## Phase 0 — Validate the Idea and Name

**Estimated effort:** 0.5–1 day

Tasks:

- Search PyPI for existing packages with similar purposes.
- Search GitHub for competing implementations.
- Read competitor documentation and issues.
- Identify problems that existing tools do not address.
- Verify the availability of `venv-match` on PyPI and GitHub.
- Confirm the distribution name and import name.
- Finalize the v0.1.0 scope.

Deliverables:

- Competitor comparison.
- Confirmed naming decision.
- Final requirements.

**Gate:** Do not publish under the name until availability and naming conflicts have been checked.

## Phase 1 — Repository Foundation

**Estimated effort:** 0.5 day

Tasks:

- Create the Git repository.
- Set up the `src` layout.
- Add `pyproject.toml`.
- Add `.gitignore`, `LICENSE`, and `README.md`.
- Create a virtual environment.
- Install development tools.
- Add the initial CI workflow.

Commands:

```bash
mkdir venv-match
cd venv-match

git init

python3.10 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
```

Create the initial files and then run:

```bash
python -m pip install -e ".[dev]"
```

Deliverables:

- Installable local package skeleton.
- Working test runner.
- Initial CI pipeline.

**Gate:** The package installs locally and CI runs successfully.

## Phase 2 — Snapshot Schema and Validation

**Estimated effort:** 1 day

Tasks:

- Define required and optional fields.
- Define schema versioning.
- Implement snapshot validation.
- Implement deterministic JSON serialization.
- Implement unsupported-version handling.
- Create baseline and changed fixture snapshots.
- Test missing fields and malformed input.

Deliverables:

- Schema implementation.
- Snapshot fixtures.
- Schema tests.
- `docs/snapshot-schema.md`.

**Gate:** Snapshots can be validated, serialized, and loaded reliably.

## Phase 3 — Implement Collectors

**Estimated effort:** 1–2 days

Implement in this order:

1. Python collector.
2. Platform collector.
3. Package collector.
4. Runtime collector.
5. Environment-variable collector.

Tasks:

- Keep collectors independent.
- Handle unavailable fields.
- Record optional collection errors.
- Apply privacy rules.
- Normalize collected values.
- Test collectors on supported Python versions.

Deliverables:

- Collector modules.
- Collector tests.
- Documented collection limitations.

**Gate:** Each collector produces validated, predictable output and respects privacy requirements.

## Phase 4 — Snapshot Service

**Estimated effort:** 0.5–1 day

Tasks:

- Implement `CaptureConfig`.
- Implement `capture()`.
- Implement `Snapshot`.
- Implement snapshot saving and loading.
- Add documented exceptions.
- Test file operations.
- Test capture in a clean environment.

Deliverables:

- Working snapshot API.
- Persistence layer.
- Integration tests.

**Gate:** A snapshot can be captured, saved, loaded, and compared without depending on CLI code.

## Phase 5 — Comparison Engine

**Estimated effort:** 1–2 days

Tasks:

- Implement `Difference`.
- Implement `ComparisonReport`.
- Detect added, removed, and changed values.
- Handle unavailable data.
- Normalize package names.
- Exclude timestamps and appropriate metadata.
- Implement deterministic sorting.
- Add ignore-path support.

Deliverables:

- Comparison engine.
- Comparison tests.
- Stable report data model.

**Gate:** Known differences are detected correctly without false removals caused by missing sections.

## Phase 6 — Diagnostic Rules and Reporting

**Estimated effort:** 1 day

Tasks:

- Implement built-in diagnostic rules.
- Define severity levels.
- Associate rules with differences.
- Write neutral explanations.
- Implement summary generation.
- Implement terminal and JSON reporters.
- Add privacy leakage tests.

Deliverables:

- Rule engine.
- Human-readable report.
- Machine-readable report.

**Gate:** Reports are deterministic, useful, and do not overstate what the comparison proves.

## Phase 7 — CLI and Integration

**Estimated effort:** 1 day

Tasks:

- Implement `capture`.
- Implement `inspect`.
- Implement `compare`.
- Add argument validation.
- Add overwrite protection.
- Implement severity thresholds and ignore paths.
- Implement documented exit codes.
- Test the CLI in subprocesses.

Deliverables:

- Functional CLI.
- CLI reference documentation.
- CLI integration tests.

**Gate:** Every documented command, option, and exit code works.

## Phase 8 — Hardening and Compatibility

**Estimated effort:** 1–2 days

Tasks:

- Run the full suite on Python 3.10, 3.11, and 3.12.
- Test malformed and incompatible snapshots.
- Test missing fields and sections.
- Test collection failures.
- Test privacy and redaction.
- Test clean virtual environments.
- Test cross-version snapshot comparison.
- Review performance with representative package inventories.
- Fix issues discovered by CI.

Deliverables:

- Passing compatibility matrix.
- Security and privacy test results.
- Release-candidate build.

**Gate:** All required acceptance criteria pass.

## Phase 9 — Documentation and Release Candidate

**Estimated effort:** 1 day

Tasks:

- Complete the README.
- Document the Python API.
- Document the CLI.
- Document the snapshot schema.
- Document privacy and limitations.
- Add practical examples.
- Add a changelog.
- Build the wheel and source distribution.
- Validate the distribution.
- Install the package in clean environments.

Commands:

```bash
python -m build
python -m twine check dist/*
```

Test installation in a clean environment before publishing.

**Gate:** The packaged distribution installs and all documented quickstart commands work.

## Phase 10 — PyPI Release

**Estimated effort:** 0.5–1 day

Tasks:

- Confirm the project name is available.
- Confirm the license and package metadata.
- Configure PyPI Trusted Publishing where practical, or use an appropriately scoped API token.
- Publish to TestPyPI.
- Install and test the TestPyPI package.
- Publish version `0.1.0` to PyPI.
- Verify the published package.
- Tag the release in Git.
- Publish the changelog and release notes.

Deliverables:

- Public package.
- Tagged release.
- Verified installation instructions.

**Gate:** A new user can install Venv Match and complete the README quickstart in a clean environment.

### Overall Estimate

Approximately **8–12 focused working days**, excluding major scope changes, feedback cycles, and unforeseen compatibility issues.

The phases are estimates, not deadlines. Do not skip a phase gate just to meet the estimate.

---

# 23. Local Development Commands

Once the repository skeleton and `pyproject.toml` exist:

```bash
# Install in editable mode with development dependencies
python -m pip install -e ".[dev]"

# Confirm the import location
python -c "import venv_match; print(venv_match.__file__)"

# Run tests
pytest -q

# Lint
ruff check .

# Check formatting
ruff format --check .

# Type checking
mypy src/

# Build wheel and source distribution
python -m build

# Validate distribution metadata
python -m twine check dist/*
```

Run these checks before merging significant changes and before each release candidate.

---

# 24. PyPI Publishing

Before publishing, verify the package name, metadata, README, license, and supported Python versions.

## TestPyPI

Build the distributions:

```bash
python -m build
python -m twine check dist/*
```

Upload them to TestPyPI:

```bash
python -m twine upload --repository testpypi dist/*
```

Install from TestPyPI in a clean virtual environment and verify imports and CLI commands.

## Production PyPI

After the TestPyPI checks succeed:

```bash
python -m twine upload dist/*
```

Prefer configuring PyPI Trusted Publishing through GitHub Actions to avoid storing a long-lived publishing token.

PyPI releases are effectively immutable. If version `0.1.0` has been published, fixes should be released under a new version such as `0.1.1`.

---

# 25. Post-Release Roadmap

These are possible future directions, not commitments for the initial release.

## 0.1.x — Stabilization

- Bug fixes.
- Compatibility fixes.
- Improved errors.
- Documentation improvements.

## 0.2.x — Custom Diagnostic Rules

- User-defined TOML rules.
- Configurable severity.
- Rule enablement and disablement.
- Additional comparison policies.

Custom rules must remain declarative. Do not introduce arbitrary executable expressions from configuration files.

## 0.3.x — Failure Context

Explore optional integrations that help correlate environment differences with a user-provided failure context.

This must remain evidence-based. The product should distinguish a difference that exists from a difference that is demonstrated to affect the failure.

## 0.4.x and Later — Integrations

Potential integrations include:

- Pytest.
- GitHub Actions.
- Other CI systems.
- Structured build artifacts.
- Additional runtime and native-library metadata.

Integrations should be added only after the core schema and comparison behavior are stable.

---

# 26. Project Principles

All implementation decisions should follow these principles.

1. **Accuracy over assumptions.** Report what was observed, not what is merely suspected.
2. **Privacy by default.** Avoid collecting secrets and identifying machine details.
3. **Deterministic output.** Identical inputs should produce identical comparisons.
4. **Safe input handling.** Snapshots are data, never executable instructions.
5. **Minimal dependencies.** Prefer the standard library for the core package.
6. **Clear separation of concerns.** Collection, comparison, diagnostics, and reporting remain independent.
7. **Cross-version interoperability.** Runtime versions recorded in snapshots are not the same as the versions supported for running the tool.
8. **Useful errors.** Fail clearly instead of silently producing misleading reports.
9. **Honest diagnostics.** Prioritize differences without pretending to prove causality.
10. **Release discipline.** Do not publish until compatibility, privacy, packaging, and documentation requirements are satisfied.

---

# 27. Final Definition of Done for Version 0.1.0

Venv Match 0.1.0 is complete when:

- The package is installable from PyPI.
- Python 3.10, 3.11, and 3.12 are tested in CI.
- Environment snapshots can be captured and persisted.
- Snapshot schema validation and version handling work.
- Snapshots can be loaded and compared across supported runtime versions.
- Package and runtime differences are detected deterministically.
- Diagnostic rules provide clear, appropriately qualified explanations.
- The Python API is usable and documented.
- The CLI provides capture, inspect, and compare operations.
- Privacy and malformed-input tests pass.
- CLI exit codes and JSON output are stable and documented.
- The wheel and source distribution pass validation.
- TestPyPI and clean-install checks succeed.
- The README quickstart works in a fresh environment.
- The release is tagged and documented.

**The immediate next step is Phase 0:** verify the project name and investigate existing tools before implementation. Once that is complete, build the repository foundation and implement the snapshot schema before writing the collectors.

---

# 28. Reference Resources

Use the official Python packaging documentation for packaging decisions:

- Python Packaging User Guide: https://packaging.python.org/en/latest/
- Packaging tutorial: https://packaging.python.org/en/latest/tutorials/packaging-projects/
- `pyproject.toml` specification: https://packaging.python.org/en/latest/specifications/pyproject-toml/
- PyPI Trusted Publishing: https://docs.pypi.org/trusted-publishers/
- PyPI TestPyPI guidance: https://packaging.python.org/en/latest/guides/using-testpypi/

These resources should be consulted during the packaging and release phases.