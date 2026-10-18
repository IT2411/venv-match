"""Tests for virtual environment creation and requirements export (v0.2.0)."""

import copy
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from venv_match import (
    Snapshot,
    SnapshotFormatError,
    create_venv,
    export_requirements,
    load_snapshot,
)
from venv_match.cli import (
    EXIT_COLLECTION_OR_IO_ERROR,
    EXIT_SNAPSHOT_LOAD_ERROR,
    EXIT_SUCCESS,
    main,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_export_requirements_excludes_build_tools_by_default() -> None:
    base_dict = load_snapshot(FIXTURES_DIR / "baseline.json").to_dict()
    base_dict["sections"]["packages"] = {
        "pip": "24.0",
        "setuptools": "70.0.0",
        "wheel": "0.43.0",
        "requests": "2.32.3",
        "numpy": "1.26.4",
    }
    snap = Snapshot.from_dict(base_dict)

    reqs_default = export_requirements(snap)
    assert reqs_default == ["numpy==1.26.4", "requests==2.32.3"]

    reqs_with_tools = export_requirements(snap, include_build_tools=True)
    assert reqs_with_tools == [
        "numpy==1.26.4",
        "pip==24.0",
        "requests==2.32.3",
        "setuptools==70.0.0",
        "wheel==0.43.0",
    ]


def test_export_requirements_rejects_uncollected_packages_section() -> None:
    base_dict = load_snapshot(FIXTURES_DIR / "baseline.json").to_dict()
    del base_dict["sections"]["packages"]
    base_dict["collection"]["completed_sections"] = ["python", "platform", "runtime"]
    snap = Snapshot.from_dict(base_dict)

    with pytest.raises(
        SnapshotFormatError, match="does not contain a collected 'packages'"
    ):
        export_requirements(snap)


def test_export_requirements_rejects_pip_flag_injection() -> None:
    base_dict = load_snapshot(FIXTURES_DIR / "baseline.json").to_dict()
    malicious_dict = copy.deepcopy(base_dict)
    malicious_dict["sections"]["packages"] = {
        "requests": "--extra-index-url=https://evil.example/simple",
    }
    snap = Snapshot.from_dict(malicious_dict)

    with pytest.raises(
        SnapshotFormatError, match="Unsafe or invalid package specification"
    ):
        export_requirements(snap)


def test_cli_export_stdout_and_file_with_overwrite_protection(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    baseline_path = str(FIXTURES_DIR / "baseline.json")

    # Print to stdout
    code = main(["export", baseline_path])
    out = capsys.readouterr().out
    assert code == EXIT_SUCCESS
    assert out == "numpy==1.26.4\nrequests==2.32.3\n"

    # Write to file
    req_file = tmp_path / "requirements.txt"
    code_file = main(["export", baseline_path, "--output", str(req_file)])
    _ = capsys.readouterr()
    assert code_file == EXIT_SUCCESS
    assert req_file.read_text(encoding="utf-8") == "numpy==1.26.4\nrequests==2.32.3\n"

    # Overwrite protection
    code_dup = main(["export", baseline_path, "--output", str(req_file)])
    err = capsys.readouterr().err
    assert code_dup == EXIT_COLLECTION_OR_IO_ERROR
    assert "already exists" in err


def test_create_venv_dry_run_and_overwrite_protection(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    baseline_path = str(FIXTURES_DIR / "baseline.json")
    target_dir = tmp_path / "my-venv"

    code = main(["create", baseline_path, "--target", str(target_dir), "--dry-run"])
    captured = capsys.readouterr()
    assert code == EXIT_SUCCESS
    assert "[Dry Run] Would create virtual environment" in captured.out
    assert "numpy==1.26.4, requests==2.32.3" in captured.out
    assert not target_dir.exists()

    # Existing target directory without overwrite must fail with exit code 4
    target_dir.mkdir()
    code_exists = main(["create", baseline_path, "--target", str(target_dir)])
    captured_exists = capsys.readouterr()
    assert code_exists == EXIT_COLLECTION_OR_IO_ERROR
    assert "Refusing to overwrite" in captured_exists.err


def test_create_venv_invokes_venv_and_pip_safely(tmp_path: Path) -> None:
    baseline = load_snapshot(FIXTURES_DIR / "baseline.json")
    target_dir = tmp_path / "recreated-venv"

    recorded_cmds: list[list[str]] = []

    def _fake_run(
        cmd: list[str], **_kwargs: object
    ) -> subprocess.CompletedProcess[str]:
        recorded_cmds.append(list(cmd))
        # When `python -m venv <target>` runs, create the fake bin/python
        if len(cmd) >= 3 and cmd[1:3] == ["-m", "venv"]:
            bin_dir = target_dir / "bin"
            bin_dir.mkdir(parents=True, exist_ok=True)
            (bin_dir / "python").write_text("", encoding="utf-8")
        return subprocess.CompletedProcess(cmd, 0, stdout="3.12.5\n", stderr="")

    with patch("venv_match.recreate.subprocess.run", side_effect=_fake_run):
        res = create_venv(baseline, target_dir)

    assert not res.dry_run
    assert res.installed_packages == ("numpy==1.26.4", "requests==2.32.3")
    assert any(cmd[1:3] == ["-m", "venv"] for cmd in recorded_cmds)
    assert any(
        cmd[1:4] == ["-m", "pip", "install"] and "--" in cmd for cmd in recorded_cmds
    )


def test_cli_create_fails_with_code_3_when_packages_uncollected(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    no_pkg_snap = tmp_path / "no_pkgs.json"
    assert (
        main(["capture", "--output", str(no_pkg_snap), "--no-packages"]) == EXIT_SUCCESS
    )
    _ = capsys.readouterr()

    code = main(
        ["create", str(no_pkg_snap), "--target", str(tmp_path / "venv"), "--dry-run"]
    )
    err = capsys.readouterr().err
    assert code == EXIT_SNAPSHOT_LOAD_ERROR
    assert "does not contain a collected 'packages' section" in err
