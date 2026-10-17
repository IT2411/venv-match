"""Diagnostic rules and severity prioritization for environment differences."""

from dataclasses import dataclass
from typing import Any

SEVERITY_ORDER: dict[str, int] = {
    "low": 1,
    "medium": 2,
    "high": 3,
    "critical": 4,
}

VALID_SEVERITIES: frozenset[str] = frozenset(SEVERITY_ORDER.keys())


@dataclass(frozen=True)
class Diagnostic:
    """Structured diagnostic explanation for one or more observed differences."""

    rule_id: str
    severity: str
    message: str
    recommendation: str
    paths: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "severity": self.severity,
            "message": self.message,
            "recommendation": self.recommendation,
            "paths": list(self.paths),
        }


def classify_difference(
    path: str,
    category: str,
    change_type: str,
) -> tuple[str, tuple[str, ...], str]:
    """Return (severity, rule_ids, explanation) for an observed difference."""
    if change_type == "unknown":
        return (
            "low",
            (),
            f"Comparison for '{path}' is unavailable because data was not collected in both snapshots.",
        )

    if path in ("sections.python.version", "sections.python.version_info"):
        return (
            "high",
            ("PYTHON_VERSION_CHANGED",),
            "The Python interpreter version differs between environments, which may affect syntax, standard library behavior, or wheel selection.",
        )

    if path == "sections.python.implementation":
        return (
            "high",
            ("PYTHON_IMPLEMENTATION_CHANGED",),
            "The Python implementation differs (for example, CPython vs PyPy), which may affect C-extension compatibility and runtime behavior.",
        )

    if path in (
        "sections.python.executable",
        "sections.python.prefix",
        "sections.python.base_prefix",
    ):
        return (
            "low",
            ("INTERPRETER_PATH_CHANGED",),
            "An interpreter filesystem path differs. Path differences are normal across machines and usually contextual.",
        )

    if path == "sections.python.is_venv":
        return (
            "medium",
            ("INTERPRETER_PATH_CHANGED",),
            "Virtual environment isolation status ('is_venv') differs between snapshots.",
        )

    if category == "packages" and path.startswith("sections.packages."):
        pkg_name = path.removeprefix("sections.packages.")
        if change_type == "removed":
            return (
                "high",
                ("PACKAGE_MISSING",),
                f"Package '{pkg_name}' is present in the baseline snapshot but missing from the current snapshot.",
            )
        if change_type == "changed":
            return (
                "medium",
                ("PACKAGE_VERSION_CHANGED",),
                f"The installed version of package '{pkg_name}' differs between snapshots.",
            )
        if change_type == "added":
            return (
                "low",
                (),
                f"Package '{pkg_name}' is present only in the current snapshot.",
            )

    if category == "platform" and path.startswith("sections.platform."):
        field = path.removeprefix("sections.platform.")
        return (
            "medium",
            ("PLATFORM_CHANGED",),
            f"Platform attribute '{field}' differs, which may affect OS-specific behavior or native binaries.",
        )

    if path == "sections.runtime.timezone":
        return (
            "medium",
            ("TIMEZONE_CHANGED",),
            "Collected timezone information differs, which may affect naive datetime handling or timestamp formatting.",
        )

    if path == "sections.runtime.locale":
        return (
            "medium",
            ("LOCALE_CHANGED",),
            "Collected locale information differs, which may affect text encoding, sorting, or number formatting.",
        )

    if path == "sections.runtime.working_directory":
        return (
            "low",
            ("WORKING_DIRECTORY_CHANGED",),
            "The working directory differs. This is usually contextual unless the application relies on relative file paths.",
        )

    if category == "environment" and path.startswith("sections.environment."):
        var_name = path.removeprefix("sections.environment.")
        severity = "medium" if change_type in ("changed", "removed") else "low"
        return (
            severity,
            ("ENVIRONMENT_VARIABLE_CHANGED",),
            f"Allowlisted environment variable '{var_name}' differs between snapshots.",
        )

    return (
        "low",
        (),
        f"Field '{path}' differs between the baseline and current snapshots.",
    )


_RULE_METADATA: dict[str, tuple[str, str, str]] = {
    "PYTHON_VERSION_CHANGED": (
        "high",
        "Python runtime version differs between snapshots.",
        "Consider investigating whether language features, standard library changes, or compiled wheels differ across these Python versions.",
    ),
    "PYTHON_IMPLEMENTATION_CHANGED": (
        "high",
        "Python interpreter implementation differs between snapshots.",
        "Consider investigating whether C extensions or implementation-specific behaviors are affected.",
    ),
    "PACKAGE_MISSING": (
        "high",
        "One or more baseline packages are not installed in the current environment.",
        "Consider verifying whether the missing distributions are required by the application or its dependencies.",
    ),
    "PACKAGE_VERSION_CHANGED": (
        "medium",
        "One or more installed package versions differ between snapshots.",
        "Consider reviewing changelogs or lockfiles for the affected distributions if behavior diverged.",
    ),
    "PLATFORM_CHANGED": (
        "medium",
        "Operating system or machine architecture information differs.",
        "Consider investigating OS-specific code paths, filesystem semantics, or platform-specific wheels.",
    ),
    "TIMEZONE_CHANGED": (
        "medium",
        "Collected timezone context differs between environments.",
        "Consider checking whether the application depends on local system time or timezone environment variables.",
    ),
    "LOCALE_CHANGED": (
        "medium",
        "Collected locale context differs between environments.",
        "Consider checking default text encodings and locale-aware string operations.",
    ),
    "ENVIRONMENT_VARIABLE_CHANGED": (
        "medium",
        "One or more allowlisted environment variables differ in presence or value.",
        "Consider verifying configuration settings derived from the affected environment variables.",
    ),
    "WORKING_DIRECTORY_CHANGED": (
        "low",
        "Current working directory differs between snapshots.",
        "Usually expected across machines; consider investigating only if relative paths are used.",
    ),
    "INTERPRETER_PATH_CHANGED": (
        "low",
        "Python interpreter path or virtual environment location differs.",
        "Usually expected across machines; verify virtual environment activation if unexpected.",
    ),
}


def build_diagnostics_for_differences(
    differences: list[Any],
) -> list[Diagnostic]:
    """Aggregate triggered rules across differences into deterministic Diagnostic objects."""
    grouped_paths: dict[str, list[str]] = {}
    rule_max_severity: dict[str, str] = {}

    for diff in differences:
        for rule_id in diff.rule_ids:
            grouped_paths.setdefault(rule_id, []).append(diff.path)
            prev_sev = rule_max_severity.get(rule_id)
            if (
                prev_sev is None
                or SEVERITY_ORDER[diff.severity] > SEVERITY_ORDER[prev_sev]
            ):
                rule_max_severity[rule_id] = diff.severity

    diagnostics: list[Diagnostic] = []
    for rule_id, paths in grouped_paths.items():
        default_sev, msg, rec = _RULE_METADATA.get(
            rule_id,
            (
                "low",
                f"Diagnostic rule {rule_id} was triggered.",
                "Consider investigating the associated fields.",
            ),
        )
        sev = rule_max_severity.get(rule_id, default_sev)
        unique_sorted_paths = tuple(sorted(set(paths)))
        diagnostics.append(
            Diagnostic(
                rule_id=rule_id,
                severity=sev,
                message=msg,
                recommendation=rec,
                paths=unique_sorted_paths,
            )
        )

    diagnostics.sort(key=lambda d: (-SEVERITY_ORDER.get(d.severity, 0), d.rule_id))
    return diagnostics
