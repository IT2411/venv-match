"""Command-line interface entry point for Venv Match."""

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import NoReturn

from venv_match.compare import compare
from venv_match.config import CaptureConfig
from venv_match.exceptions import (
    CollectionError,
    ComparisonError,
    SnapshotFormatError,
    UnsupportedSchemaVersionError,
)
from venv_match.recreate import create_venv, export_requirements
from venv_match.reporting import (
    format_comparison_json,
    format_comparison_text,
    format_inspection_text,
)
from venv_match.snapshot import PACKAGE_VERSION, capture, load_snapshot

EXIT_SUCCESS = 0
EXIT_DIFF_THRESHOLD_MET = 1
EXIT_USAGE_ERROR = 2
EXIT_SNAPSHOT_LOAD_ERROR = 3
EXIT_COLLECTION_OR_IO_ERROR = 4
EXIT_UNSUPPORTED_SCHEMA = 5


class _CliArgumentParser(argparse.ArgumentParser):
    """ArgumentParser that consistently raises SystemExit(2) on invalid arguments."""

    def error(self, message: str) -> NoReturn:
        self.print_usage(sys.stderr)
        sys.stderr.write(f"{self.prog}: error: {message}\n")
        raise SystemExit(EXIT_USAGE_ERROR)


def _build_parser() -> _CliArgumentParser:
    parser = _CliArgumentParser(
        prog="venv-match",
        description="Capture, inspect, compare, and recreate Python runtime environment snapshots.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {PACKAGE_VERSION}",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # capture subcommand
    capture_parser = subparsers.add_parser(
        "capture",
        help="Capture the current Python environment and write a JSON snapshot.",
    )
    capture_parser.add_argument(
        "--output",
        "-o",
        required=True,
        help="Path to write the output snapshot JSON file.",
    )
    pkg_group = capture_parser.add_mutually_exclusive_group()
    pkg_group.add_argument(
        "--include-packages",
        dest="include_packages",
        action="store_true",
        default=True,
        help="Include installed package versions in the snapshot (default).",
    )
    pkg_group.add_argument(
        "--no-packages",
        dest="include_packages",
        action="store_false",
        help="Do not collect installed package versions.",
    )
    capture_parser.add_argument(
        "--env",
        dest="env_vars",
        action="append",
        default=[],
        metavar="NAME",
        help="Allowlist an environment variable name to record (repeatable).",
    )
    capture_parser.add_argument(
        "--env-values",
        dest="include_env_values",
        action="store_true",
        default=False,
        help="Record values for allowlisted non-secret environment variables.",
    )
    capture_parser.add_argument(
        "--overwrite",
        action="store_true",
        default=False,
        help="Allow overwriting an existing output file.",
    )

    # compare subcommand
    compare_parser = subparsers.add_parser(
        "compare",
        help="Compare a baseline snapshot against a current snapshot.",
    )
    compare_parser.add_argument(
        "baseline",
        help="Path to the baseline snapshot JSON file.",
    )
    compare_parser.add_argument(
        "current",
        help="Path to the current snapshot JSON file.",
    )
    compare_parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output report format (default: text).",
    )
    compare_parser.add_argument(
        "--fail-on-diff",
        action="store_true",
        default=False,
        help="Return exit code 1 if any non-ignored difference is detected.",
    )
    compare_parser.add_argument(
        "--min-severity",
        choices=("low", "medium", "high", "critical"),
        default=None,
        help="Return exit code 1 if any non-ignored difference meets or exceeds this severity.",
    )
    compare_parser.add_argument(
        "--ignore",
        dest="ignore_paths",
        action="append",
        default=[],
        metavar="PATH",
        help="Exact field path to exclude from comparison (repeatable).",
    )

    # inspect subcommand
    inspect_parser = subparsers.add_parser(
        "inspect",
        help="Display metadata and a readable summary of a snapshot file.",
    )
    inspect_parser.add_argument(
        "snapshot",
        help="Path to the snapshot JSON file to inspect.",
    )

    # export subcommand
    export_parser = subparsers.add_parser(
        "export",
        help="Export pinned requirements (package==version) from a snapshot.",
    )
    export_parser.add_argument(
        "snapshot",
        help="Path to the snapshot JSON file.",
    )
    export_parser.add_argument(
        "--output",
        "-o",
        default=None,
        help="Optional path to write requirements.txt (prints to stdout if omitted).",
    )
    export_parser.add_argument(
        "--include-build-tools",
        action="store_true",
        default=False,
        help="Include pip, setuptools, and wheel in the exported requirements.",
    )
    export_parser.add_argument(
        "--overwrite",
        action="store_true",
        default=False,
        help="Allow overwriting an existing output file.",
    )

    # create subcommand
    create_parser = subparsers.add_parser(
        "create",
        help="Create a virtual environment and install packages from a snapshot.",
    )
    create_parser.add_argument(
        "snapshot",
        help="Path to the snapshot JSON file.",
    )
    create_parser.add_argument(
        "--target",
        "-t",
        default=".venv",
        help="Target directory for the new virtual environment (default: .venv).",
    )
    create_parser.add_argument(
        "--python",
        "-p",
        default=None,
        help="Python interpreter executable to use (defaults to current interpreter).",
    )
    create_parser.add_argument(
        "--include-build-tools",
        action="store_true",
        default=False,
        help="Also install pip, setuptools, and wheel versions from the snapshot.",
    )
    create_parser.add_argument(
        "--overwrite",
        action="store_true",
        default=False,
        help="Allow replacing an existing target directory.",
    )
    create_parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Preview virtual environment creation and package installation without modifying disk.",
    )

    return parser


