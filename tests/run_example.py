"""
Open README.md and execute python code blocks.
"""

import re
import os
import tempfile
from pathlib import Path


def extract_python_code_blocks(text):
    pattern = re.compile(r"```python(.*?)```", re.DOTALL)
    return [block.strip() for block in pattern.findall(text)]


def main():
    script_path = Path(__file__).resolve()
    readme_path = script_path.parent.parent / "README.md"
    with readme_path.open(encoding="utf-8") as f:
        content = f.read()
    code_blocks = extract_python_code_blocks(content)
    if not code_blocks:
        print("No Python code blocks found in README.md.")
        return
    with tempfile.TemporaryDirectory() as tmp_dir:
        for i, code in enumerate(code_blocks, 1):
            print(f"\n--- Executing code block #{i} ---")
            exec_globals = {"__name__": "__main__", "__file__": str(readme_path)}
            cwd_before = Path.cwd()
            try:
                os.chdir(tmp_dir)
                exec(code, exec_globals)
            finally:
                os.chdir(cwd_before)


if __name__ == "__main__":
    main()
