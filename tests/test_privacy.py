"""Privacy and security tests for Phase 6."""

import copy
from pathlib import Path

import pytest

from venv_match import CaptureConfig, Snapshot, capture, compare, load_snapshot
from venv_match.reporting import (
    REDACTED_PLACEHOLDER,
    format_comparison_json,
    format_comparison_text,
    format_inspection_text,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_unapproved_env_vars_never_collected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("UNAPPROVED_SECRET_KEY", "top-secret-12345")
    monkeypatch.setenv("RANDOM_USER_VAR", "sensitive-user-data")

    snap = capture(CaptureConfig(env_vars=("TZ",), include_env_values=True))
    raw_json = snap.to_json()

    assert "UNAPPROVED_SECRET_KEY" not in raw_json
    assert "top-secret-12345" not in raw_json
    assert "RANDOM_USER_VAR" not in raw_json
    assert "sensitive-user-data" not in raw_json


def test_secret_like_env_var_value_excluded_even_when_allowlisted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    secret_val = "ghp_super_secret_token_9999"
    monkeypatch.setenv("GITHUB_API_TOKEN", secret_val)

    snap = capture(
        CaptureConfig(env_vars=("GITHUB_API_TOKEN",), include_env_values=True)
    )
    assert secret_val not in snap.to_json()
    assert secret_val not in format_inspection_text(snap)


def test_crafted_snapshot_with_secret_value_is_redacted_in_all_reports() -> None:
    baseline = load_snapshot(FIXTURES_DIR / "baseline.json")
    curr_dict = copy.deepcopy(baseline.to_dict())

    leaked_secret = "leaked_password_value_xyz"
    curr_dict["sections"]["environment"]["DB_PASSWORD"] = {
        "present": True,
        "value": leaked_secret,
    }
    base_dict = copy.deepcopy(baseline.to_dict())
    base_dict["sections"]["environment"]["DB_PASSWORD"] = {
        "present": True,
        "value": "old_password_value_abc",
    }

    snap_base = Snapshot.from_dict(base_dict)
    snap_curr = Snapshot.from_dict(curr_dict)

    report = compare(snap_base, snap_curr)
    text_out = format_comparison_text(report)
    json_out = format_comparison_json(report)
    inspect_out = format_inspection_text(snap_curr)

    assert leaked_secret not in text_out
    assert "old_password_value_abc" not in text_out
    assert REDACTED_PLACEHOLDER in text_out

    assert leaked_secret not in json_out
    assert "old_password_value_abc" not in json_out
    assert REDACTED_PLACEHOLDER in json_out

    assert leaked_secret not in inspect_out
    assert REDACTED_PLACEHOLDER in inspect_out
