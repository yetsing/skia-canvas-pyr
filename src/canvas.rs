use crate::context::Context2D;
use crate::context::page::{ExportOptions, pages_arg};
use crate::gpu;
use crate::utils::*;
use pyo3::prelude::*;
use serde_json::json;
use skia_safe::SurfaceProps;

#[pyclass]
pub struct Canvas {
  pub width: f32,
  pub height: f32,
  pub text_contrast: f64,
  pub text_gamma: f64,
  pub gpu_disabled: bool,
  engine: Option<gpu::RenderingEngine>,
}

impl Canvas {
  pub fn new(text_contrast: f64, text_gamma: f64, gpu_disabled: bool) -> Self {
    Canvas {
      width: 300.0,
      height: 150.0,
      text_contrast,
      text_gamma,
      gpu_disabled,
      engine: None,
    }
  }

  pub fn engine(&mut self) -> gpu::RenderingEngine {
    *self
      .engine
      .get_or_insert_with(gpu::RenderingEngine::default)
  }

  pub fn export_options(&self) -> ExportOptions {
    ExportOptions {
      text_contrast: self.text_contrast as _,
      text_gamma: self.text_gamma as _,
      ..Default::default()
    }
  }
}

/* #region Python Methods */

#[pymethods]
impl Canvas {
  #[new]
  pub fn new_py(
    text_contrast: Option<f64>,
    text_gamma: Option<f64>,
    gpu_enabled: bool,
  ) -> PyResult<Self> {
    let text_contrast = opt_finite_float64(text_contrast, 0.0)?;
    let (min_c, max_c) = (
      SurfaceProps::MIN_CONTRAST_INCLUSIVE as _,
      SurfaceProps::MAX_CONTRAST_INCLUSIVE as _,
    );
    if text_contrast < min_c || text_contrast > max_c {
      return Err(pyo3::exceptions::PyValueError::new_err(format!(
        "Expected a number between {} and {} for `textContrast`",
        min_c, max_c
      )));
    }

    let mut text_gamma = opt_finite_float64(text_gamma, 1.4)?;
    let (min_g, max_g) = (
      SurfaceProps::MIN_GAMMA_INCLUSIVE as _,
      SurfaceProps::MAX_GAMMA_EXCLUSIVE as _,
    );
    if text_gamma == max_g {
      text_gamma -= f32::EPSILON as f64
    }; // nudge down values right at the max
    if text_gamma < min_g || text_gamma > max_g {
      return Err(pyo3::exceptions::PyValueError::new_err(format!(
        "Expected a number between {} and {} for `textGamma`",
        min_g, max_g
      )));
    }

    Ok(Self::new(text_contrast, text_gamma, !gpu_enabled))
  }

  pub fn get_width(&self) -> f32 {
    self.width
  }

  pub fn get_height(&self) -> f32 {
    self.height
  }

  pub fn set_width(&mut self, width: f32) -> PyResult<()> {
    finite_float(width)?;
    if width < 0.0 {
      return Err(pyo3::exceptions::PyValueError::new_err(
        "Width must be a non-negative number",
      ));
    }
    self.width = width;
    Ok(())
  }

  pub fn set_height(&mut self, height: f32) -> PyResult<()> {
    finite_float(height)?;
    if height < 0.0 {
      return Err(pyo3::exceptions::PyValueError::new_err(
        "Height must be a non-negative number",
      ));
    }
    self.height = height;
    Ok(())
  }

  pub fn get_engine(&mut self) -> String {
    from_engine(self.engine())
  }

  pub fn set_engine(&mut self, engine_name: String) {
    if let Some(new_engine) = to_engine(&engine_name)
      && new_engine.selectable()
    {
      self.gpu_disabled = matches!(new_engine, gpu::RenderingEngine::CPU);
      self.engine = Some(new_engine)
    }
  }

  pub fn get_engine_status(&mut self) -> String {
    let mut details = self.engine().status(self.gpu_disabled);
    details["textContrast"] = json!(self.text_contrast);
    details["textGamma"] = json!(self.text_gamma);
    details.to_string()
  }

  #[pyo3(name = "to_buffer_sync")]
  pub fn py_to_buffer_sync(
    &mut self,
    pages: Vec<PyRef<Context2D>>,
    options: ExportOptions,
  ) -> PyResult<Vec<u8>> {
    let pages = pages_arg(pages, &options, self)?;

    let encoded = {
      if options.format == "pdf" && pages.len() > 1 {
        pages.as_pdf(options)
      } else {
        pages.first().encoded_as(options, pages.engine)
      }
    };

    match encoded {
      Ok(data) => Ok(data),
      Err(e) => Err(pyo3::exceptions::PyRuntimeError::new_err(e)),
    }
  }

  pub fn save_sync(
    &mut self,
    pages: Vec<PyRef<Context2D>>,
    name_pattern: String,
    padding: Option<f32>,
    options: ExportOptions,
  ) -> PyResult<()> {
    let sequence = padding.is_some();
    let padding = opt_finite_float(padding, -1.0)?;
    let pages = pages_arg(pages, &options, self)?;

    let result = {
      if sequence {
        pages.write_sequence(&name_pattern, padding, options)
      } else if options.format == "pdf" {
        pages.write_pdf(&name_pattern, options)
      } else {
        pages.write_image(&name_pattern, options)
      }
    };

    match result {
      Ok(_) => Ok(()),
      Err(e) => Err(pyo3::exceptions::PyRuntimeError::new_err(e)),
    }
  }
}

/* #endregion */