def _handle_capture(args: argparse.Namespace) -> int:
    output_path = Path(args.output)
    if output_path.exists() and not args.overwrite:
        sys.stderr.write(
            f"Error: Output file '{output_path}' already exists. "
            "Use --overwrite to replace it.\n"
        )
        return EXIT_COLLECTION_OR_IO_ERROR

    if args.include_env_values and args.env_vars:
        sys.stderr.write(
            "Warning: --env-values is enabled. Values for allowlisted non-secret "
            "environment variables will be recorded in the snapshot.\n"
        )

    config = CaptureConfig(
        include_packages=bool(args.include_packages),
        env_vars=tuple(args.env_vars),
        include_env_values=bool(args.include_env_values),
    )
    snapshot = capture(config)
    snapshot.save(output_path, overwrite=bool(args.overwrite))
    sys.stdout.write(f"Snapshot saved to {output_path}\n")
    return EXIT_SUCCESS


def _handle_compare(args: argparse.Namespace) -> int:
    baseline = load_snapshot(args.baseline)
    current = load_snapshot(args.current)

    report = compare(
        baseline,
        current,
        ignore_paths=tuple(args.ignore_paths),
    )

    if args.format == "json":
        sys.stdout.write(format_comparison_json(report))
    else:
        sys.stdout.write(format_comparison_text(report))

    if report.meets_failure_threshold(
        fail_on_diff=bool(args.fail_on_diff),
        min_severity=args.min_severity,
    ):
        return EXIT_DIFF_THRESHOLD_MET

    return EXIT_SUCCESS


def _handle_inspect(args: argparse.Namespace) -> int:
    snapshot = load_snapshot(args.snapshot)
    sys.stdout.write(format_inspection_text(snapshot))
    return EXIT_SUCCESS


def _handle_export(args: argparse.Namespace) -> int:
    snapshot = load_snapshot(args.snapshot)
    specs = export_requirements(
        snapshot, include_build_tools=bool(args.include_build_tools)
    )
    content = "\n".join(specs) + ("\n" if specs else "")

    if args.output is not None:
        out_path = Path(args.output)
        if out_path.exists() and not args.overwrite:
            sys.stderr.write(
                f"Error: Output file '{out_path}' already exists. "
                "Use --overwrite to replace it.\n"
            )
            return EXIT_COLLECTION_OR_IO_ERROR
        try:
            out_path.write_text(content, encoding="utf-8")
        except OSError as exc:
            sys.stderr.write(f"Error: Failed to write '{out_path}': {exc}\n")
            return EXIT_COLLECTION_OR_IO_ERROR
        sys.stdout.write(
            f"Exported {len(specs)} package requirement(s) to {out_path}\n"
        )
    else:
        sys.stdout.write(content)

    return EXIT_SUCCESS


def _handle_create(args: argparse.Namespace) -> int:
    snapshot = load_snapshot(args.snapshot)
    result = create_venv(
        snapshot,
        args.target,
        python_executable=args.python,
        include_build_tools=bool(args.include_build_tools),
        overwrite=bool(args.overwrite),
        dry_run=bool(args.dry_run),
    )

    if result.python_version_warning:
        sys.stderr.write(f"Warning: {result.python_version_warning}\n")

    if result.dry_run:
        sys.stdout.write(
            f"[Dry Run] Would create virtual environment at '{result.target_dir}' "
            f"using '{result.python_executable}'\n"
        )
        sys.stdout.write(
            f"[Dry Run] Would install {len(result.installed_packages)} package(s)"
        )
        if result.installed_packages:
            sys.stdout.write(": " + ", ".join(result.installed_packages) + "\n")
        else:
            sys.stdout.write(".\n")
    else:
        sys.stdout.write(
            f"Created virtual environment at '{result.target_dir}' "
            f"and installed {len(result.installed_packages)} package(s).\n"
        )

    return EXIT_SUCCESS


def main(argv: Sequence[str] | None = None) -> int:
    """Run the venv-match CLI and return a documented exit code."""
    parser = _build_parser()
    try:
        parsed_args = parser.parse_args(list(argv) if argv is not None else None)
    except SystemExit as exc:
        code = exc.code
        return int(code) if isinstance(code, int) else EXIT_USAGE_ERROR

    try:
        if parsed_args.command == "capture":
            return _handle_capture(parsed_args)
        if parsed_args.command == "compare":
            return _handle_compare(parsed_args)
        if parsed_args.command == "inspect":
            return _handle_inspect(parsed_args)
        if parsed_args.command == "export":
            return _handle_export(parsed_args)
        if parsed_args.command == "create":
            return _handle_create(parsed_args)
    except UnsupportedSchemaVersionError as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return EXIT_UNSUPPORTED_SCHEMA
    except SnapshotFormatError as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return EXIT_SNAPSHOT_LOAD_ERROR
    except CollectionError as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return EXIT_COLLECTION_OR_IO_ERROR
    except ComparisonError as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return EXIT_USAGE_ERROR

    return EXIT_USAGE_ERROR
