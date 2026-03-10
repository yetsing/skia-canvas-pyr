use core::ops::Range;
use css_color::Rgba;
use skia_safe::{Color, Data, Matrix, Path, Point, RGB};
use std::cmp;
use std::f32::consts::PI;

pub fn almost_equal(a: f32, b: f32) -> bool {
  (a - b).abs() < 0.00001
}

pub fn almost_zero(a: f32) -> bool {
  a.abs() < 0.00001
}

pub fn to_degrees(radians: f32) -> f32 {
  radians / PI * 180.0
}

pub fn to_radians(degrees: f32) -> f32 {
  degrees / 180.0 * PI
}

pub fn to_matrix(t: &[f32]) -> Option<Matrix> {
  match t.len() {
    6 => Some(Matrix::new_all(
      t[0], t[1], t[2], t[3], t[4], t[5], 0.0, 0.0, 1.0,
    )),
    9 => Some(Matrix::new_all(
      t[0], t[1], t[2], t[3], t[4], t[5], t[6], t[7], t[8],
    )),
    _ => None,
  }
}
