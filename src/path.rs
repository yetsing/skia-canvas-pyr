use pyo3::types::PyList;
use pyo3::{IntoPyObjectExt, prelude::*};
use skia_safe::path::{self, AddPathMode, Verb};
use skia_safe::{
  Matrix, Path, PathBuilder, PathDirection, PathFillType, PathOp, Point, RRect, Rect, StrokeRec,
};
use skia_safe::{PathEffect, trim_path_effect};
use std::f32::consts::PI;

use crate::utils::{to_degrees, to_matrix};

#[pyclass(unsendable)]
pub struct Path2D {
  pub path: Path,
}

impl Default for Path2D {
  fn default() -> Self {
    Self { path: Path::new() }
  }
}

impl From<PathBuilder> for Path2D {
  fn from(builder: PathBuilder) -> Self {
    Self {
      path: builder.into(),
    }
  }
}

impl Path2D {
  pub fn scoot(&mut self, x: f32, y: f32) {
    if self.path.is_empty() {
      self.path.move_to((x, y));
    }
  }

  pub fn add_ellipse(
    &mut self,
    origin: impl Into<Point>,
    radii: impl Into<Point>,
    rotation: f32,
    start_angle: f32,
    end_angle: f32,
    ccw: bool,
  ) {
    let Point { x, y } = origin.into();
    let Point {
      x: x_radius,
      y: y_radius,
    } = radii.into();

    // based off of CanonicalizeAngle in Chrome
    let tau = 2.0 * PI;
    let mut new_start_angle = start_angle % tau;
    if new_start_angle < 0.0 {
      new_start_angle += tau;
    }
    let delta = new_start_angle - start_angle;
    let start_angle = new_start_angle;
    let mut end_angle = end_angle + delta;

    // Originally based off of AdjustEndAngle in Chrome, but does not limit to 360 degree sweep.
    if !ccw && start_angle > end_angle {
      end_angle = start_angle + (tau - (start_angle - end_angle) % tau);
    } else if ccw && start_angle < end_angle {
      end_angle = start_angle - (tau - (end_angle - start_angle) % tau);
    }

    let oval = Rect::new(x - x_radius, y - y_radius, x + x_radius, y + y_radius);

    let mut rotated = Matrix::new_identity();
    rotated
      .pre_translate((x, y))
      .pre_rotate(to_degrees(rotation), None)
      .pre_translate((-x, -y));

    self.path.transform(&rotated.invert().unwrap());
    {
      // Based off of Chrome's implementation in
      // https://cs.chromium.org/chromium/src/third_party/blink/renderer/platform/graphics/path.cc
      // of note, can't use addArc or addOval because they close the arc, which
      // the spec says not to do (unless the user explicitly calls closePath).
      // This throws off points being in/out of the arc.

      // rounding degrees to 4 decimals eliminates ambiguity from f32 imprecision dealing with radians
      let sweep_deg = (to_degrees(end_angle - start_angle) * 10000.0).round() / 10000.0;
      let start_deg = (to_degrees(start_angle) * 10000.0).round() / 10000.0;

      // draw 360° ellipses in two 180° segments; trying to draw the full ellipse at once draws nothing.
      if sweep_deg >= 360.0 - f32::EPSILON {
        self.path.arc_to(oval, start_deg, 180.0, false);
        self.path.arc_to(oval, start_deg + 180.0, 180.0, false);
      } else if sweep_deg <= -360.0 + f32::EPSILON {
        self.path.arc_to(oval, start_deg, -180.0, false);
        self.path.arc_to(oval, start_deg - 180.0, -180.0, false);
      } else {
        // Draw incomplete (< 360°) ellipses in a single arc.
        self.path.arc_to(oval, start_deg, sweep_deg, false);
      }
    }
    self.path.transform(&rotated);
  }
}

#[allow(clippy::too_many_arguments)]
#[pymethods]
impl Path2D {
  #[new]
  pub fn new() -> Self {
    let path = Path::new();
    Self { path }
  }

  #[staticmethod]
  pub fn from_path(other_path: &Path2D) -> Self {
    Self {
      path: other_path.path.clone(),
    }
  }

  #[staticmethod]
  pub fn from_svg(d: String) -> Self {
    let path = Path::from_svg(d).unwrap_or_default();
    Self { path }
  }

