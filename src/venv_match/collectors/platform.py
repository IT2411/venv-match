"""Collector for non-identifying operating system and architecture metadata."""

import platform
from typing import Any


def _clean_optional_str(value: str) -> str | None:
    stripped = value.strip()
    return stripped if stripped else None


def collect_platform_metadata() -> dict[str, Any]:
    """Collect OS family, release, and machine architecture safely."""
    try:
        system = _clean_optional_str(platform.system())
    except Exception:
        system = None

    try:
        release = _clean_optional_str(platform.release())
    except Exception:
        release = None

    try:
        machine = _clean_optional_str(platform.machine())
    except Exception:
        machine = None

    return {
        "system": system,
        "release": release,
        "machine": machine,
    }
