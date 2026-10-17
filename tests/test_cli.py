"""CLI unit and subprocess integration tests for Phase 7."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from venv_match.cli import (
    EXIT_COLLECTION_OR_IO_ERROR,
    EXIT_DIFF_THRESHOLD_MET,
    EXIT_SNAPSHOT_LOAD_ERROR,
    EXIT_SUCCESS,
    EXIT_UNSUPPORTED_SCHEMA,
    EXIT_USAGE_ERROR,
    main,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.mark.parametrize(
    "args",
    [
        ["--help"],
        ["capture", "--help"],
        ["compare", "--help"],
        ["inspect", "--help"],
    ],
)
def test_help_commands_succeed(
    args: list[str], capsys: pytest.CaptureFixture[str]
) -> None:
    code = main(args)
    captured = capsys.readouterr()
    assert code == EXIT_SUCCESS
    assert "usage:" in captured.out


def test_invalid_arguments_return_exit_code_2(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main([]) == EXIT_USAGE_ERROR
    assert main(["unknown-cmd"]) == EXIT_USAGE_ERROR
    assert main(["capture"]) == EXIT_USAGE_ERROR
    captured = capsys.readouterr()
    assert "error:" in captured.err


def test_capture_and_overwrite_protection(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    out_file = tmp_path / "captured.json"

    # First capture succeeds
    code = main(["capture", "--output", str(out_file), "--no-packages"])
    assert code == EXIT_SUCCESS
    assert out_file.exists()

    # Second capture without --overwrite fails with exit code 4
    code_no_overwrite = main(["capture", "--output", str(out_file), "--no-packages"])
    assert code_no_overwrite == EXIT_COLLECTION_OR_IO_ERROR
    err_out = capsys.readouterr().err
    assert "already exists" in err_out

    # Capture with --overwrite succeeds
    code_overwrite = main(
        ["capture", "--output", str(out_file), "--no-packages", "--overwrite"]
    )
    assert code_overwrite == EXIT_SUCCESS


def test_capture_with_env_values_emits_warning_to_stderr(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("MY_SAFE_VAR", "val123")
    out_file = tmp_path / "env_snap.json"

    code = main(
        [
            "capture",
            "--output",
            str(out_file),
            "--no-packages",
            "--env",
            "MY_SAFE_VAR",
            "--env-values",
        ]
    )
    assert code == EXIT_SUCCESS
    captured = capsys.readouterr()
    assert "Warning: --env-values is enabled" in captured.err


def test_inspect_command_succeeds(capsys: pytest.CaptureFixture[str]) -> None:
    baseline_path = str(FIXTURES_DIR / "baseline.json")
    code = main(["inspect", baseline_path])
    captured = capsys.readouterr()
    assert code == EXIT_SUCCESS
    assert "Venv Match Snapshot Inspection" in captured.out
    assert "3.12.5" in captured.out


def test_compare_text_and_json_and_thresholds(
    capsys: pytest.CaptureFixture[str],
) -> None:
    baseline_path = str(FIXTURES_DIR / "baseline.json")
    changed_path = str(FIXTURES_DIR / "changed.json")

    # Default compare returns 0 even when differences exist
    code = main(["compare", baseline_path, changed_path])
    out = capsys.readouterr().out
    assert code == EXIT_SUCCESS
    assert "Venv Match Comparison Report" in out

    # --fail-on-diff returns 1
    code_fail = main(["compare", baseline_path, changed_path, "--fail-on-diff"])
    _ = capsys.readouterr()
    assert code_fail == EXIT_DIFF_THRESHOLD_MET

    # --min-severity high returns 1 (since python version and missing package are high)
    code_sev_high = main(
        ["compare", baseline_path, changed_path, "--min-severity", "high"]
    )
    _ = capsys.readouterr()
    assert code_sev_high == EXIT_DIFF_THRESHOLD_MET

    # --min-severity critical returns 0 (no critical differences in fixtures)
    code_sev_crit = main(
        ["compare", baseline_path, changed_path, "--min-severity", "critical"]
    )
    _ = capsys.readouterr()
    assert code_sev_crit == EXIT_SUCCESS

    # --format json produces valid JSON on stdout even when returning exit code 1
    code_json = main(
        [
            "compare",
            baseline_path,
            changed_path,
            "--format",
            "json",
            "--fail-on-diff",
            "--ignore",
            "sections.packages.numpy",
        ]
    )
    captured_json = capsys.readouterr()
    assert code_json == EXIT_DIFF_THRESHOLD_MET
    assert captured_json.err == ""
    parsed = json.loads(captured_json.out)
    assert parsed["has_differences"] is True
    assert parsed["ignored_paths"] == ["sections.packages.numpy"]


def test_exit_code_3_on_missing_or_corrupt_snapshot(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    corrupt_file = tmp_path / "corrupt.json"
    corrupt_file.write_text("{not valid json", encoding="utf-8")

    assert main(["inspect", str(corrupt_file)]) == EXIT_SNAPSHOT_LOAD_ERROR
    assert main(["inspect", str(tmp_path / "missing.json")]) == EXIT_SNAPSHOT_LOAD_ERROR
    _ = capsys.readouterr()


def test_exit_code_5_on_unsupported_schema_version(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    baseline_raw = json.loads(
        (FIXTURES_DIR / "baseline.json").read_text(encoding="utf-8")
    )
    baseline_raw["schema_version"] = "99.0"
    future_file = tmp_path / "future.json"
    future_file.write_text(json.dumps(baseline_raw), encoding="utf-8")

    code = main(["inspect", str(future_file)])
    captured = capsys.readouterr()
    assert code == EXIT_UNSUPPORTED_SCHEMA
    assert "Unsupported snapshot schema_version '99.0'" in captured.err


def test_subprocess_cli_execution(tmp_path: Path) -> None:
    snap_path = tmp_path / "sub_snap.json"
    res_capture = subprocess.run(
        [
            sys.executable,
            "-m",
            "venv_match",
            "capture",
            "--output",
            str(snap_path),
            "--no-packages",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert res_capture.returncode == EXIT_SUCCESS
    assert snap_path.exists()

    res_compare = subprocess.run(
        [
            sys.executable,
            "-m",
            "venv_match",
            "compare",
            str(snap_path),
            str(snap_path),
            "--format",
            "json",
            "--fail-on-diff",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert res_compare.returncode == EXIT_SUCCESS
    parsed = json.loads(res_compare.stdout)
    assert parsed["has_differences"] is False