  /// Adds a path to the current path.
  pub fn add_path(&mut self, other: &Path2D, transform: Option<Vec<f32>>) {
    let matrix = match transform {
      Some(t) => to_matrix(&t).unwrap_or_else(Matrix::new_identity),
      None => Matrix::new_identity(),
    };

    // make a copy if adding a path to itself, otherwise use a ref
    if std::ptr::eq(self, other) {
      let src = other.path.clone();
      self
        .path
        .add_path_matrix(&src, &matrix, AddPathMode::Append);
    } else {
      let src = &other.path;
      self.path.add_path_matrix(src, &matrix, AddPathMode::Append);
    }
  }

  /// Causes the point of the pen to move back to the start of the current sub-path. It tries to draw a straight line from the current point to the start. If the shape has already been closed or has only one point, this function does nothing.
  pub fn close_path(&mut self) {
    self.path.close();
  }

  /// Moves the starting point of a new sub-path to the (x, y) coordinates.
  pub fn move_to(&mut self, x: f32, y: f32) {
    self.path.move_to((x, y));
  }

  /// Connects the last point in the subpath to the (x, y) coordinates with a straight line.
  pub fn line_to(&mut self, x: f32, y: f32) {
    self.scoot(x, y);
    self.path.line_to((x, y));
  }

  /// Adds a cubic Bézier curve to the path. It requires three points. The first two points are control points and the third one is the end point. The starting point is the last point in the current path, which can be changed using moveTo() before creating the Bézier curve.
  pub fn bezier_curve_to(&mut self, cp1x: f32, cp1y: f32, cp2x: f32, cp2y: f32, x: f32, y: f32) {
    self.scoot(cp1x, cp1y);
    self.path.cubic_to((cp1x, cp1y), (cp2x, cp2y), (x, y));
  }

  /// Adds a quadratic Bézier curve to the current path.
  pub fn quadratic_curve_to(&mut self, cpx: f32, cpy: f32, x: f32, y: f32) {
    self.scoot(cpx, cpy);
    self.path.quad_to((cpx, cpy), (x, y));
  }

  /// Adds a conic-section curve to the current path.
  pub fn conic_curve_to(&mut self, cpx: f32, cpy: f32, x: f32, y: f32, weight: f32) {
    self.scoot(cpx, cpy);
    self.path.conic_to((cpx, cpy), (x, y), weight);
  }

  /// Adds an arc to the path which is centered at (x, y) position with radius r starting at startAngle and ending at endAngle going in the given direction by anticlockwise (defaulting to clockwise).
  pub fn arc(
    &mut self,
    x: f32,
    y: f32,
    radius: f32,
    start_angle: f32,
    end_angle: f32,
    counterclockwise: Option<bool>,
  ) {
    self.add_ellipse(
      (x, y),
      (radius, radius),
      0.0,
      start_angle,
      end_angle,
      counterclockwise.unwrap_or(false),
    );
  }

  /// Adds a circular arc to the path with the given control points and radius, connected to the previous point by a straight line.
  pub fn arc_to(&mut self, x1: f32, y1: f32, x2: f32, y2: f32, radius: f32) {
    self.scoot(x1, y1);
    self.path.arc_to_tangent((x1, y1), (x2, y2), radius);
  }

  /// Adds an elliptical arc to the path which is centered at (x, y) position with the radii radiusX and radiusY starting at startAngle and ending at endAngle going in the given direction by anticlockwise (defaulting to clockwise).
  pub fn ellipse(
    &mut self,
    x: f32,
    y: f32,
    radius_x: f32,
    radius_y: f32,
    rotation: f32,
    start_angle: f32,
    end_angle: f32,
    counterclockwise: Option<bool>,
  ) -> PyResult<()> {
    if radius_x < 0.0 || radius_y < 0.0 {
      return Err(pyo3::exceptions::PyValueError::new_err(
        "Radius value must be positive",
      ));
    }
    self.add_ellipse(
      (x, y),
      (radius_x, radius_y),
      rotation,
      start_angle,
      end_angle,
      counterclockwise.unwrap_or(false),
    );

    Ok(())
  }

  // Creates a path for a rectangle at position (x, y) with a size that is determined by width and height.
  pub fn rect(&mut self, x: f32, y: f32, width: f32, height: f32) {
    let rect = Rect::from_xywh(x, y, width, height);
    let direction = if width.signum() == height.signum() {
      PathDirection::CW
    } else {
      PathDirection::CCW
    };

    self.path.add_rect(rect, Some((direction, 0)));
  }

