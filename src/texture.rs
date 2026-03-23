use pyo3::prelude::*;
use skia_safe::{Color, Color4f, Matrix, Paint, PaintCap, PaintStyle, Path, Point};
use skia_safe::{line_2d_path_effect, path_2d_path_effect};
use std::cell::RefCell;
use std::f32::consts::PI;
use std::rc::Rc;

use crate::path::Path2D;
use crate::utils::*;

struct Texture {
  path: Option<Path>,
  color: Color,
  line: f32,
  cap: PaintCap,
  angle: f32,
  scale: (f32, f32),
  shift: (f32, f32),
}

impl Default for Texture {
  fn default() -> Self {
    Texture {
      path: None,
      color: Color::BLACK,
      line: 1.0,
      cap: PaintCap::Butt,
      angle: 0.0,
      scale: (1.0, 1.0),
      shift: (0.0, 0.0),
    }
  }
}

#[pyclass(unsendable, skip_from_py_object)]
#[derive(Clone)]
pub struct CanvasTexture {
  texture: Rc<RefCell<Texture>>,
  outline: bool,
}

impl CanvasTexture {
  pub fn mix_into(&self, paint: &mut Paint, alpha: f32) {
    let tile = self.texture.borrow();

    let mut matrix = Matrix::new_identity();
    matrix
      .pre_translate(tile.shift)
      .pre_rotate(180.0 * tile.angle / PI, None);

    match &tile.path {
      Some(path) => {
        let path = path.with_transform(&Matrix::rotate_rad(tile.angle));
        matrix.pre_scale(tile.scale, None);
        paint.set_path_effect(path_2d_path_effect::new(&matrix, &path));
      }
      None => {
        let scale = tile.scale.0.max(tile.scale.1);
        matrix.pre_scale((scale, scale), None);
        paint.set_path_effect(line_2d_path_effect::new(tile.line, &matrix));
      }
    };

    if tile.line > 0.0 {
      paint.set_stroke_width(tile.line);
      paint.set_stroke_cap(tile.cap);
      paint.set_style(PaintStyle::Stroke);
    } else {
      paint.set_style(PaintStyle::Fill);
    }

    let mut color: Color4f = tile.color.into();
    color.a *= alpha;
    paint.set_color(color.to_color());
  }

  pub fn use_clip(&self) -> bool {
    !self.outline
  }

  pub fn spacing(&self) -> Point {
    let tile = self.texture.borrow();
    tile.scale.into()
  }

  pub fn to_color(&self, alpha: f32) -> Color {
    let tile = self.texture.borrow();
    let mut color: Color4f = tile.color.into();
    color.a *= alpha;
    color.to_color()
  }
}

#[allow(clippy::too_many_arguments)]
#[pymethods]
impl CanvasTexture {
  #[new]
  pub fn new(
    line: f32,
    cap: &str,
    angle: f32,
    outline: bool,
    h: f32,
    v: f32,
    x: f32,
    y: f32,
    path: Option<&Path2D>,
    color: Option<&str>,
  ) -> PyResult<Self> {
    finite_floats(&[line, angle, h, v, x, y])?;
    let path = path.map(|p| p.path.clone());
    let color = color.and_then(css_to_color).unwrap_or(Color::BLACK);
    let cap = match to_stroke_cap(cap) {
      Some(style) => style,
      None => {
        return Err(pyo3::exceptions::PyValueError::new_err(
          "Expected \"butt\", \"square\", or \"round\" for `cap`",
        ));
      }
    };
    let scale = (h, v);
    let shift = (x, y);

    let texture = Texture {
      path,
      color,
      line,
      cap,
      angle,
      scale,
      shift,
    };

    Ok(CanvasTexture {
      texture: Rc::new(RefCell::new(texture)),
      outline,
    })
  }

  pub fn repr(&self) -> String {
    let tile = self.texture.borrow();
    let style = if tile.path.is_some() { "Path" } else { "Lines" };
    style.to_string()
  }
}
