"""Collector for installed Python distributions via importlib.metadata."""

import importlib.metadata
from collections.abc import Iterable
from typing import Any

from venv_match.exceptions import CollectionError
from venv_match.schema import normalize_package_name


def collect_packages_metadata(
    distributions: Iterable[importlib.metadata.Distribution] | None = None,
) -> dict[str, str]:
    """Collect installed package names (normalized) and versions deterministically."""
    try:
        dist_iter = (
            distributions
            if distributions is not None
            else importlib.metadata.distributions()
        )
        packages: dict[str, str] = {}
        for dist in dist_iter:
            try:
                meta: Any = dist.metadata
                raw_name = meta["Name"] if meta is not None else None
                raw_version = getattr(dist, "version", None)
                if not raw_name and meta is not None:
                    raw_name = meta.get("Name")
                if not raw_version and meta is not None:
                    raw_version = meta.get("Version")
                if not isinstance(raw_name, str) or not raw_name.strip():
                    continue
                if not isinstance(raw_version, str) or not raw_version.strip():
                    continue
                norm_name = normalize_package_name(raw_name)
                packages[norm_name] = raw_version.strip()
            except Exception:
                # Ignore individual malformed distributions without failing collection
                continue
    except Exception as exc:
        raise CollectionError(f"Failed to collect installed packages: {exc}") from exc

    return dict(sorted(packages.items()))
