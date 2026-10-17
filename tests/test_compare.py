"""Unit tests for Phase 5 snapshot comparison engine."""

import copy
from pathlib import Path

import pytest

from venv_match import ComparisonError, Snapshot, compare, load_snapshot

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_identical_snapshots_ignoring_timestamps_and_tool_version() -> None:
    baseline = load_snapshot(FIXTURES_DIR / "baseline.json")
    modified_dict = baseline.to_dict()
    modified_dict["captured_at"] = "2026-12-31T23:59:59Z"
    modified_dict["venv_match_version"] = "0.9.9"
    current = Snapshot.from_dict(modified_dict)

    report = compare(baseline, current)
    assert not report.has_differences
    assert not report.has_unknowns
    assert report.differences == ()
    assert report.diagnostics == ()
    assert "No differences detected" in report.summary()


def test_compare_baseline_and_changed_fixtures() -> None:
    baseline = load_snapshot(FIXTURES_DIR / "baseline.json")
    changed = load_snapshot(FIXTURES_DIR / "changed.json")

    report = compare(baseline, changed)
    assert report.has_differences

    by_path = {d.path: d for d in report.differences}

    # Python version changed
    assert by_path["sections.python.version"].change_type == "changed"
    assert by_path["sections.python.version"].severity == "high"
    assert "PYTHON_VERSION_CHANGED" in by_path["sections.python.version"].rule_ids

    # Packages added, removed, changed
    assert by_path["sections.packages.requests"].change_type == "removed"
    assert by_path["sections.packages.requests"].severity == "high"
    assert "PACKAGE_MISSING" in by_path["sections.packages.requests"].rule_ids

    assert by_path["sections.packages.numpy"].change_type == "changed"
    assert by_path["sections.packages.numpy"].baseline == "1.26.4"
    assert by_path["sections.packages.numpy"].current == "2.1.1"
    assert by_path["sections.packages.numpy"].severity == "medium"

    assert by_path["sections.packages.pydantic"].change_type == "added"
    assert by_path["sections.packages.pydantic"].severity == "low"

    # Runtime differences
    assert by_path["sections.runtime.timezone"].change_type == "changed"
    assert by_path["sections.runtime.locale"].change_type == "changed"
    assert by_path["sections.runtime.working_directory"].change_type == "changed"

    # Environment variable differences
    assert by_path["sections.environment.LANG"].change_type == "changed"
    assert by_path["sections.environment.TZ"].change_type == "removed"


def test_missing_section_reported_as_unknown_not_false_removals() -> None:
    baseline = load_snapshot(FIXTURES_DIR / "baseline.json")
    curr_dict = baseline.to_dict()
    del curr_dict["sections"]["packages"]
    curr_dict["collection"]["completed_sections"] = [
        s for s in curr_dict["collection"]["completed_sections"] if s != "packages"
    ]
    current = Snapshot.from_dict(curr_dict)

    report = compare(baseline, current)
    assert not report.has_differences
    assert report.has_unknowns
    assert len(report.differences) == 1

    diff = report.differences[0]
    assert diff.path == "sections.packages"
    assert diff.change_type == "unknown"
    assert diff.baseline == "collected"
    assert diff.current == "uncollected"


def test_ignore_paths_excludes_fields_and_records_in_report() -> None:
    baseline = load_snapshot(FIXTURES_DIR / "baseline.json")
    changed = load_snapshot(FIXTURES_DIR / "changed.json")

    report = compare(
        baseline,
        changed,
        ignore_paths=[
            "sections.packages.NumPy",
            "sections.runtime.working_directory",
            "sections.python",
        ],
    )
    paths = {d.path for d in report.differences}
    assert "sections.packages.numpy" not in paths
    assert "sections.runtime.working_directory" not in paths
    assert not any(p.startswith("sections.python.") for p in paths)
    assert report.ignored_paths == (
        "sections.packages.numpy",
        "sections.python",
        "sections.runtime.working_directory",
    )


def test_failure_threshold_evaluation() -> None:
    baseline = load_snapshot(FIXTURES_DIR / "baseline.json")
    low_only_dict = copy.deepcopy(baseline.to_dict())
    low_only_dict["sections"]["runtime"]["working_directory"] = "/other/dir"
    current = Snapshot.from_dict(low_only_dict)

    report = compare(baseline, current)
    assert report.has_differences
    assert not report.meets_failure_threshold(fail_on_diff=False, min_severity=None)
    assert report.meets_failure_threshold(fail_on_diff=True)
    assert report.meets_failure_threshold(min_severity="low")
    assert not report.meets_failure_threshold(min_severity="medium")
    assert not report.meets_failure_threshold(min_severity="high")
    assert not report.meets_failure_threshold(min_severity="critical")

    with pytest.raises(ComparisonError, match="Invalid minimum severity"):
        report.meets_failure_threshold(min_severity="invalid")
