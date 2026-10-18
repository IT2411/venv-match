"""Venv Match — Python environment comparison and diagnostic library."""

from venv_match.compare import ComparisonReport, Difference, compare
from venv_match.config import CaptureConfig
from venv_match.exceptions import (
    CollectionError,
    ComparisonError,
    SnapshotFormatError,
    UnsupportedSchemaVersionError,
    VenvMatchError,
)
from venv_match.recreate import CreateVenvResult, create_venv, export_requirements
from venv_match.snapshot import Snapshot, capture, load_snapshot

__version__ = "0.2.0"

__all__ = [
    "__version__",
    "CaptureConfig",
    "ComparisonReport",
    "CreateVenvResult",
    "Difference",
    "Snapshot",
    "capture",
    "compare",
    "create_venv",
    "export_requirements",
    "load_snapshot",
    "VenvMatchError",
    "SnapshotFormatError",
    "UnsupportedSchemaVersionError",
    "CollectionError",
    "ComparisonError",
]
