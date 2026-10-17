"""Terminal and JSON report formatting with privacy and redaction enforcement."""

import copy
import json
from typing import Any

from venv_match.collectors.environment import is_secret_variable_name
from venv_match.compare import ComparisonReport, Difference
from venv_match.snapshot import Snapshot

REDACTED_PLACEHOLDER = "<redacted>"


def _sanitize_env_entry(
    var_name: str,
    entry: Any,
    *,
    redact_all_values: bool = False,
) -> Any:
    if not isinstance(entry, dict):
        return entry
    sanitized = copy.deepcopy(entry)
    if (
        "value" in sanitized
        and sanitized["value"] is not None
        and (redact_all_values or is_secret_variable_name(var_name))
    ):
        sanitized["value"] = REDACTED_PLACEHOLDER
    return sanitized


def _sanitize_difference_dict(
    diff_dict: dict[str, Any],
    *,
    redact_all_env_values: bool = False,
) -> dict[str, Any]:
    out = copy.deepcopy(diff_dict)
    path = str(out.get("path", ""))
    if path.startswith("sections.environment."):
        var_name = path.removeprefix("sections.environment.")
        out["baseline"] = _sanitize_env_entry(
            var_name,
            out.get("baseline"),
            redact_all_values=redact_all_env_values,
        )
        out["current"] = _sanitize_env_entry(
            var_name,
            out.get("current"),
            redact_all_values=redact_all_env_values,
        )
    return out


def redact_report_dict(
    report: ComparisonReport,
    *,
    redact_all_env_values: bool = False,
) -> dict[str, Any]:
    """Return a JSON-serializable report dictionary with privacy redaction applied."""
    raw = report.to_dict()
    raw["differences"] = [
        _sanitize_difference_dict(d, redact_all_env_values=redact_all_env_values)
        for d in raw["differences"]
    ]
    return raw


def format_comparison_json(
    report: ComparisonReport,
    *,
    redact_all_env_values: bool = False,
) -> str:
    """Format a ComparisonReport as deterministic, privacy-redacted UTF-8 JSON."""
    sanitized = redact_report_dict(report, redact_all_env_values=redact_all_env_values)
    return json.dumps(sanitized, indent=2, sort_keys=False) + "\n"


def _format_value_for_text(
    diff: Difference,
    side_value: Any,
    *,
    redact_all_env_values: bool = False,
) -> str:
    if diff.path.startswith("sections.environment.") and isinstance(side_value, dict):
        var_name = diff.path.removeprefix("sections.environment.")
        sanitized = _sanitize_env_entry(
            var_name, side_value, redact_all_values=redact_all_env_values
        )
        present = bool(sanitized.get("present"))
        if not present:
            return "absent"
        if "value" in sanitized and sanitized["value"] is not None:
            return f"present (value={json.dumps(sanitized['value'])})"
        return "present"
    if side_value is None:
        return "<none>"
    if isinstance(side_value, str):
        return side_value
    return json.dumps(side_value)


def format_comparison_text(
    report: ComparisonReport,
    *,
    redact_all_env_values: bool = False,
) -> str:
    """Format a ComparisonReport into a human-readable terminal report."""
    lines: list[str] = [
        "Venv Match Comparison Report",
        "============================",
        f"Summary: {report.summary()}",
    ]

    if report.ignored_paths:
        lines.append(
            f"Ignored paths ({len(report.ignored_paths)}): {', '.join(report.ignored_paths)}"
        )

    if report.diagnostics:
        lines.append("")
        lines.append("Diagnostics (Prioritized for Investigation):")
        for diag in report.diagnostics:
            lines.append(
                f"  - [{diag.severity.upper()}] {diag.rule_id}: {diag.message}"
            )
            lines.append(f"    Next step: {diag.recommendation}")
            lines.append(f"    Triggered by: {', '.join(diag.paths)}")

    if report.differences:
        lines.append("")
        lines.append("Observed Differences:")
        for diff in report.differences:
            b_str = _format_value_for_text(
                diff, diff.baseline, redact_all_env_values=redact_all_env_values
            )
            c_str = _format_value_for_text(
                diff, diff.current, redact_all_env_values=redact_all_env_values
            )
            lines.append(
                f"  - [{diff.severity.upper()}] {diff.path} ({diff.change_type}): "
                f"{b_str} -> {c_str}"
            )
            lines.append(f"    Note: {diff.explanation}")

    return "\n".join(lines) + "\n"


def format_inspection_text(
    snapshot: Snapshot,
    *,
    redact_all_env_values: bool = False,
) -> str:
    """Format a Snapshot into a human-readable inspection summary."""
    sections = snapshot.sections
    lines: list[str] = [
        "Venv Match Snapshot Inspection",
        "==============================",
        f"Schema version:     {snapshot.schema_version}",
        f"Venv Match version: {snapshot.venv_match_version}",
        f"Captured at:        {snapshot.captured_at}",
        f"Completed sections: {', '.join(snapshot.completed_sections)}",
    ]

    if snapshot.collection_errors:
        lines.append(f"Collection errors:  {len(snapshot.collection_errors)}")
        for err in snapshot.collection_errors:
            lines.append(f"  - {err['section']}: {err['message']}")

    py_sec = sections.get("python", {})
    lines.extend(
        [
            "",
            "Python:",
            f"  Implementation: {py_sec.get('implementation')}",
            f"  Version:        {py_sec.get('version')}",
            f"  Executable:     {py_sec.get('executable')}",
            f"  Virtualenv:     {py_sec.get('is_venv')}",
        ]
    )

    if "platform" in sections:
        plat = sections["platform"]
        lines.extend(
            [
                "",
                "Platform:",
                f"  System:         {plat.get('system')}",
                f"  Release:        {plat.get('release')}",
                f"  Machine:        {plat.get('machine')}",
            ]
        )

    if "packages" in sections:
        pkgs = sections["packages"]
        lines.append("")
        lines.append(f"Packages ({len(pkgs)} installed):")
        for pkg_name, pkg_ver in pkgs.items():
            lines.append(f"  - {pkg_name}=={pkg_ver}")

    if "runtime" in sections:
        rt = sections["runtime"]
        lines.extend(
            [
                "",
                "Runtime:",
                f"  Working dir:    {rt.get('working_directory')}",
                f"  Timezone:       {rt.get('timezone')}",
                f"  Locale:         {rt.get('locale')}",
            ]
        )

    if "environment" in sections:
        env = sections["environment"]
        lines.append("")
        lines.append(f"Environment Variables ({len(env)} tracked):")
        for var_name, entry in env.items():
            sanitized = _sanitize_env_entry(
                var_name, entry, redact_all_values=redact_all_env_values
            )
            present = bool(sanitized.get("present"))
            if not present:
                status = "absent"
            elif "value" in sanitized and sanitized["value"] is not None:
                status = f"present (value={json.dumps(sanitized['value'])})"
            else:
                status = "present"
            lines.append(f"  - {var_name}: {status}")

    return "\n".join(lines) + "\n"
