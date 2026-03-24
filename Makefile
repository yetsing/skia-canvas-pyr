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
	.venv/bin/pytest