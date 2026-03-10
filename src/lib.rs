use pyo3::prelude::*;

mod context;
mod filter;
mod font_library;
mod gradient;
mod image;
mod path;
mod texture;
mod typography;
mod utils;

/// A Python module implemented in Rust.
#[pymodule]
mod skia_canvas_pyr {
  use pyo3::prelude::*;

  #[pymodule_export]
  use super::{
    font_library::{FamilyDetails, add_family, family, get_families, has, reset},
    gradient::CanvasGradient,
    path::Path2D,
    texture::CanvasTexture,
    typography::TypefaceDetails,
  };

  /// Formats the sum of two numbers as string.
  #[pyfunction]
  fn sum_as_string(a: usize, b: usize) -> PyResult<String> {
    Ok((a + b).to_string())
  }
}
