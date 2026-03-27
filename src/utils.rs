#![allow(dead_code)]
use css_color::Rgba;
use pyo3::prelude::*;
use pyo3::types::{PyMapping, PySequence, PyTuple};
use skia_safe::{Color, Matrix, Point, RGB};
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

/* #region strings */

pub fn strings_at_key(obj: Borrowed<'_, '_, PyAny>, attr: &str) -> PyResult<Vec<String>> {
  let attr = obj.getattr(attr)?;
  let list = attr.cast::<PySequence>()?;
  let len = list.len()?;
  let mut result = Vec::with_capacity(len);
  for i in 0..len {
    let item = list.get_item(i)?;
    let s = item.extract::<String>()?;
    result.push(s);
  }
  Ok(result)
}

pub fn strings_at_key_mapping(obj: &Bound<'_, PyMapping>, attr: &str) -> PyResult<Vec<String>> {
  let attr = obj.get_item(attr)?;
  let list = attr.cast::<PySequence>()?;
  let len = list.len()?;
  let mut result = Vec::with_capacity(len);
  for i in 0..len {
    let item = list.get_item(i)?;
    let s = item.extract::<String>()?;
    result.push(s);
  }
  Ok(result)
}

pub fn opt_string_for_key(obj: Borrowed<'_, '_, PyAny>, attr: &str) -> Option<String> {
  obj
    .getattr(attr)
    .ok()
    .and_then(|v| v.extract::<String>().ok())
}

pub fn string_for_key(obj: Borrowed<'_, '_, PyAny>, attr: &str) -> PyResult<String> {
  obj.getattr(attr)?.extract::<String>()
}

/* #endregion */

/* #region floats */

pub fn opt_finite_float(v: Option<f32>, default: f32) -> PyResult<f32> {
  match v {
    Some(num) => finite_float(num),
    None => Ok(default),
  }
}

pub fn opt_finite_float64(v: Option<f64>, default: f64) -> PyResult<f64> {
  match v {
    Some(num) => finite_float64(num),
    None => Ok(default),
  }
}

pub fn finite_float(v: f32) -> PyResult<f32> {
  if v.is_finite() {
    Ok(v)
  } else {
    Err(pyo3::exceptions::PyValueError::new_err(
      "Expected a finite number",
    ))
  }
}

pub fn finite_floats(v: &[f32]) -> PyResult<()> {
  for &num in v {
    finite_float(num)?;
  }
  Ok(())
}

pub fn finite_float64(v: f64) -> PyResult<f64> {
  if v.is_finite() {
    Ok(v)
  } else {
    Err(pyo3::exceptions::PyValueError::new_err(
      "Expected a finite number",
    ))
  }
}

pub fn finite_float64s(v: &[f64]) -> PyResult<()> {
  for &num in v {
    finite_float64(num)?;
  }
  Ok(())
}

pub fn opt_float_for_key(obj: Borrowed<'_, '_, PyAny>, attr: &str) -> Option<f32> {
  obj
    .getattr(attr)
    .ok()
    .and_then(|v| v.extract::<f32>().and_then(finite_float).ok())
}

pub fn float_for_key(obj: Borrowed<'_, '_, PyAny>, attr: &str) -> PyResult<f32> {
  obj.getattr(attr)?.extract::<f32>().and_then(finite_float)
}

pub fn float_for_key_mapping(obj: &Bound<'_, PyMapping>, attr: &str) -> PyResult<f32> {
  obj.get_item(attr)?.extract::<f32>().and_then(finite_float)
}

/* #endregion */

/* #region Colors */

pub fn opt_color_for_key(obj: Borrowed<'_, '_, PyAny>, attr: &str) -> Option<Color> {
  obj
    .getattr(attr)
    .ok()
    .and_then(|v| v.extract::<String>().ok())
    .and_then(|s| css_to_color(&s))
}

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

