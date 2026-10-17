"""Unit and integration tests for Phase 4 snapshot service and persistence."""

from pathlib import Path

import pytest

from venv_match import (
    CaptureConfig,
    CollectionError,
    Snapshot,
    SnapshotFormatError,
    capture,
    load_snapshot,
)


def test_capture_default_config_succeeds() -> None:
    snap = capture()
    assert isinstance(snap, Snapshot)
    assert snap.schema_version == "1.0"
    assert snap.venv_match_version == "0.1.0"
    assert "python" in snap.completed_sections
    assert "platform" in snap.completed_sections
    assert "packages" in snap.completed_sections
    assert "runtime" in snap.completed_sections
    assert "environment" in snap.completed_sections
    assert snap.collection_errors == []
    assert snap.sections["environment"] == {}


def test_capture_disabling_optional_sections() -> None:
    cfg = CaptureConfig(
        include_packages=False,
        include_platform=False,
        include_runtime=False,
    )
    snap = capture(cfg)
    assert snap.completed_sections == ["python", "environment"]
    assert "packages" not in snap.sections
    assert "platform" not in snap.sections
    assert "runtime" not in snap.sections


def test_capture_with_env_vars(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VENV_MATCH_TEST_VAR", "hello")
    monkeypatch.setenv("VENV_MATCH_SECRET_TOKEN", "do-not-record")

    cfg = CaptureConfig(
        env_vars=("VENV_MATCH_TEST_VAR", "VENV_MATCH_SECRET_TOKEN", "MISSING_TEST_VAR"),
        include_env_values=True,
    )
    snap = capture(cfg)
    env_sec = snap.sections["environment"]
    assert env_sec["VENV_MATCH_TEST_VAR"] == {"present": True, "value": "hello"}
    assert env_sec["MISSING_TEST_VAR"] == {"present": False, "value": None}
    assert env_sec["VENV_MATCH_SECRET_TOKEN"] == {"present": True}
    assert "value" not in env_sec["VENV_MATCH_SECRET_TOKEN"]


def test_save_and_load_roundtrip_and_overwrite_protection(tmp_path: Path) -> None:
    snap = capture(CaptureConfig(include_packages=False))
    out_file = tmp_path / "snap.json"

    saved_path = snap.save(out_file)
    assert saved_path == out_file
    assert out_file.exists()

    # Overwrite protection must reject saving again by default
    with pytest.raises(CollectionError, match="Refusing to overwrite"):
        snap.save(out_file)

    # Explicit overwrite=True succeeds
    snap.save(out_file, overwrite=True)

    loaded = load_snapshot(out_file)
    assert loaded.to_dict() == snap.to_dict()
    assert loaded.to_json() == snap.to_json()


def test_load_missing_file_raises_snapshot_format_error(tmp_path: Path) -> None:
    missing = tmp_path / "does_not_exist.json"
    with pytest.raises(SnapshotFormatError, match="Could not read snapshot file"):
        load_snapshot(missing)


def test_optional_collector_failure_recorded_by_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _failing_packages() -> dict[str, str]:
        raise CollectionError("Simulated package metadata error")

    monkeypatch.setattr(
        "venv_match.snapshot.collect_packages_metadata", _failing_packages
    )

    snap = capture(CaptureConfig(include_packages=True))
    assert "packages" not in snap.completed_sections
    assert "packages" not in snap.sections
    assert len(snap.collection_errors) == 1
    assert snap.collection_errors[0]["section"] == "packages"
    assert "Simulated package metadata error" in snap.collection_errors[0]["message"]


def test_optional_collector_failure_raises_when_strict(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _failing_packages() -> dict[str, str]:
        raise CollectionError("Simulated strict package error")

    monkeypatch.setattr(
        "venv_match.snapshot.collect_packages_metadata", _failing_packages
    )

    with pytest.raises(CollectionError, match="Simulated strict package error"):
        capture(CaptureConfig(include_packages=True, strict_optional_collectors=True))


def test_required_python_collector_failure_always_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _failing_python() -> dict[str, object]:
        raise CollectionError("Python metadata unavailable")

    monkeypatch.setattr("venv_match.snapshot.collect_python_metadata", _failing_python)

    with pytest.raises(CollectionError, match="Python metadata unavailable"):
        capture()
