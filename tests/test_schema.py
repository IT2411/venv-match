"""Unit tests for Phase 2 snapshot schema and validation."""

import copy
from pathlib import Path

import pytest

from venv_match.exceptions import SnapshotFormatError, UnsupportedSchemaVersionError
from venv_match.schema import (
    deserialize_snapshot_json,
    normalize_package_name,
    serialize_snapshot_dict,
    validate_snapshot_dict,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _load_baseline_dict() -> dict[str, object]:
    raw = (FIXTURES_DIR / "baseline.json").read_text(encoding="utf-8")
    return deserialize_snapshot_json(raw)


def test_fixtures_are_valid_and_deterministic() -> None:
    for name in ("baseline.json", "changed.json"):
        content = (FIXTURES_DIR / name).read_text(encoding="utf-8")
        parsed = deserialize_snapshot_json(content)
        reserialized = serialize_snapshot_dict(parsed)
        assert reserialized == content


@pytest.mark.parametrize(
    ("raw_name", "expected"),
    [
        ("Requests", "requests"),
        ("typing_extensions", "typing-extensions"),
        ("zope.interface", "zope-interface"),
        ("Foo___Bar--Baz..Qux", "foo-bar-baz-qux"),
    ],
)
def test_normalize_package_name(raw_name: str, expected: str) -> None:
    assert normalize_package_name(raw_name) == expected


def test_normalize_package_name_rejects_empty() -> None:
    with pytest.raises(SnapshotFormatError):
        normalize_package_name("   ")


def test_packages_normalized_and_sorted_on_validation() -> None:
    data = _load_baseline_dict()
    sections = copy.deepcopy(data["sections"])
    assert isinstance(sections, dict)
    sections["packages"] = {
        "Zope.Interface": "6.0",
        "My_Pkg": "1.0.0",
        "attrs": "23.2.0",
    }
    data["sections"] = sections

    validated = validate_snapshot_dict(data)
    assert list(validated["sections"]["packages"].keys()) == [
        "attrs",
        "my-pkg",
        "zope-interface",
    ]


def test_conflicting_normalized_package_names_rejected() -> None:
    data = _load_baseline_dict()
    sections = copy.deepcopy(data["sections"])
    assert isinstance(sections, dict)
    sections["packages"] = {
        "my_pkg": "1.0.0",
        "my-pkg": "2.0.0",
    }
    data["sections"] = sections

    with pytest.raises(SnapshotFormatError, match="Conflicting versions"):
        validate_snapshot_dict(data)


def test_unsupported_schema_version_raises_specific_error() -> None:
    data = _load_baseline_dict()
    data["schema_version"] = "2.0"

    with pytest.raises(UnsupportedSchemaVersionError, match="2.0"):
        validate_snapshot_dict(data)


def test_invalid_timestamp_rejected() -> None:
    data = _load_baseline_dict()
    data["captured_at"] = "not-a-timestamp"

    with pytest.raises(SnapshotFormatError, match="captured_at"):
        validate_snapshot_dict(data)


def test_missing_python_section_rejected() -> None:
    data = _load_baseline_dict()
    sections = copy.deepcopy(data["sections"])
    assert isinstance(sections, dict)
    del sections["python"]
    data["sections"] = sections

    with pytest.raises(SnapshotFormatError, match="sections.python"):
        validate_snapshot_dict(data)


def test_missing_optional_section_allowed_when_not_in_completed() -> None:
    data = _load_baseline_dict()
    sections = copy.deepcopy(data["sections"])
    collection = copy.deepcopy(data["collection"])
    assert isinstance(sections, dict)
    assert isinstance(collection, dict)

    del sections["packages"]
    collection["completed_sections"] = ["python", "platform", "runtime", "environment"]
    collection["errors"] = [
        {
            "section": "packages",
            "message": "Package metadata read failed.",
            "error_type": "CollectionError",
        }
    ]
    data["sections"] = sections
    data["collection"] = collection

    validated = validate_snapshot_dict(data)
    assert "packages" not in validated["sections"]
    assert "packages" not in validated["collection"]["completed_sections"]
    assert len(validated["collection"]["errors"]) == 1


def test_completed_section_missing_from_sections_rejected() -> None:
    data = _load_baseline_dict()
    sections = copy.deepcopy(data["sections"])
    assert isinstance(sections, dict)
    del sections["packages"]
    data["sections"] = sections

    with pytest.raises(SnapshotFormatError, match="missing from 'sections'"):
        validate_snapshot_dict(data)


def test_environment_value_present_false_with_non_null_value_rejected() -> None:
    data = _load_baseline_dict()
    sections = copy.deepcopy(data["sections"])
    assert isinstance(sections, dict)
    sections["environment"] = {
        "TZ": {"present": False, "value": "UTC"},
    }
    data["sections"] = sections

    with pytest.raises(
        SnapshotFormatError, match="must be null when 'present' is false"
    ):
        validate_snapshot_dict(data)


def test_malformed_json_rejected_safely() -> None:
    with pytest.raises(SnapshotFormatError, match="Invalid JSON"):
        deserialize_snapshot_json("{bad json")