  /// Creates a path for a rounded rectangle at position (x, y) with a size (w, h) and whose radii
  /// are specified in x/y pairs for top_left, top_right, bottom_right, and bottom_left
  pub fn round_rect(
    &mut self,
    x: f32,
    y: f32,
    width: f32,
    height: f32,
    top_left_radius_x: f32,
    top_left_radius_y: f32,
    top_right_radius_x: f32,
    top_right_radius_y: f32,
    bottom_right_radius_x: f32,
    bottom_right_radius_y: f32,
    bottom_left_radius_x: f32,
    bottom_left_radius_y: f32,
  ) {
    let rect = Rect::from_xywh(x, y, width, height);
    let radii = [
      Point::new(top_left_radius_x, top_left_radius_y),
      Point::new(top_right_radius_x, top_right_radius_y),
      Point::new(bottom_right_radius_x, bottom_right_radius_y),
      Point::new(bottom_left_radius_x, bottom_left_radius_y),
    ];
    let rrect = RRect::new_rect_radii(rect, &radii);
    let direction = if width.signum() == height.signum() {
      PathDirection::CW
    } else {
      PathDirection::CCW
    };

    self.path.add_rrect(rrect, Some((direction, 0)));
  }

  // Applies a boolean operator to this and a second path, returning a new Path2D with their combination
  pub fn op(&self, other: &Path2D, operation: String) -> PyResult<Self> {
    let op = match operation.to_lowercase().as_str() {
      "difference" => PathOp::Difference,
      "intersect" => PathOp::Intersect,
      "union" => PathOp::Union,
      "xor" => PathOp::XOR,
      "reversedifference" | "complement" => PathOp::ReverseDifference,
      _ => {
        return Err(pyo3::exceptions::PyValueError::new_err(
          "pathOp must be Difference, Intersect, Union, XOR, or Complement",
        ));
      }
    };

    match self.path.op(&other.path, op) {
      Some(result) => Ok(Self { path: result }),
      None => Err(pyo3::exceptions::PyValueError::new_err(
        "path operation failed",
      )),
    }
  }

  pub fn interpolate(&self, other: &Path2D, weight: f32) -> PyResult<Self> {
    // reverse path order since 0..1 = this..other is a less non-sensical mapping than the default
    if let Some(path) = other.path.interpolate(&self.path, weight) {
      Ok(Self { path })
    } else {
      Err(pyo3::exceptions::PyValueError::new_err(
        "Can only interpolate between two Path2D objects with the same number of points and control points",
      ))
    }
  }

  /// Returns a path with only non-overlapping contours that describe the same area as the original path
  pub fn simplify(&mut self, fill_rule: Option<String>) -> PyResult<Self> {
    let fill_rule = fill_rule.unwrap_or("nonzero".to_string());
    let rule = match fill_rule.as_str() {
      "nonzero" => PathFillType::Winding,
      "evenodd" => PathFillType::EvenOdd,
      _ => {
        return Err(pyo3::exceptions::PyValueError::new_err(
          "fillRule must be 'nonzero' or 'evenodd'",
        ));
      }
    };

    self.path.set_fill_type(rule);

    let new_path = Self {
      path: match self.path.simplify() {
        Some(simpler) => simpler,
        None => self.path.clone(),
      },
    };

    Ok(new_path)
  }

  /// Returns a path that can be drawn with a nonzero fill but looks like the original drawn with evenodd
  pub fn unwind(&mut self) -> Self {
    self.path.set_fill_type(PathFillType::EvenOdd);

    Self {
      path: match self.path.as_winding() {
        Some(rewound) => rewound,
        None => self.path.clone(),
      },
    }
  }

  /// Returns a copy whose points have been shifted by (dx, dy)
  pub fn offset(&self, dx: f32, dy: f32) -> Self {
    let path = self.path.with_offset((dx, dy));
    Self { path }
  }

  /// Returns a copy whose points have been transformed by a given matrix
  pub fn transform(&self, matrix: Vec<f32>) -> PyResult<Self> {
    let matrix = to_matrix(&matrix).ok_or_else(|| {
      pyo3::exceptions::PyValueError::new_err("Matrix must be a 6 or 9 element array")
    })?;

    let path = self.path.with_transform(&matrix);
    Ok(Self { path })
  }

