#!/bin/bash

set -euo pipefail

export TAG=$(make -s skia-version)
git clone --depth 1 --branch $TAG --recurse-submodules -j8 https://github.com/rust-skia/rust-skia.git
patch -d rust-skia -p1 -F10 < ./containers/use-static-fontconfig.patch

make -s with-local-skia

rustup install
rustup target add "${target_triple}"
maturin build -i "/usr/bin/python${python_version}" --target "${target_triple}" --release --out dist --compatibility pypi --features "${cargo_features}"
