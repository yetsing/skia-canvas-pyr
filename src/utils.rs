use core::ops::Range;
use css_color::Rgba;
use skia_safe::{Color, Data, Matrix, Path, Point, RGB};
use std::cmp;
use std::f32::consts::PI;

/* #region meta-helpers */

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

/* #endregion */

/* #region Colors */

pub fn css_to_color(css: &str) -> Option<Color> {
  css.parse::<Rgba>().ok().map(
    |Rgba {
       red,
       green,
       blue,
       alpha,
     }| {
      Color::from_argb(
        (alpha * 255.0).round() as u8,
        (red * 255.0).round() as u8,
        (green * 255.0).round() as u8,
        (blue * 255.0).round() as u8,
      )
    },
  )
}

/* #endregion */

/* #region Matrices */

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

/* #endregion */

/* #region Image & ImageData */

use skia_safe::{AlphaType, ColorSpace, ColorType, ImageInfo};

pub fn to_color_space(mode_name: &str) -> ColorSpace {
  match mode_name {
    // TODO: add display-p3 support
    "srgb" | _ => ColorSpace::new_srgb(),
  }
}

pub fn from_color_space(mode: ColorSpace) -> String {
  match mode {
    _ => "srgb",
  }
  .to_string()
}

pub fn to_color_type(type_name: &str) -> ColorType {
  match type_name {
    "Alpha8" => ColorType::Alpha8,
    "RGB565" => ColorType::RGB565,
    "ARGB4444" => ColorType::ARGB4444,
    "RGBA1010102" => ColorType::RGBA1010102,
    "BGRA1010102" => ColorType::BGRA1010102,
    "RGB101010x" => ColorType::RGB101010x,
    "BGR101010x" => ColorType::BGR101010x,
    "Gray8" => ColorType::Gray8,
    "RGBAF16Norm" => ColorType::RGBAF16Norm,
    "RGBAF16" => ColorType::RGBAF16,
    "RGBAF32" => ColorType::RGBAF32,
    "R8G8UNorm" => ColorType::R8G8UNorm,
    "A16Float" => ColorType::A16Float,
    "R16G16Float" => ColorType::R16G16Float,
    "A16UNorm" => ColorType::A16UNorm,
    "R16G16UNorm" => ColorType::R16G16UNorm,
    "R16G16B16A16UNorm" => ColorType::R16G16B16A16UNorm,
    "SRGBA8888" => ColorType::SRGBA8888,
    "R8UNorm" => ColorType::R8UNorm,
    "N32" => ColorType::N32,
    "RGB888x" | "rgb" => ColorType::RGB888x,
    "BGRA8888" | "bgra" => ColorType::BGRA8888,
    "RGBA8888" | "rgba" | _ => ColorType::RGBA8888,
  }
}

pub fn from_color_type(color_type: ColorType) -> String {
  match color_type {
    ColorType::Alpha8 => "Alpha8",
    ColorType::RGB565 => "RGB565",
    ColorType::ARGB4444 => "ARGB4444",
    ColorType::RGBA8888 => "RGBA8888",
    ColorType::RGB888x => "RGB888x",
    ColorType::BGRA8888 => "BGRA8888",
    ColorType::RGBA1010102 => "RGBA1010102",
    ColorType::BGRA1010102 => "BGRA1010102",
    ColorType::RGB101010x => "RGB101010x",
    ColorType::BGR101010x => "BGR101010x",
    ColorType::Gray8 => "Gray8",
    ColorType::RGBAF16Norm => "RGBAF16Norm",
    ColorType::RGBAF16 => "RGBAF16",
    ColorType::RGBAF32 => "RGBAF32",
    ColorType::R8G8UNorm => "R8G8UNorm",
    ColorType::A16Float => "A16Float",
    ColorType::R16G16Float => "R16G16Float",
    ColorType::A16UNorm => "A16UNorm",
    ColorType::R16G16UNorm => "R16G16UNorm",
    ColorType::R16G16B16A16UNorm => "R16G16B16A16UNorm",
    ColorType::SRGBA8888 => "SRGBA8888",
    ColorType::R8UNorm => "R8UNorm",
    _ => "unknown",
  }
  .to_string()
}

/* #endregion */

/* #region Skia Enums */

use skia_safe::{
  TileMode,
  TileMode::{Decal, Repeat},
};
pub fn to_repeat_mode(repeat: &str) -> Option<(TileMode, TileMode)> {
  let mode = match repeat.to_lowercase().as_str() {
    "repeat" | "" => (Repeat, Repeat),
    "repeat-x" => (Repeat, Decal),
    "repeat-y" => (Decal, Repeat),
    "no-repeat" => (Decal, Decal),
    _ => return None,
  };
  Some(mode)
}

use skia_safe::PaintCap;
pub fn to_stroke_cap(mode_name: &str) -> Option<PaintCap> {
  let mode = match mode_name.to_lowercase().as_str() {
    "butt" => PaintCap::Butt,
    "round" => PaintCap::Round,
    "square" => PaintCap::Square,
    _ => return None,
  };
  Some(mode)
}

pub fn from_stroke_cap(mode: PaintCap) -> String {
  match mode {
    PaintCap::Butt => "butt",
    PaintCap::Round => "round",
    PaintCap::Square => "square",
  }
  .to_string()
}

/* #endregion */
