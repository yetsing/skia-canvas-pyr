use pyo3::prelude::*;

mod context;
mod filter;
mod gradient;
mod image;
mod path;
mod texture;
mod utils;

/// A Python module implemented in Rust.
#[pymodule]
mod skia_canvas_pyr {
  use pyo3::prelude::*;

  #[pymodule_export]
  use super::{gradient::CanvasGradient, path::Path2D, texture::CanvasTexture};

  /// Formats the sum of two numbers as string.
  #[pyfunction]
  fn sum_as_string(a: usize, b: usize) -> PyResult<String> {
    Ok((a + b).to_string())
  }
}
