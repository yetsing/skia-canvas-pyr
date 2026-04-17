#!/bin/bash

set -euo pipefail

cat /opt/commit_id.txt

export TAG=$(make -s skia-version)
git clone --depth 1 --branch $TAG --recurse-submodules -j8 https://github.com/rust-skia/rust-skia.git ../rust-skia
patch -d ../rust-skia -p1 -F10 < ./containers/use-static-fontconfig.patch

make -s with-local-skia
