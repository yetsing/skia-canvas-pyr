#!/usr/bin/env python3
"""
A fake docker entrypoint for testing the CI workflow without building the actual docker image.
"""

import os
import platform
import shutil
import sys
from pathlib import Path


script_dir = Path(__file__).parent.resolve()
MAX_LINE = int(os.environ.get("MAX_LINE", 100))


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
    print(sys.argv)
    for arg in sys.argv[1:]:
        path = Path(arg)
        if can_print(path):
            print(f"--- {path} ---")
            print(path.read_text(encoding="utf-8"))

    action = sys.argv[1]
    if action == "run":
        sys.exit(1)

    path = os.environ.get("PATH", None)
    if path:
        parts = path.split(os.pathsep)
        if str(script_dir) in parts:
            parts.remove(str(script_dir))
            path = os.pathsep.join(parts)
    docker = shutil.which("docker", path=path)  # 确保 docker 在 PATH 中
    assert docker, "Docker executable not found in PATH"
    os.execv(docker, [docker] + sys.argv[1:])


if __name__ == "__main__":
    main()
