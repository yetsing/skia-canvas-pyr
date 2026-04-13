#!/bin/sh

set -eu

# Second install guarantees it's going to install from local dir w/ --no-index
# use first to get in dev dependencies
python -m pip install skia-canvas-pyr[dev] --pre --find-links dist --force-reinstall
python -m pip install skia-canvas-pyr --pre --no-index --find-links dist --force-reinstall

python -m pytest
