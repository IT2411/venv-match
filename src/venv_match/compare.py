"""Deterministic comparison engine for environment snapshots."""

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from venv_match.exceptions import ComparisonError
from venv_match.rules import (
    SEVERITY_ORDER,
    VALID_SEVERITIES,
    Diagnostic,
    build_diagnostics_for_differences,
    classify_difference,
)
from venv_match.schema import KNOWN_SECTIONS, normalize_package_name
from venv_match.snapshot import Snapshot

CHANGE_TYPES: frozenset[str] = frozenset({"added", "removed", "changed", "unknown"})


@dataclass(frozen=True)
class Difference:
    """Representation of a single comparison finding between two snapshots."""

    path: str
    category: str
    change_type: str
    baseline: Any
    current: Any
    severity: str
    rule_ids: tuple[str, ...]
    explanation: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "category": self.category,
            "change_type": self.change_type,
            "baseline": self.baseline,
            "current": self.current,
            "severity": self.severity,
            "rule_ids": list(self.rule_ids),
            "explanation": self.explanation,
        }


@dataclass(frozen=True)
class ComparisonReport:
    """Structured report produced by comparing a baseline and current snapshot."""

    differences: tuple[Difference, ...]
    diagnostics: tuple[Diagnostic, ...]
    ignored_paths: tuple[str, ...]

    @property
    def has_differences(self) -> bool:
        """Return True if any non-unknown difference (added, removed, changed) was found."""
        return any(
            d.change_type in ("added", "removed", "changed") for d in self.differences
        )

    @property
    def has_unknowns(self) -> bool:
        """Return True if any section or field could not be reliably compared."""
        return any(d.change_type == "unknown" for d in self.differences)

    def meets_failure_threshold(
        self,
        *,
        fail_on_diff: bool = False,
        min_severity: str | None = None,
    ) -> bool:
        """Return True if the report meets the configured CI failure policy."""
        if min_severity is not None and min_severity not in VALID_SEVERITIES:
            raise ComparisonError(f"Invalid minimum severity '{min_severity}'.")

        if not fail_on_diff and min_severity is None:
            return False

        threshold_rank = SEVERITY_ORDER[min_severity] if min_severity is not None else 1
        for diff in self.differences:
            if diff.change_type not in ("added", "removed", "changed"):
                continue
            if SEVERITY_ORDER.get(diff.severity, 0) >= threshold_rank:
                return True
        return False

    def summary(self) -> str:
        """Return a concise human-readable summary of the comparison."""
        actionable = [
            d
            for d in self.differences
            if d.change_type in ("added", "removed", "changed")
        ]
        unknowns = [d for d in self.differences if d.change_type == "unknown"]

        if not actionable and not unknowns:
            return "No differences detected between baseline and current snapshots."

        counts_by_type = {"added": 0, "removed": 0, "changed": 0}
        for d in actionable:
            counts_by_type[d.change_type] += 1

        parts = [
            f"Detected {len(actionable)} difference(s) "
            f"(added: {counts_by_type['added']}, "
            f"removed: {counts_by_type['removed']}, "
            f"changed: {counts_by_type['changed']})"
        ]
        if unknowns:
            parts.append(f"{len(unknowns)} uncomparable section(s)/field(s)")
        return "; ".join(parts) + "."

    def to_dict(self) -> dict[str, Any]:
        """Serialize the comparison report into a deterministic dictionary."""
        actionable_count = sum(
            1
            for d in self.differences
            if d.change_type in ("added", "removed", "changed")
        )
        unknown_count = sum(1 for d in self.differences if d.change_type == "unknown")
        return {
            "has_differences": self.has_differences,
            "summary": self.summary(),
            "counts": {
                "differences": actionable_count,
                "unknown": unknown_count,
                "diagnostics": len(self.diagnostics),
                "ignored_paths": len(self.ignored_paths),
            },
            "ignored_paths": list(self.ignored_paths),
            "differences": [d.to_dict() for d in self.differences],
            "diagnostics": [diag.to_dict() for diag in self.diagnostics],
        }


def _validate_and_normalize_ignore_path(raw_ignore: str) -> str:
    """Validate that an ignore path targets a known section or field path."""
    if not isinstance(raw_ignore, str) or not raw_ignore.strip():
        raise ComparisonError("Ignore paths must be non-empty strings.")
    cleaned = raw_ignore.strip()
    parts = cleaned.split(".")
    if len(parts) < 2 or parts[0] != "sections" or parts[1] not in KNOWN_SECTIONS:
        valid_prefixes = ", ".join(f"sections.{s}" for s in KNOWN_SECTIONS)
        raise ComparisonError(
            f"Invalid ignore path '{cleaned}'. Ignore paths must start with one of: {valid_prefixes}."
        )
    if len(parts) >= 3 and parts[1] == "packages":
        pkg_part = ".".join(parts[2:])
        cleaned = f"sections.packages.{normalize_package_name(pkg_part)}"
    return cleaned


def _make_difference(
    path: str,
    category: str,
    change_type: str,
    baseline: Any,
    current: Any,
) -> Difference:
    severity, rule_ids, explanation = classify_difference(path, category, change_type)
    return Difference(
        path=path,
        category=category,
        change_type=change_type,
        baseline=baseline,
        current=current,
        severity=severity,
        rule_ids=rule_ids,
        explanation=explanation,
    )


