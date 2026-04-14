#!/usr/bin/env python3
"""
A fake docker entrypoint for testing the CI workflow without building the actual docker image.
"""

import os
import platform
import sys
from pathlib import Path


script_dir = Path(__file__).parent.resolve()
MAX_LINE = int(os.environ.get("MAX_LINE", 100))
DOCKER_CMD = "{{DOCKER_CMD}}"


def can_print(path: Path) -> bool:
    if not path.exists() or path.is_dir():
        return False

    try:
        with path.open(encoding="utf-8") as f:
            for i, _ in enumerate(f):
                if i >= MAX_LINE:
                    return False
    except Exception:
        return False

    return True


def main():
    if platform.system() != "Linux":
        print("This script is only intended to run on Linux systems.")
        sys.exit(1)
    for arg in sys.argv[1:]:
        path = Path(arg)
        if can_print(path):
            print(f"--- {path} ---")
            print(path.read_text(encoding="utf-8"))

    sys.stdout.flush()
    sys.stderr.flush()

    docker = DOCKER_CMD
    os.execv(docker, [docker] + sys.argv[1:])


if __name__ == "__main__":
    main()
