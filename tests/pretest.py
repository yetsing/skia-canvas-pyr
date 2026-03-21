"""
初始化工作如下：

    - 下载 skia-canvas 仓库里面的 tests/assets 目录放到当前项目的 tests 目录下，skia-canvas 相关信息在 pyproject.toml
"""

from __future__ import annotations

import argparse
import shutil
import tempfile
import urllib.request
import zipfile
from pathlib import Path

try:
    import tomllib as _toml_read  # Python 3.11+
except ModuleNotFoundError:
    import tomli as _toml_read  # pip install tomli


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _load_upstream() -> tuple[str, str]:
    pyproject = _repo_root() / "pyproject.toml"
    data = _toml_read.loads(pyproject.read_text(encoding="utf-8"))
    try:
        upstream = data["tool"]["skia_canvas_pyr"]["upstream"]
        return str(upstream["url"]), str(upstream["commit"])
    except Exception as exc:
        raise RuntimeError("Missing upstream url/commit in pyproject.toml") from exc


def _archive_url(repo_url: str, commit: str) -> str:
    # Convert the repository URL to GitHub's zip archive endpoint.
    normalized = repo_url.rstrip("/")
    if normalized.endswith(".git"):
        normalized = normalized[:-4]
    if not normalized.startswith("https://github.com/"):
        raise ValueError(f"Unsupported upstream url: {repo_url}")
    return f"{normalized}/archive/{commit}.zip"


def _extract_assets(zip_path: Path, target_dir: Path, force: bool = False) -> None:
    with zipfile.ZipFile(zip_path) as zf:
        members = [m for m in zf.namelist() if "/tests/assets/" in m]
        if not members:
            raise RuntimeError("tests/assets was not found in upstream archive")

        root_prefix = members[0].split("/", 1)[0]
        src_prefix = f"{root_prefix}/tests/assets/"

        if target_dir.exists() and force:
            shutil.rmtree(target_dir)
        target_dir.mkdir(parents=True, exist_ok=True)

        for name in members:
            if not name.startswith(src_prefix) or name.endswith("/"):
                continue
            rel = name[len(src_prefix) :]
            out_file = target_dir / rel
            out_file.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(name) as src, out_file.open("wb") as dst:
                shutil.copyfileobj(src, dst)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download upstream skia-canvas tests/assets into local tests/assets."
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Replace existing tests/assets before downloading.",
    )
    args = parser.parse_args()

    repo_url, commit = _load_upstream()
    url = _archive_url(repo_url, commit)

    tests_dir = _repo_root() / "tests"
    assets_dir = tests_dir / "assets"

    if assets_dir.exists() and not args.force:
        print(f"Skip: {assets_dir} already exists (use --force to refresh)")
        return

    with tempfile.TemporaryDirectory(prefix="skia-canvas-assets-") as tmp:
        archive = Path(tmp) / f"{commit}.zip"
        print(f"Downloading {url}")
        urllib.request.urlretrieve(url, archive)
        _extract_assets(archive, assets_dir, force=args.force)

    print(f"Prepared assets at {assets_dir}")


if __name__ == "__main__":
    main()