  /// Returns a copy where every sharp junction to an arcTo-style rounded corner
  pub fn round(&self, radius: f32) -> Self {
    let bounds = self.path.bounds();
    let stroke_rec = StrokeRec::new_hairline();

    if let Some(rounder) = PathEffect::corner_path(radius)
      && let Some((path, _)) = rounder.filter_path(&self.path, &stroke_rec, bounds)
    {
      return Self::from(path);
    }

    Self {
      path: self.path.clone(),
    }
  }

  /// Clips a proportional segment out of the middle of the path (or the edges if invert=true)
  pub fn trim(&self, begin: f32, end: f32, inverted: Option<bool>) -> Self {
    let inverted = inverted.unwrap_or(false);

    let bounds = self.path.bounds();
    let stroke_rect = StrokeRec::new_hairline();
    let mode = if inverted {
      trim_path_effect::Mode::Inverted
    } else {
      trim_path_effect::Mode::Normal
    };

    if let Some(trimmer) = PathEffect::trim(begin, end, mode)
      && let Some((path, _)) = trimmer.filter_path(&self.path, &stroke_rect, bounds)
    {
      return Self::from(path);
    }

    Self {
      path: self.path.clone(),
    }
  }

  /// Discretizes the path at a fixed segment length then randomly offsets the points
  pub fn jitter(&self, segment_length: f32, variance: f32, seed: Option<f32>) -> Self {
    let seed = seed.unwrap_or(0.0) as u32;

    let bounds = self.path.bounds();
    let stroke_rect = StrokeRec::new_hairline();

    if let Some(trimmer) = PathEffect::discrete(segment_length, variance, Some(seed))
      && let Some((path, _)) = trimmer.filter_path(&self.path, &stroke_rect, bounds)
    {
      return Self::from(path);
    }

    Self {
      path: self.path.clone(),
    }
  }

  /// Returns the computed `tight` bounds that contain all the points, control points, and connecting contours
  pub fn bounds(&self) -> Path2DBounds {
    let b = self.path.compute_tight_bounds();
    Path2DBounds {
      top: b.top,
      left: b.left,
      bottom: b.bottom,
      right: b.right,
      width: b.width(),
      height: b.height(),
    }
  }

  pub fn contains(&self, x: f32, y: f32) -> bool {
    self.path.contains((x, y))
  }

  pub fn edges<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyList>> {
    let mut weights = path::Iter::new(&self.path, false);
    let iter = path::Iter::new(&self.path, false);

    let mut edges = vec![];
    for (verb, points) in iter {
      weights.next();

      if let Some(edge) = from_verb(verb) {
        let cmd = edge.into_py_any(py)?;
        let segment = PyList::empty(py);
        segment.append(cmd)?;

        let at_point = if points.len() > 1 { 1 } else { 0 };
        for pt in points.iter().skip(at_point) {
          segment.append(pt.x)?;
          segment.append(pt.y)?;
        }

        if verb == Verb::Conic {
          let weight = weights.conic_weight().unwrap();
          segment.set_item(5, weight)?;
        }

        edges.push(segment.to_tuple());
      }
    }

    PyList::new(py, edges)
  }

  pub fn get_d(&self) -> String {
    self.path.to_svg()
  }

  pub fn set_d(&mut self, p: String) -> PyResult<()> {
    if let Some(path) = Path::from_svg(p) {
      self.path.rewind();
      self.path.add_path(&path, (0, 0), None);
      Ok(())
    } else {
      Err(pyo3::exceptions::PyValueError::new_err(
        "Invalid SVG path string",
      ))
    }
  }
}

fn from_verb(verb: Verb) -> Option<String> {
  let cmd = match verb {
    Verb::Move => "moveTo",
    Verb::Line => "lineTo",
    Verb::Quad => "quadraticCurveTo",
    Verb::Cubic => "bezierCurveTo",
    Verb::Conic => "conicCurveTo",
    Verb::Close => "closePath",
    _ => return None,
  };
  Some(cmd.to_string())
}

#[pyclass(get_all)]
pub struct Path2DBounds {
  pub top: f32,
  pub left: f32,
  pub bottom: f32,
  pub right: f32,
  pub width: f32,
  pub height: f32,
}
