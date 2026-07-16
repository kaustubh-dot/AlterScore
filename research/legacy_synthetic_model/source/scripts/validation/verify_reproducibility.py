"""Archived research-era validation entrypoint.

This module is retained only as an archive marker. It is not a production
release check and must not be used as evidence for the public v2 scorer.
"""

from __future__ import annotations

import sys


def main() -> int:
    print(
        "Archived: use AlterScore CI, the backend pytest suite, and "
        "scripts/ci/smoke_release.py for bounded release verification."
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
