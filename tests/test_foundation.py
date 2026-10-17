"""Smoke tests for Phase 1 repository foundation."""

import venv_match
from venv_match.cli import EXIT_SUCCESS, main
from venv_match.exceptions import (
    CollectionError,
    ComparisonError,
    SnapshotFormatError,
    UnsupportedSchemaVersionError,
    VenvMatchError,
)


def test_version() -> None:
    assert venv_match.__version__ == "0.1.0"


def test_exception_hierarchy() -> None:
    assert issubclass(SnapshotFormatError, VenvMatchError)
    assert issubclass(UnsupportedSchemaVersionError, SnapshotFormatError)
    assert issubclass(CollectionError, VenvMatchError)
    assert issubclass(ComparisonError, VenvMatchError)


def test_cli_help_exits_zero() -> None:
    assert main(["--help"]) == EXIT_SUCCESS
