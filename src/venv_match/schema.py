"""Snapshot schema definition, normalization, validation, and JSON serialization."""

import json
import re
from collections.abc import Mapping
from typing import Any

from venv_match.exceptions import SnapshotFormatError, UnsupportedSchemaVersionError

CURRENT_SCHEMA_VERSION = "1.0"
SUPPORTED_SCHEMA_VERSIONS: frozenset[str] = frozenset({CURRENT_SCHEMA_VERSION})
MAX_SNAPSHOT_BYTES = 10 * 1024 * 1024  # 10 MiB limit for untrusted snapshot inputs

KNOWN_SECTIONS: tuple[str, ...] = (
    "python",
    "platform",
    "packages",
    "runtime",
    "environment",
)

_PACKAGE_NORMALIZE_RE = re.compile(r"[-_.]+")
_ISO_UTC_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|\+00:00)$"
)


def normalize_package_name(name: str) -> str:
    """Normalize a Python distribution name according to PEP 503 rules."""
    if not isinstance(name, str) or not name.strip():
        raise SnapshotFormatError("Package name must be a non-empty string.")
    return _PACKAGE_NORMALIZE_RE.sub("-", name.strip()).lower()


def _require_mapping(value: Any, context: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise SnapshotFormatError(f"Expected an object for '{context}'.")
    for k in value:
        if not isinstance(k, str):
            raise SnapshotFormatError(f"All keys in '{context}' must be strings.")
    return value


def _require_non_empty_str(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SnapshotFormatError(f"'{field_name}' must be a non-empty string.")
    return value


def _require_optional_str(value: Any, field_name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise SnapshotFormatError(f"'{field_name}' must be a string or null.")
    return value


def _validate_python_section(raw: Any) -> dict[str, Any]:
    data = _require_mapping(raw, "sections.python")
    required_keys = (
        "implementation",
        "version",
        "version_info",
        "executable",
        "prefix",
        "base_prefix",
        "is_venv",
    )
    for key in required_keys:
        if key not in data:
            raise SnapshotFormatError(
                f"Missing required field 'sections.python.{key}'."
            )

    implementation = _require_non_empty_str(
        data["implementation"], "sections.python.implementation"
    )
    version = _require_non_empty_str(data["version"], "sections.python.version")

    version_info = data["version_info"]
    if (
        not isinstance(version_info, list)
        or len(version_info) < 2
        or any(
            not isinstance(part, int) or isinstance(part, bool) for part in version_info
        )
    ):
        raise SnapshotFormatError(
            "'sections.python.version_info' must be a list of integers."
        )

    executable = _require_non_empty_str(
        data["executable"], "sections.python.executable"
    )
    prefix = _require_non_empty_str(data["prefix"], "sections.python.prefix")
    base_prefix = _require_non_empty_str(
        data["base_prefix"], "sections.python.base_prefix"
    )

    is_venv = data["is_venv"]
    if not isinstance(is_venv, bool):
        raise SnapshotFormatError("'sections.python.is_venv' must be a boolean.")

    validated: dict[str, Any] = {
        "implementation": implementation,
        "version": version,
        "version_info": list(version_info),
        "executable": executable,
        "prefix": prefix,
        "base_prefix": base_prefix,
        "is_venv": is_venv,
    }
    return validated


def _validate_platform_section(raw: Any) -> dict[str, Any]:
    data = _require_mapping(raw, "sections.platform")
    for key in ("system", "release", "machine"):
        if key not in data:
            raise SnapshotFormatError(
                f"Missing required field 'sections.platform.{key}'."
            )

    return {
        "system": _require_optional_str(data["system"], "sections.platform.system"),
        "release": _require_optional_str(data["release"], "sections.platform.release"),
        "machine": _require_optional_str(data["machine"], "sections.platform.machine"),
    }


def _validate_packages_section(raw: Any) -> dict[str, str]:
    data = _require_mapping(raw, "sections.packages")
    normalized: dict[str, str] = {}
    for pkg_name, pkg_version in data.items():
        norm_name = normalize_package_name(pkg_name)
        version_str = _require_non_empty_str(
            pkg_version, f"sections.packages.{pkg_name}"
        )
        if norm_name in normalized and normalized[norm_name] != version_str:
            raise SnapshotFormatError(
                f"Conflicting versions for normalized package '{norm_name}'."
            )
        normalized[norm_name] = version_str

    return dict(sorted(normalized.items()))


def _validate_runtime_section(raw: Any) -> dict[str, Any]:
    data = _require_mapping(raw, "sections.runtime")
    for key in ("working_directory", "timezone", "locale"):
        if key not in data:
            raise SnapshotFormatError(
                f"Missing required field 'sections.runtime.{key}'."
            )

    return {
        "working_directory": _require_optional_str(
            data["working_directory"], "sections.runtime.working_directory"
        ),
        "timezone": _require_optional_str(
            data["timezone"], "sections.runtime.timezone"
        ),
        "locale": _require_optional_str(data["locale"], "sections.runtime.locale"),
    }


def _validate_environment_section(raw: Any) -> dict[str, dict[str, Any]]:
    data = _require_mapping(raw, "sections.environment")
    validated_env: dict[str, dict[str, Any]] = {}
    for var_name in sorted(data.keys()):
        if not var_name.strip():
            raise SnapshotFormatError(
                "Environment variable names in 'sections.environment' must not be empty."
            )
        entry = _require_mapping(data[var_name], f"sections.environment.{var_name}")
        if "present" not in entry or not isinstance(entry["present"], bool):
            raise SnapshotFormatError(
                f"'sections.environment.{var_name}.present' must be a boolean."
            )
        present = entry["present"]
        raw_val = entry.get("value")
        val = _require_optional_str(raw_val, f"sections.environment.{var_name}.value")
        if not present and val is not None:
            raise SnapshotFormatError(
                f"'sections.environment.{var_name}.value' must be null when 'present' is false."
            )
        entry_dict: dict[str, Any] = {"present": present}
        if "value" in entry:
            entry_dict["value"] = val
        validated_env[var_name] = entry_dict
    return validated_env


def _validate_collection_metadata(
    raw: Any, present_sections: set[str]
) -> dict[str, Any]:
    data = _require_mapping(raw, "collection")
    if "completed_sections" not in data or "errors" not in data:
        raise SnapshotFormatError(
            "'collection' must contain 'completed_sections' and 'errors'."
        )

    raw_completed = data["completed_sections"]
    if not isinstance(raw_completed, list):
        raise SnapshotFormatError("'collection.completed_sections' must be a list.")

    completed: list[str] = []
    seen: set[str] = set()
    for item in raw_completed:
        sec_name = _require_non_empty_str(item, "collection.completed_sections[]")
        if sec_name not in KNOWN_SECTIONS:
            raise SnapshotFormatError(
                f"Unknown section '{sec_name}' in 'collection.completed_sections'."
            )
        if sec_name not in present_sections:
            raise SnapshotFormatError(
                f"Section '{sec_name}' is listed in 'completed_sections' but missing from 'sections'."
            )
        if sec_name not in seen:
            completed.append(sec_name)
            seen.add(sec_name)

    raw_errors = data["errors"]
    if not isinstance(raw_errors, list):
        raise SnapshotFormatError("'collection.errors' must be a list.")

    errors: list[dict[str, str]] = []
    for idx, err_item in enumerate(raw_errors):
        err_map = _require_mapping(err_item, f"collection.errors[{idx}]")
        section = _require_non_empty_str(
            err_map.get("section"), f"collection.errors[{idx}].section"
        )
        if section not in KNOWN_SECTIONS:
            raise SnapshotFormatError(
                f"Unknown section '{section}' in 'collection.errors[{idx}]'."
            )
        message = _require_non_empty_str(
            err_map.get("message"), f"collection.errors[{idx}].message"
        )
        err_entry: dict[str, str] = {"section": section, "message": message}
        if "error_type" in err_map and err_map["error_type"] is not None:
            err_entry["error_type"] = _require_non_empty_str(
                err_map["error_type"], f"collection.errors[{idx}].error_type"
            )
        errors.append(err_entry)

    return {
        "completed_sections": completed,
        "errors": errors,
    }


def validate_snapshot_dict(raw: Any) -> dict[str, Any]:
    """Validate and normalize a raw parsed JSON mapping into a canonical snapshot dict."""
    root = _require_mapping(raw, "root")

    if "schema_version" not in root:
        raise SnapshotFormatError("Missing required top-level field 'schema_version'.")
    schema_version = _require_non_empty_str(root["schema_version"], "schema_version")
    if schema_version not in SUPPORTED_SCHEMA_VERSIONS:
        raise UnsupportedSchemaVersionError(
            f"Unsupported snapshot schema_version '{schema_version}'. "
            f"Supported versions: {', '.join(sorted(SUPPORTED_SCHEMA_VERSIONS))}."
        )

    if "venv_match_version" not in root:
        raise SnapshotFormatError(
            "Missing required top-level field 'venv_match_version'."
        )
    venv_match_version = _require_non_empty_str(
        root["venv_match_version"], "venv_match_version"
    )

    if "captured_at" not in root:
        raise SnapshotFormatError("Missing required top-level field 'captured_at'.")
    captured_at = _require_non_empty_str(root["captured_at"], "captured_at")
    if not _ISO_UTC_RE.match(captured_at):
        raise SnapshotFormatError(
            "'captured_at' must be a valid UTC ISO 8601 timestamp (e.g. '2026-09-28T10:00:00Z')."
        )

    if "sections" not in root:
        raise SnapshotFormatError("Missing required top-level field 'sections'.")
    raw_sections = _require_mapping(root["sections"], "sections")

    if "python" not in raw_sections or raw_sections["python"] is None:
        raise SnapshotFormatError(
            "Required section 'sections.python' is missing or null."
        )

    validated_sections: dict[str, Any] = {}
    present_sections: set[str] = set()

    for section_name in KNOWN_SECTIONS:
        if section_name not in raw_sections or raw_sections[section_name] is None:
            continue
        sec_val = raw_sections[section_name]
        if section_name == "python":
            validated_sections["python"] = _validate_python_section(sec_val)
        elif section_name == "platform":
            validated_sections["platform"] = _validate_platform_section(sec_val)
        elif section_name == "packages":
            validated_sections["packages"] = _validate_packages_section(sec_val)
        elif section_name == "runtime":
            validated_sections["runtime"] = _validate_runtime_section(sec_val)
        elif section_name == "environment":
            validated_sections["environment"] = _validate_environment_section(sec_val)
        present_sections.add(section_name)

    if "collection" not in root:
        raise SnapshotFormatError("Missing required top-level field 'collection'.")
    validated_collection = _validate_collection_metadata(
        root["collection"], present_sections
    )

    if "python" not in validated_collection["completed_sections"]:
        raise SnapshotFormatError(
            "'python' must be present in 'collection.completed_sections'."
        )

    return {
        "schema_version": schema_version,
        "venv_match_version": venv_match_version,
        "captured_at": captured_at,
        "sections": validated_sections,
        "collection": validated_collection,
    }


def serialize_snapshot_dict(data: Mapping[str, Any]) -> str:
    """Validate and deterministically serialize a snapshot dictionary to UTF-8 JSON."""
    validated = validate_snapshot_dict(data)
    return json.dumps(validated, indent=2, sort_keys=False) + "\n"


def deserialize_snapshot_json(raw_json: str) -> dict[str, Any]:
    """Safely parse and validate a JSON string into a normalized snapshot dictionary."""
    if not isinstance(raw_json, str):
        raise SnapshotFormatError("Snapshot JSON input must be a string.")
    if len(raw_json.encode("utf-8")) > MAX_SNAPSHOT_BYTES:
        raise SnapshotFormatError(
            f"Snapshot JSON exceeds maximum allowed size of {MAX_SNAPSHOT_BYTES} bytes."
        )
    try:
        parsed = json.loads(raw_json)
    except json.JSONDecodeError as exc:
        raise SnapshotFormatError(
            f"Invalid JSON in snapshot at line {exc.lineno}, column {exc.colno}."
        ) from exc

    return validate_snapshot_dict(parsed)
