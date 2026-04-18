#!/bin/bash

set -euo pipefail

uv sync --only-dev
uv pip install skia-canvas-pyr --prerelease allow --no-index --find-links dist --reinstall
uv run pytest
