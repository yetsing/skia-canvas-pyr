#!/usr/bin/env python3

import shutil
from pathlib import Path

script_dir = Path(__file__).parent.resolve()


def main():
    directory = script_dir / "skia_canvas_pyr"
    try:
        if directory.exists() and directory.is_dir():
            shutil.rmtree(directory)
        print(f"Directory '{directory}' and its contents have been removed.")
    except FileNotFoundError:
        print(f"Directory '{directory}' does not exist.")
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
