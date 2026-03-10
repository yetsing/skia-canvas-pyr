.PHONY: dev

dev:
	maturin develop --features "vulkan,window,freetype"

clippy:
	cargo clippy --features "vulkan,window,freetype"
