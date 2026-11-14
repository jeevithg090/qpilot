"""Allow ``python -m qpilot``."""

import sys

from qpilot.cli import main

if __name__ == "__main__":
    sys.exit(main())
