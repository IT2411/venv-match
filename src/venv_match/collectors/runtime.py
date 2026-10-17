"""Collector for working directory, timezone, and locale context."""

import datetime
import locale
import os
import time
from typing import Any


def _detect_working_directory() -> str | None:
    try:
        cwd = os.getcwd()
        return cwd if cwd else None
    except Exception:
        return None


def _detect_timezone() -> str | None:
    try:
        tz_env = os.environ.get("TZ", "").strip()
        if tz_env:
            return tz_env
        now_tz = datetime.datetime.now().astimezone().tzname()
        if now_tz and now_tz.strip():
            return now_tz.strip()
        if time.tzname and time.tzname[0]:
            return time.tzname[0].strip() or None
    except Exception:
        return None
    return None


def _detect_locale() -> str | None:
    """Detect locale without mutating global process locale state."""
    try:
        lang_code, encoding = locale.getlocale()
        if lang_code and encoding:
            return f"{lang_code}.{encoding}"
        if lang_code:
            return str(lang_code)
    except Exception:
        pass

    for env_var in ("LC_ALL", "LC_CTYPE", "LANG"):
        val = os.environ.get(env_var, "").strip()
        if val:
            return val
    return None


def collect_runtime_metadata() -> dict[str, Any]:
    """Collect runtime working directory, timezone, and locale safely."""
    return {
        "working_directory": _detect_working_directory(),
        "timezone": _detect_timezone(),
        "locale": _detect_locale(),
    }
