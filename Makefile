OS := $(shell uname -s)
.PHONY: dev

ifeq ($(OS),Darwin)
  CARGO_FEATURES = metal,window
else ifeq ($(OS),Linux)
  CARGO_FEATURES = vulkan,window,freetype
else ifeq ($(OS),Windows_NT)
  CARGO_FEATURES = vulkan,window
else
  CARGO_FEATURES = vulkan,window,freetype
endif


dev:
	maturin develop --features "$(CARGO_FEATURES)"

clippy:
	cargo clippy --features "$(CARGO_FEATURES)"

fmt:
	uvx black skia_canvas_pyr/ tests/

test:
	uv run pytest

visual:
	uv run python tests/visual/index.py

# linux-build helpers
skia-version:
	@grep -m 1 '^skia-safe' Cargo.toml | egrep -o '[0-9\.]+'

with-local-skia:
	echo '' >> Cargo.toml
	echo '[patch.crates-io]' >> Cargo.toml
	echo 'skia-safe = { path = "./rust-skia/skia-safe" }' >> Cargo.toml
	echo 'skia-bindings = { path = "./rust-skia/skia-bindings" }' >> Cargo.toml
