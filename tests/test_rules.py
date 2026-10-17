"""Unit tests for Phase 6 diagnostic rules and report formatting."""

import json
from pathlib import Path

from venv_match import compare, load_snapshot
from venv_match.reporting import (
    format_comparison_json,
    format_comparison_text,
    format_inspection_text,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_all_expected_rules_triggered_for_fixture_comparison() -> None:
    baseline = load_snapshot(FIXTURES_DIR / "baseline.json")
    changed = load_snapshot(FIXTURES_DIR / "changed.json")

    report = compare(baseline, changed)
    rule_ids = {diag.rule_id for diag in report.diagnostics}

    expected_rules = {
        "PYTHON_VERSION_CHANGED",
        "PACKAGE_MISSING",
        "PACKAGE_VERSION_CHANGED",
        "TIMEZONE_CHANGED",
        "LOCALE_CHANGED",
        "ENVIRONMENT_VARIABLE_CHANGED",
        "WORKING_DIRECTORY_CHANGED",
        "INTERPRETER_PATH_CHANGED",
    }
    assert expected_rules.issubset(rule_ids)

    # Diagnostics must be sorted by severity descending (high before medium before low)
    severities = [diag.severity for diag in report.diagnostics]
    rank = {"critical": 4, "high": 3, "medium": 2, "low": 1}
    ranks = [rank[s] for s in severities]
    assert ranks == sorted(ranks, reverse=True)


def test_neutral_diagnostic_language() -> None:
    baseline = load_snapshot(FIXTURES_DIR / "baseline.json")
    changed = load_snapshot(FIXTURES_DIR / "changed.json")
    report = compare(baseline, changed)

    text = format_comparison_text(report)
    assert "caused the failure" not in text.lower()
    assert "Diagnostics (Prioritized for Investigation):" in text
    assert "Observed Differences:" in text


def test_json_report_is_valid_and_deterministic() -> None:
    baseline = load_snapshot(FIXTURES_DIR / "baseline.json")
    changed = load_snapshot(FIXTURES_DIR / "changed.json")
    report = compare(baseline, changed)

    json_1 = format_comparison_json(report)
    json_2 = format_comparison_json(report)
    assert json_1 == json_2

    parsed = json.loads(json_1)
    assert parsed["has_differences"] is True
    assert parsed["counts"]["differences"] > 0
    assert isinstance(parsed["differences"], list)
    assert isinstance(parsed["diagnostics"], list)


def test_inspection_text_formatting() -> None:
    baseline = load_snapshot(FIXTURES_DIR / "baseline.json")
    text = format_inspection_text(baseline)
    assert "Venv Match Snapshot Inspection" in text
    assert "CPython" in text
    assert "3.12.5" in text
    assert "numpy==1.26.4" in text
    assert 'TZ: present (value="UTC")' in text
