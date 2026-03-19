use pyo3::prelude::*;

mod canvas;
mod context;
mod filter;
mod font_library;
#[allow(clippy::all)]
mod gpu;
mod gradient;
#[cfg(feature = "window")]
mod gui;
mod image;
mod path;
mod pattern;
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
    gui::{activate, close, open, quit, register, set_mode, set_rate, wait_for_termination},
    image::Image,
    path::{Path2D, Path2DBounds},
    pattern::CanvasPattern,
    texture::CanvasTexture,
    typography::TypefaceDetails,
  };

  /// Formats the sum of two numbers as string.
  #[pyfunction]
  fn sum_as_string(a: usize, b: usize) -> PyResult<String> {
    Ok((a + b).to_string())
  }
}
