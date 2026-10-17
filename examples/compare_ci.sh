#!/usr/bin/env bash
set -euo pipefail

# Capture current CI environment snapshot
venv-match capture --output ci-current.json --env TZ --env LANG --overwrite

# Compare against committed baseline, ignoring working directory and interpreter paths
venv-match compare baseline.json ci-current.json \
  --min-severity medium \
  --ignore sections.runtime.working_directory \
  --ignore sections.python.executable \
  --ignore sections.python.prefix
