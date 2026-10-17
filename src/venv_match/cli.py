"""Command-line interface entry point for Venv Match."""

from collections.abc import Sequence


def main(argv: Sequence[str] | None = None) -> int:
    """Run the venv-match CLI."""
    _ = argv
    return 0
