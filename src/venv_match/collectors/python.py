"""Collector for Python interpreter and virtual environment metadata."""

import platform
import sys
from typing import Any

from venv_match.exceptions import CollectionError


def _detect_is_venv() -> bool:
    """Detect whether the interpreter is running in a virtual environment."""
    base_prefix = getattr(sys, "base_prefix", sys.prefix)
    real_prefix = getattr(sys, "real_prefix", None)
    return real_prefix is not None or sys.prefix != base_prefix


def collect_python_metadata() -> dict[str, Any]:
    """Collect Python runtime metadata using standard library attributes."""
    try:
        implementation = platform.python_implementation() or sys.implementation.name
        version = platform.python_version()
        v_info = sys.version_info
        version_info = [int(v_info[0]), int(v_info[1]), int(v_info[2])]
        executable = sys.executable or "unknown"
        prefix = sys.prefix or "unknown"
        base_prefix = getattr(sys, "base_prefix", sys.prefix) or prefix
        is_venv = _detect_is_venv()
    except Exception as exc:
        raise CollectionError(f"Failed to collect Python metadata: {exc}") from exc

    return {
        "implementation": implementation,
        "version": version,
        "version_info": version_info,
        "executable": executable,
        "prefix": prefix,
        "base_prefix": base_prefix,
        "is_venv": is_venv,
    }
