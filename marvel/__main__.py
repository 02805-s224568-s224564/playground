"""`python -m marvel`: fetch and verify the snapshot files, then print a summary."""

import sys

from .data import SnapshotError, _main

try:
    sys.exit(_main())
except SnapshotError as err:
    print(f"error: {err}", file=sys.stderr)
    sys.exit(1)
