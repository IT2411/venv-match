"""Allow running Venv Match via `python -m venv_match`."""

import sys

from venv_match.cli import main

if __name__ == "__main__":
    sys.exit(main())
