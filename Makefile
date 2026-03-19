.PHONY: dev

dev:
	maturin develop --features "vulkan,window,freetype"

clippy:
	cargo clippy --features "vulkan,window,freetype"

fmt:
	uvx black skia_canvas_pyr/ tests/
