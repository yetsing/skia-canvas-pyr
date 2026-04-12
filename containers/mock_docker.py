#!/usr/bin/env python3
"""
A fake docker entrypoint for testing the CI workflow without building the actual docker image.
"""

import os
import sys
from pathlib import Path


MAX_LINE = int(os.environ.get("MAX_LINE", 100))


def can_print(path: Path) -> bool:
    if not path.exists() or path.is_dir():
        return True

    try:
        with path.open(encoding="utf-8") as f:
            for i, _ in enumerate(f):
                if i >= MAX_LINE:
                    return False
    except Exception:
        return False

    return True


def main():
    print(sys.argv)
    for arg in sys.argv[1:]:
        path = Path(arg)
        if can_print(path):
            print(f"--- {path} ---")
            print(path.read_text(encoding="utf-8"))

    sys.exit(1)


if __name__ == "__main__":
    main()