def _compare_keyed_mapping(
    category: str,
    prefix: str,
    base_map: dict[str, Any],
    curr_map: dict[str, Any],
    ignored: set[str],
) -> list[Difference]:
    diffs: list[Difference] = []
    all_keys = sorted(set(base_map.keys()) | set(curr_map.keys()))
    for key in all_keys:
        path = f"{prefix}.{key}"
        if path in ignored:
            continue
        in_base = key in base_map
        in_curr = key in curr_map
        if in_base and not in_curr:
            diffs.append(
                _make_difference(path, category, "removed", base_map[key], None)
            )
        elif not in_base and in_curr:
            diffs.append(_make_difference(path, category, "added", None, curr_map[key]))
        else:
            b_val = base_map[key]
            c_val = curr_map[key]
            if (
                b_val is None
                and c_val is not None
                or b_val is not None
                and c_val is None
            ):
                if category in ("platform", "runtime"):
                    diffs.append(
                        _make_difference(path, category, "unknown", b_val, c_val)
                    )
                elif b_val != c_val:
                    diffs.append(
                        _make_difference(path, category, "changed", b_val, c_val)
                    )
            elif b_val != c_val:
                diffs.append(_make_difference(path, category, "changed", b_val, c_val))
    return diffs


def _compare_environment_section(
    base_env: dict[str, dict[str, Any]],
    curr_env: dict[str, dict[str, Any]],
    ignored: set[str],
) -> list[Difference]:
    diffs: list[Difference] = []
    all_vars = sorted(set(base_env.keys()) | set(curr_env.keys()))
    for var_name in all_vars:
        path = f"sections.environment.{var_name}"
        if path in ignored:
            continue
        in_base = var_name in base_env
        in_curr = var_name in curr_env
        if in_base and not in_curr:
            diffs.append(
                _make_difference(
                    path, "environment", "unknown", base_env[var_name], None
                )
            )
            continue
        if not in_base and in_curr:
            diffs.append(
                _make_difference(
                    path, "environment", "unknown", None, curr_env[var_name]
                )
            )
            continue

        b_entry = base_env[var_name]
        c_entry = curr_env[var_name]
        b_present = bool(b_entry.get("present"))
        c_present = bool(c_entry.get("present"))

        if b_present and not c_present:
            diffs.append(
                _make_difference(path, "environment", "removed", b_entry, c_entry)
            )
        elif not b_present and c_present:
            diffs.append(
                _make_difference(path, "environment", "added", b_entry, c_entry)
            )
        elif b_present and c_present:
            b_has_val = "value" in b_entry
            c_has_val = "value" in c_entry
            if b_has_val and c_has_val:
                if b_entry["value"] != c_entry["value"]:
                    diffs.append(
                        _make_difference(
                            path, "environment", "changed", b_entry, c_entry
                        )
                    )
            elif b_has_val != c_has_val:
                diffs.append(
                    _make_difference(path, "environment", "unknown", b_entry, c_entry)
                )
    return diffs


def compare(
    baseline: Snapshot,
    current: Snapshot,
    *,
    ignore_paths: Iterable[str] = (),
) -> ComparisonReport:
    """Compare two validated Snapshot instances and return a deterministic ComparisonReport."""
    if not isinstance(baseline, Snapshot) or not isinstance(current, Snapshot):
        raise ComparisonError("Both baseline and current must be Snapshot instances.")

    normalized_ignores: set[str] = {
        _validate_and_normalize_ignore_path(raw_ignore) for raw_ignore in ignore_paths
    }

    base_sections = baseline.sections
    curr_sections = current.sections
    base_completed = set(baseline.completed_sections)
    curr_completed = set(current.completed_sections)

    differences: list[Difference] = []

    for section_name in KNOWN_SECTIONS:
        sec_path = f"sections.{section_name}"
        if sec_path in normalized_ignores:
            continue

        b_ok = section_name in base_completed and section_name in base_sections
        c_ok = section_name in curr_completed and section_name in curr_sections

        if not b_ok and not c_ok:
            continue

        if b_ok != c_ok:
            differences.append(
                _make_difference(
                    sec_path,
                    section_name,
                    "unknown",
                    "collected" if b_ok else "uncollected",
                    "collected" if c_ok else "uncollected",
                )
            )
            continue

        b_sec = base_sections[section_name]
        c_sec = curr_sections[section_name]

        if section_name == "environment":
            differences.extend(
                _compare_environment_section(b_sec, c_sec, normalized_ignores)
            )
        else:
            differences.extend(
                _compare_keyed_mapping(
                    section_name, sec_path, b_sec, c_sec, normalized_ignores
                )
            )

    # Sort deterministically by (-severity_rank, path, change_type)
    differences.sort(
        key=lambda d: (
            -SEVERITY_ORDER.get(d.severity, 0),
            d.path,
            d.change_type,
        )
    )

    diagnostics = build_diagnostics_for_differences(differences)

    return ComparisonReport(
        differences=tuple(differences),
        diagnostics=tuple(diagnostics),
        ignored_paths=tuple(sorted(normalized_ignores)),
    )
