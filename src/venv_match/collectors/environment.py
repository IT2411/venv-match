"""Allowlist-based collector for environment variables with privacy controls."""

import os
from collections.abc import Iterable, Mapping
from typing import Any

from venv_match.exceptions import CollectionError

SECRET_KEYWORDS: tuple[str, ...] = (
    "TOKEN",
    "SECRET",
    "PASSWORD",
    "PASSWD",
    "API_KEY",
    "APIKEY",
    "PRIVATE_KEY",
    "PRIVATEKEY",
    "CREDENTIAL",
    "AUTH",
)


def is_secret_variable_name(name: str) -> bool:
    """Return True if the variable name contains a known secret-like keyword."""
    upper_name = name.upper()
    return any(keyword in upper_name for keyword in SECRET_KEYWORDS)


def validate_env_var_name(name: str) -> str:
    """Validate an allowlisted environment variable name (no wildcards or blanks)."""
    if not isinstance(name, str) or not name.strip():
        raise CollectionError("Environment variable name must be a non-empty string.")
    cleaned = name.strip()
    if "*" in cleaned or "?" in cleaned:
        raise CollectionError(
            f"Wildcard environment variable collection is not permitted: '{cleaned}'."
        )
    return cleaned


def collect_environment_metadata(
    allowlist: Iterable[str] = (),
    include_values: bool = False,
    environ: Mapping[str, str] | None = None,
) -> dict[str, dict[str, Any]]:
    """Collect explicitly allowlisted environment variables respecting privacy policy."""
    env_source: Mapping[str, str] = os.environ if environ is None else environ
    validated_names = sorted({validate_env_var_name(name) for name in allowlist})

    result: dict[str, dict[str, Any]] = {}
    for var_name in validated_names:
        present = var_name in env_source
        entry: dict[str, Any] = {"present": present}
        if include_values and not is_secret_variable_name(var_name):
            entry["value"] = env_source[var_name] if present else None
        result[var_name] = entry

    return result
