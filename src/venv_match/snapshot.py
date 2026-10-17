"""Snapshot model, environment capture service, and file persistence."""

import copy
from collections.abc import Callable, Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from venv_match.collectors import (
    collect_environment_metadata,
    collect_packages_metadata,
    collect_platform_metadata,
    collect_python_metadata,
    collect_runtime_metadata,
)
from venv_match.config import CaptureConfig
from venv_match.exceptions import CollectionError, SnapshotFormatError
from venv_match.schema import (
    CURRENT_SCHEMA_VERSION,
    deserialize_snapshot_json,
    serialize_snapshot_dict,
    validate_snapshot_dict,
)

PACKAGE_VERSION = "0.1.0"


class Snapshot:
    """Validated, immutable-by-convention representation of an environment snapshot."""

    def __init__(self, data: Mapping[str, Any]) -> None:
        self._data: dict[str, Any] = validate_snapshot_dict(data)

    @property
    def schema_version(self) -> str:
        return str(self._data["schema_version"])

    @property
    def venv_match_version(self) -> str:
        return str(self._data["venv_match_version"])

    @property
    def captured_at(self) -> str:
        return str(self._data["captured_at"])

    @property
    def sections(self) -> dict[str, Any]:
        return copy.deepcopy(self._data["sections"])

    @property
    def collection(self) -> dict[str, Any]:
        return copy.deepcopy(self._data["collection"])

    @property
    def completed_sections(self) -> list[str]:
        return list(self._data["collection"]["completed_sections"])

    @property
    def collection_errors(self) -> list[dict[str, str]]:
        return copy.deepcopy(self._data["collection"]["errors"])

    def to_dict(self) -> dict[str, Any]:
        """Return a deep copy of the normalized snapshot dictionary."""
        return copy.deepcopy(self._data)

    def to_json(self) -> str:
        """Return a deterministic UTF-8 JSON string representation of the snapshot."""
        return serialize_snapshot_dict(self._data)

    def save(self, path: str | Path, *, overwrite: bool = False) -> Path:
        """Write the snapshot to a UTF-8 JSON file with overwrite protection."""
        target = Path(path)
        if target.exists() and not overwrite:
            raise CollectionError(
                f"Refusing to overwrite existing snapshot file '{target}'. "
                "Pass overwrite=True or --overwrite to replace it."
            )
        json_content = self.to_json()
        try:
            target.write_text(json_content, encoding="utf-8")
        except OSError as exc:
            raise CollectionError(
                f"Failed to write snapshot to '{target}': {exc}"
            ) from exc
        return target

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "Snapshot":
        """Create and validate a Snapshot from a dictionary."""
        return cls(data)

    @classmethod
    def from_json(cls, raw_json: str) -> "Snapshot":
        """Create and validate a Snapshot from a JSON string."""
        return cls(deserialize_snapshot_json(raw_json))


def load_snapshot(path: str | Path) -> Snapshot:
    """Load and validate a Snapshot from a JSON file on disk."""
    source = Path(path)
    try:
        raw_json = source.read_text(encoding="utf-8")
    except OSError as exc:
        raise SnapshotFormatError(
            f"Could not read snapshot file '{source}': {exc}"
        ) from exc
    return Snapshot.from_json(raw_json)


def _utc_now_iso() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def capture(config: CaptureConfig | None = None) -> Snapshot:
    """Capture the current Python environment into a validated Snapshot."""
    cfg = config if config is not None else CaptureConfig()

    sections: dict[str, Any] = {}
    completed_sections: list[str] = []
    errors: list[dict[str, str]] = []

    # Required section: python
    try:
        sections["python"] = collect_python_metadata()
        completed_sections.append("python")
    except CollectionError:
        raise
    except Exception as exc:
        raise CollectionError(
            f"Required Python metadata collection failed: {exc}"
        ) from exc

    optional_collectors: list[tuple[str, bool, Callable[[], Any]]] = [
        ("platform", cfg.include_platform, collect_platform_metadata),
        ("packages", cfg.include_packages, collect_packages_metadata),
        ("runtime", cfg.include_runtime, collect_runtime_metadata),
        (
            "environment",
            True,
            lambda: collect_environment_metadata(
                allowlist=cfg.env_vars,
                include_values=cfg.include_env_values,
            ),
        ),
    ]

    for section_name, enabled, collector_fn in optional_collectors:
        if not enabled:
            continue
        try:
            sections[section_name] = collector_fn()
            completed_sections.append(section_name)
        except Exception as exc:
            if cfg.strict_optional_collectors:
                if isinstance(exc, CollectionError):
                    raise
                raise CollectionError(
                    f"Collector '{section_name}' failed: {exc}"
                ) from exc
            errors.append(
                {
                    "section": section_name,
                    "message": str(exc) or f"Failed to collect '{section_name}'.",
                    "error_type": type(exc).__name__,
                }
            )

    raw_snapshot: dict[str, Any] = {
        "schema_version": CURRENT_SCHEMA_VERSION,
        "venv_match_version": PACKAGE_VERSION,
        "captured_at": _utc_now_iso(),
        "sections": sections,
        "collection": {
            "completed_sections": completed_sections,
            "errors": errors,
        },
    }
    return Snapshot(raw_snapshot)
