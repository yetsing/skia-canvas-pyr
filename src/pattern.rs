use pyo3::prelude::*;
use skia_safe::{FilterMode, Matrix, Rect, Shader, Size, TileMode};
use std::cell::RefCell;
use std::rc::Rc;

use crate::context::Context2D;
use crate::filter::ImageFilter;
use crate::image::{Content, Image, ImageData};
use crate::utils::*;

pub struct Stamp {
  content: Content,
  dims: Size,
  repeat: (TileMode, TileMode),
  matrix: Matrix,
}

#[pyclass(unsendable, skip_from_py_object)]
#[derive(Clone)]
pub struct CanvasPattern {
  pub stamp: Rc<RefCell<Stamp>>,
}

impl CanvasPattern {
  pub fn shader(&self, image_filter: ImageFilter) -> Option<Shader> {
    let stamp = self.stamp.borrow();

    match &stamp.content {
      Content::Bitmap(image) => image
        .to_shader(stamp.repeat, image_filter.sampling(), None)
        .map(|shader| shader.with_local_matrix(&stamp.matrix)),
      Content::Vector(pict, ..) => {
        let tile_rect = Rect::from_size(stamp.dims);
        let shader = pict.to_shader(stamp.repeat, FilterMode::Linear, None, Some(&tile_rect));
        Some(shader.with_local_matrix(&stamp.matrix))
      }
      _ => None,
    }
  }

  pub fn is_opaque(&self) -> bool {
    let stamp = self.stamp.borrow();

    match &stamp.content {
      Content::Bitmap(image) => image.is_opaque(),
      _ => false,
    }
  }
}

/* #region Python Methods */

#[pymethods]
impl CanvasPattern {
  #[staticmethod]
  pub fn from_image(
    src: &Image,
    canvas_width: f32,
    canvas_height: f32,
    repetition: Option<String>,
  ) -> PyResult<Self> {
    let repetition = repetition.unwrap_or_default();
    let repeat = match to_repeat_mode(&repetition) {
      Some(mode) => mode,
      None => {
        return Err(pyo3::exceptions::PyValueError::new_err(format!(
          "Invalid repetition mode: {}",
          repetition
        )));
      }
    };

    let content = src.content.clone();
    let dims = src.content.size();
    let mut matrix = Matrix::new_identity();

    if src.autosized && !dims.is_empty() {
      // If this flag is set (for SVG images with no intrinsic size) then we need to scale the image to
      // the canvas' smallest dimension. This preserves compatibility with how Chromium browsers behave.
      let min_size = f32::min(canvas_width, canvas_height);
      let factor = (min_size / dims.width, min_size / dims.height);
      matrix.set_scale(factor, None);
    }

    let stamp = Stamp {
      content,
      dims,
      repeat,
      matrix,
    };
    let canvas_pattern = CanvasPattern {
      stamp: Rc::new(RefCell::new(stamp)),
    };
    Ok(canvas_pattern)
  }

  #[staticmethod]
  pub fn from_image_data(src: ImageData, repetition: Option<String>) -> PyResult<Self> {
    let repetition = repetition.unwrap_or_default();
    let repeat = match to_repeat_mode(&repetition) {
      Some(mode) => mode,
      None => {
        return Err(pyo3::exceptions::PyValueError::new_err(format!(
          "Invalid repetition mode: {}",
          repetition
        )));
      }
    };

    let content = Content::from_image_data(src);
    let dims: Size = content.size();
    let matrix = Matrix::new_identity();

    let stamp = Stamp {
      content,
      dims,
      repeat,
      matrix,
    };
    let canvas_pattern = CanvasPattern {
      stamp: Rc::new(RefCell::new(stamp)),
    };

    Ok(canvas_pattern)
  }

  // TODO from_canvas
  #[staticmethod]
  pub fn from_canvas(src: &mut Context2D, repetition: Option<String>) -> PyResult<Self> {
    let repetition = repetition.unwrap_or_default();
    let repeat = match to_repeat_mode(&repetition) {
      Some(mode) => mode,
      None => {
        return Err(pyo3::exceptions::PyValueError::new_err(format!(
          "Invalid repetition mode: {}",
          repetition
        )));
      }
    };

    let dims = src.bounds.size();
    let matrix = Matrix::new_identity();
    let content = src
      .get_picture()
      .map(|picture| Content::Vector(picture, dims))
      .unwrap_or_default();

    let stamp = Stamp {
      content,
      dims,
      repeat,
      matrix,
    };
    let canvas_pattern = CanvasPattern {
      stamp: Rc::new(RefCell::new(stamp)),
    };

    Ok(canvas_pattern)
  }

  pub fn set_transform(&mut self, matrix: Vec<f32>) -> PyResult<()> {
    finite_floats(&matrix)?;
    let matrix = match to_matrix(&matrix) {
      Some(m) => m,
      None => {
        return Err(pyo3::exceptions::PyValueError::new_err(format!(
          "Invalid transformation matrix: expected 6 or 9 elements, got {}",
          matrix.len(),
        )));
      }
    };
    let mut stamp = self.stamp.borrow_mut();
    stamp.matrix = matrix;
    Ok(())
  }

  pub fn repr(&self) -> String {
    let stamp = self.stamp.borrow();
    let style = match stamp.content {
      Content::Bitmap(..) => "Bitmap",
      _ => "Canvas",
    };

    format!("{} {}×{}", style, stamp.dims.width, stamp.dims.height)
  }
}

/* #endregion */
