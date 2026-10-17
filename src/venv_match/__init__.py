"""Venv Match — Python environment comparison and diagnostic library."""

from venv_match.exceptions import (
    CollectionError,
    ComparisonError,
    SnapshotFormatError,
    UnsupportedSchemaVersionError,
    VenvMatchError,
)

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "VenvMatchError",
    "SnapshotFormatError",
    "UnsupportedSchemaVersionError",
    "CollectionError",
    "ComparisonError",
]