pub fn color_to_css(color: &Color) -> String {
  let RGB { r, g, b } = color.to_rgb();
  match color.a() {
    255 => format!("#{:02x}{:02x}{:02x}", r, g, b),
    _ => {
      let alpha = format!("{:.3}", color.a() as f32 / 255.0);
      let alpha = alpha.trim_end_matches('0');
      format!(
        "rgba({}, {}, {}, {})",
        r,
        g,
        b,
        if alpha == "0." { "0" } else { alpha }
      )
    }
  }
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

pub fn opt_finite_matrix(t: &[f32]) -> Option<Matrix> {
  if t.iter().all(|&v| finite_float(v).is_ok()) {
    to_matrix(t)
  } else {
    None
  }
}

/* #endregion */

/* #region Points */

pub fn to_points(nums: Vec<f32>) -> Option<Vec<Point>> {
  if !nums.len().is_multiple_of(2) {
    return None;
  }
  let points = nums
    .as_slice()
    .chunks_exact(2)
    .map(|pair| Point::new(pair[0], pair[1]))
    .collect();
  Some(points)
}

/* #endregion */

/* #region Image & ImageData */

use skia_safe::{ColorSpace, ColorType};

pub struct ImageDataExportArg {
  pub color_type: ColorType,
  pub color_space: ColorSpace,
  pub matte: Option<Color>,
  pub density: f32,
  pub msaa: Option<usize>,
}

impl FromPyObject<'_, '_> for ImageDataExportArg {
  type Error = PyErr;

  fn extract(obj: Borrowed<'_, '_, PyAny>) -> Result<Self, Self::Error> {
    let color_type = opt_string_for_key(obj, "color_type").unwrap_or("rgba".to_string());
    let color_space = opt_string_for_key(obj, "color_space").unwrap_or("srgb".to_string());
    let matte = opt_color_for_key(obj, "matte");
    let density = opt_float_for_key(obj, "density").unwrap_or(1.0);
    let msaa = opt_float_for_key(obj, "msaa").map(|n| n as usize);
    Ok(Self {
      color_type: to_color_type(&color_type),
      color_space: to_color_space(&color_space),
      matte,
      density,
      msaa,
    })
  }
}

pub fn image_data_export_arg(arg: Option<ImageDataExportArg>) -> ImageDataExportArg {
  match arg {
    Some(v) => v,
    None => ImageDataExportArg {
      color_type: ColorType::RGBA8888,
      color_space: ColorSpace::new_srgb(),
      matte: None,
      density: 1.0,
      msaa: None,
    },
  }
}

pub fn to_color_space(_: &str) -> ColorSpace {
  // TODO: add display-p3 support
  // match mode_name {
  //   "srgb" | _ => ColorSpace::new_srgb(),
  // }
  ColorSpace::new_srgb()
}

pub fn from_color_space(_: ColorSpace) -> String {
  // TODO: add display-p3 support
  // match mode {
  //   _ => "srgb",
  // }
  // .to_string()
  "srgb".to_string()
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
    "RGBA8888" | "rgba" => ColorType::RGBA8888,
    _ => ColorType::RGBA8888,
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

/* #region Filters */

use crate::filter::{FilterQuality, FilterSpec};

pub struct FilterPy {
  pub canonical: String,
  pub filters: Vec<FilterSpec>,
}

impl FromPyObject<'_, '_> for FilterPy {
  type Error = PyErr;

  fn extract(obj: Borrowed<'_, '_, PyAny>) -> Result<Self, Self::Error> {
    let canonical = string_for_key(obj, "canonical")?;
    let filter_obj = obj.getattr("filters")?;
    let mapping = filter_obj.cast::<PyMapping>()?;
    let mut filters = Vec::new();
    let items_list = mapping.items()?;

    for item in items_list.iter() {
      let tuple_item = item.cast::<PyTuple>()?;
      let key: String = tuple_item.get_item(0)?.extract()?;
      let value = tuple_item.get_item(1)?;
      match key.as_str() {
        "drop-shadow" => {
          let values = value.cast::<PyTuple>()?;
          let mut dims = Vec::new();
          for v in values.iter() {
            if let Ok(n) = v.extract::<f32>() {
              dims.push(n);
            }
          }
          let color_str = values.get_item(3)?.extract::<String>()?;
          if let Some(color) = css_to_color(&color_str) {
            filters.push(FilterSpec::Shadow {
              offset: Point::new(dims[0], dims[1]),
              blur: dims[2],
              color,
            });
          }
        }
        _ => {
          let value = value.extract::<f32>()?;
          filters.push(FilterSpec::Plain {
            name: key.clone(),
            value,
          })
        }
      }
    }

    Ok(Self { canonical, filters })
  }
}

pub fn to_filter_quality(mode_name: &str) -> Option<FilterQuality> {
  let mode = match mode_name.to_lowercase().as_str() {
    "low" => FilterQuality::Low,
    "medium" => FilterQuality::Medium,
    "high" => FilterQuality::High,
    _ => return None,
  };
  Some(mode)
}

pub fn from_filter_quality(mode: FilterQuality) -> String {
  match mode {
    FilterQuality::Low => "low",
    FilterQuality::Medium => "medium",
    FilterQuality::High => "high",
    _ => "low",
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

use skia_safe::PaintJoin;
pub fn to_stroke_join(mode_name: &str) -> Option<PaintJoin> {
  let mode = match mode_name.to_lowercase().as_str() {
    "miter" => PaintJoin::Miter,
    "round" => PaintJoin::Round,
    "bevel" => PaintJoin::Bevel,
    _ => return None,
  };
  Some(mode)
}

pub fn from_stroke_join(mode: PaintJoin) -> String {
  match mode {
    PaintJoin::Miter => "miter",
    PaintJoin::Round => "round",
    PaintJoin::Bevel => "bevel",
  }
  .to_string()
}

use skia_safe::BlendMode;
pub fn to_blend_mode(mode_name: &str) -> Option<BlendMode> {
  let mode = match mode_name.to_lowercase().as_str() {
    "source-over" => BlendMode::SrcOver,
    "destination-over" => BlendMode::DstOver,
    "copy" => BlendMode::Src,
    "destination" => BlendMode::Dst,
    "clear" => BlendMode::Clear,
    "source-in" => BlendMode::SrcIn,
    "destination-in" => BlendMode::DstIn,
    "source-out" => BlendMode::SrcOut,
    "destination-out" => BlendMode::DstOut,
    "source-atop" => BlendMode::SrcATop,
    "destination-atop" => BlendMode::DstATop,
    "xor" => BlendMode::Xor,
    "lighter" => BlendMode::Plus,
    "multiply" => BlendMode::Multiply,
    "screen" => BlendMode::Screen,
    "overlay" => BlendMode::Overlay,
    "darken" => BlendMode::Darken,
    "lighten" => BlendMode::Lighten,
    "color-dodge" => BlendMode::ColorDodge,
    "color-burn" => BlendMode::ColorBurn,
    "hard-light" => BlendMode::HardLight,
    "soft-light" => BlendMode::SoftLight,
    "difference" => BlendMode::Difference,
    "exclusion" => BlendMode::Exclusion,
    "hue" => BlendMode::Hue,
    "saturation" => BlendMode::Saturation,
    "color" => BlendMode::Color,
    "luminosity" => BlendMode::Luminosity,
    _ => return None,
  };
  Some(mode)
}

pub fn from_blend_mode(mode: BlendMode) -> String {
  match mode {
    BlendMode::SrcOver => "source-over",
    BlendMode::DstOver => "destination-over",
    BlendMode::Src => "copy",
    BlendMode::Dst => "destination",
    BlendMode::Clear => "clear",
    BlendMode::SrcIn => "source-in",
    BlendMode::DstIn => "destination-in",
    BlendMode::SrcOut => "source-out",
    BlendMode::DstOut => "destination-out",
    BlendMode::SrcATop => "source-atop",
    BlendMode::DstATop => "destination-atop",
    BlendMode::Xor => "xor",
    BlendMode::Plus => "lighter",
    BlendMode::Multiply => "multiply",
    BlendMode::Screen => "screen",
    BlendMode::Overlay => "overlay",
    BlendMode::Darken => "darken",
    BlendMode::Lighten => "lighten",
    BlendMode::ColorDodge => "color-dodge",
    BlendMode::ColorBurn => "color-burn",
    BlendMode::HardLight => "hard-light",
    BlendMode::SoftLight => "soft-light",
    BlendMode::Difference => "difference",
    BlendMode::Exclusion => "exclusion",
    BlendMode::Hue => "hue",
    BlendMode::Saturation => "saturation",
    BlendMode::Color => "color",
    BlendMode::Luminosity => "luminosity",
    _ => "source-over",
  }
  .to_string()
}

use skia_safe::PathOp;
pub fn to_path_op(op_name: &str) -> Option<PathOp> {
  let op = match op_name.to_lowercase().as_str() {
    "difference" => PathOp::Difference,
    "intersect" => PathOp::Intersect,
    "union" => PathOp::Union,
    "xor" => PathOp::XOR,
    "reversedifference" | "complement" => PathOp::ReverseDifference,
    _ => return None,
  };
  Some(op)
}

use skia_safe::path_1d_path_effect;
pub fn to_1d_style(mode_name: &str) -> Option<path_1d_path_effect::Style> {
  let mode = match mode_name.to_lowercase().as_str() {
    "move" => path_1d_path_effect::Style::Translate,
    "turn" => path_1d_path_effect::Style::Rotate,
    "follow" => path_1d_path_effect::Style::Morph,
    _ => return None,
  };
  Some(mode)
}

pub fn from_1d_style(mode: path_1d_path_effect::Style) -> String {
  match mode {
    path_1d_path_effect::Style::Translate => "move",
    path_1d_path_effect::Style::Rotate => "turn",
    path_1d_path_effect::Style::Morph => "follow",
  }
  .to_string()
}

use skia_safe::PathFillType;

pub fn to_fill_rule(rule_name: &str) -> Option<PathFillType> {
  match rule_name {
    "nonzero" => Some(PathFillType::Winding),
    "evenodd" => Some(PathFillType::EvenOdd),
    _ => None,
  }
}

pub fn to_fill_rule_or_error(rule_name: &str) -> PyResult<PathFillType> {
  match to_fill_rule(rule_name) {
    Some(v) => Ok(v),
    None => Err(pyo3::exceptions::PyValueError::new_err(format!(
      "Invalid fill rule: {}. Expected 'nonzero' or 'evenodd'.",
      rule_name
    ))),
  }
}

use crate::gpu::RenderingEngine;
pub fn to_engine(engine_name: &str) -> Option<RenderingEngine> {
  let mode = match engine_name.to_lowercase().as_str() {
    "gpu" => RenderingEngine::GPU,
    "cpu" => RenderingEngine::CPU,
    _ => return None,
  };
  Some(mode)
}

pub fn from_engine(engine: RenderingEngine) -> String {
  match engine {
    RenderingEngine::GPU => "gpu",
    RenderingEngine::CPU => "cpu",
  }
  .to_string()
}

/* #endregion */
