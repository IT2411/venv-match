"""Phase 8 hardening, cross-version interoperability, and edge-case tests."""

import copy
import time
from pathlib import Path

import pytest

from venv_match import (
    ComparisonError,
    Snapshot,
    SnapshotFormatError,
    compare,
    load_snapshot,
)
from venv_match.schema import deserialize_snapshot_json

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_cross_version_and_implementation_snapshot_interoperability() -> None:
    """Snapshots describing Python 3.10, 3.12, or PyPy must load and compare cleanly."""
    base_dict = load_snapshot(FIXTURES_DIR / "baseline.json").to_dict()
    py310_dict = copy.deepcopy(base_dict)
    py310_dict["sections"]["python"] = {
        "implementation": "PyPy",
        "version": "3.10.14",
        "version_info": [3, 10, 14],
        "executable": "/opt/pypy3.10/bin/pypy3",
        "prefix": "/opt/pypy3.10",
        "base_prefix": "/opt/pypy3.10",
        "is_venv": False,
    }

    snap_312 = Snapshot.from_dict(base_dict)
    snap_310_pypy = Snapshot.from_dict(py310_dict)

    report = compare(snap_312, snap_310_pypy)
    assert report.has_differences
    rule_ids = {d.rule_id for d in report.diagnostics}
    assert "PYTHON_VERSION_CHANGED" in rule_ids
    assert "PYTHON_IMPLEMENTATION_CHANGED" in rule_ids
    assert "INTERPRETER_PATH_CHANGED" in rule_ids


@pytest.mark.parametrize(
    "malformed_payload",
    [
        "[]",
        '"just a string"',
        "12345",
        "null",
        '{"schema_version": 1.0}',
        '{"schema_version": "1.0", "venv_match_version": ""}',
    ],
)
def test_malformed_json_payloads_rejected_predictably(
    malformed_payload: str,
) -> None:
    with pytest.raises(SnapshotFormatError):
        deserialize_snapshot_json(malformed_payload)


def test_boolean_in_version_info_rejected() -> None:
    """In Python bool is a subclass of int; schema validation must reject booleans in version_info."""
    base_dict = load_snapshot(FIXTURES_DIR / "baseline.json").to_dict()
    base_dict["sections"]["python"]["version_info"] = [3, True, 5]
    with pytest.raises(SnapshotFormatError, match="version_info"):
        Snapshot.from_dict(base_dict)


def test_parse_error_does_not_leak_sensitive_payload_values() -> None:
    secret_token = "super_secret_token_value_do_not_echo_in_error"
    bad_json = f'{{"SECRET": "{secret_token}", invalid_json_syntax}}'
    with pytest.raises(SnapshotFormatError) as exc_info:
        deserialize_snapshot_json(bad_json)
    assert secret_token not in str(exc_info.value)


def test_environment_partial_collection_and_presence_vs_value_yields_unknown() -> None:
    base_dict = load_snapshot(FIXTURES_DIR / "baseline.json").to_dict()
    curr_dict = copy.deepcopy(base_dict)

    # Variable tracked only in baseline -> unknown
    base_dict["sections"]["environment"]["ONLY_IN_BASE"] = {"present": True}

    # Variable with value in baseline, presence-only in current -> unknown
    base_dict["sections"]["environment"]["PARTIAL_VAL"] = {
        "present": True,
        "value": "v1",
    }
    curr_dict["sections"]["environment"]["PARTIAL_VAL"] = {"present": True}

    report = compare(Snapshot.from_dict(base_dict), Snapshot.from_dict(curr_dict))
    by_path = {d.path: d for d in report.differences}

    assert by_path["sections.environment.ONLY_IN_BASE"].change_type == "unknown"
    assert by_path["sections.environment.PARTIAL_VAL"].change_type == "unknown"
    assert not report.has_differences
    assert report.has_unknowns


def test_platform_and_runtime_none_vs_value_yields_unknown() -> None:
    base_dict = load_snapshot(FIXTURES_DIR / "baseline.json").to_dict()
    curr_dict = copy.deepcopy(base_dict)
    curr_dict["sections"]["platform"]["release"] = None
    curr_dict["sections"]["runtime"]["timezone"] = None

    report = compare(Snapshot.from_dict(base_dict), Snapshot.from_dict(curr_dict))
    by_path = {d.path: d for d in report.differences}

    assert by_path["sections.platform.release"].change_type == "unknown"
    assert by_path["sections.runtime.timezone"].change_type == "unknown"


def test_large_package_inventory_comparison_performance() -> None:
    """Comparing snapshots with 500 packages should be deterministic and fast (<0.5s)."""
    base_dict = load_snapshot(FIXTURES_DIR / "baseline.json").to_dict()
    curr_dict = copy.deepcopy(base_dict)

    base_pkgs = {f"pkg-{i:04d}": f"1.0.{i}" for i in range(500)}
    curr_pkgs = {f"pkg-{i:04d}": f"1.0.{i}" for i in range(500)}
    curr_pkgs["pkg-0010"] = "2.0.0"
    del curr_pkgs["pkg-0020"]
    curr_pkgs["pkg-9999"] = "0.1.0"

    base_dict["sections"]["packages"] = base_pkgs
    curr_dict["sections"]["packages"] = curr_pkgs

    start = time.perf_counter()
    snap_a = Snapshot.from_dict(base_dict)
    snap_b = Snapshot.from_dict(curr_dict)
    report = compare(snap_a, snap_b)
    elapsed = time.perf_counter() - start

    assert elapsed < 0.5
    assert len(report.differences) == 3


def test_compare_rejects_non_snapshot_arguments() -> None:
    baseline = load_snapshot(FIXTURES_DIR / "baseline.json")
    with pytest.raises(ComparisonError):
        compare(baseline, {})  # type: ignore[arg-type]
