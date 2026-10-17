"""Exception hierarchy for Venv Match."""


class VenvMatchError(Exception):
    """Base exception for all Venv Match errors."""


class SnapshotFormatError(VenvMatchError):
    """Raised when a snapshot fails validation, parsing, or schema checks."""


class CollectionError(VenvMatchError):
    """Raised when a required environment collection or I/O operation fails."""


class ComparisonError(VenvMatchError):
    """Raised when snapshots cannot be compared."""
