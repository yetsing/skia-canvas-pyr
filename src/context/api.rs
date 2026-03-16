use pyo3::prelude::*;
use skia_safe::PaintStyle::{Fill, Stroke};
use skia_safe::path::AddPathMode::Extend;
use skia_safe::textlayout::TextDirection;
use skia_safe::{Matrix, PaintStyle, Path, PathDirection, Point, RRect, Rect, Size};

use super::{Context2D, Dye, DyeValue, page::ExportOptions};
use crate::canvas::Canvas;
use crate::filter::Filter;
use crate::image::{Content, Image, ImageData};
use crate::path::Path2D;
use crate::typography::{
  DecorationStyle, FontSpec, Spacing, font_features, from_text_align, from_text_baseline,
  from_width, to_text_align, to_text_baseline, to_width,
};
use crate::utils::*;

//
// The py interface for the Context2D struct
//

#[allow(clippy::too_many_arguments)]
#[pymethods]
impl Context2D {
  #[new]
  pub fn new_py(canvas: &Canvas) -> Self {
    let mut ins = Self::new();
    ins.reset_size((canvas.width, canvas.height));
    ins
  }

  #[pyo3(name = "reset_size")]
  pub fn reset_size_py(&mut self, canvas: &Canvas) {
    self.reset_size((canvas.width, canvas.height));
  }

  pub fn get_size(&self) -> (f32, f32) {
    let bounds = self.bounds;
    (bounds.size().width, bounds.size().height)
  }

  pub fn set_size(&mut self, width: f32, height: f32) {
    self.reset_size((width, height));
  }

  pub fn reset(&mut self) {
    let size = self.bounds.size();
    self.reset_size(size);
  }

  //
  // Grid State
  //

  pub fn save(&mut self) {
    self.push();
  }

  pub fn restore(&mut self) {
    self.pop();
  }

  pub fn transform(&mut self, matrix: Vec<f32>) -> PyResult<()> {
    let matrix = to_matrix(&matrix).ok_or_else(|| {
      pyo3::exceptions::PyValueError::new_err("Matrix must be a 6 or 9 element array")
    })?;
    self.with_matrix(|ctm| ctm.pre_concat(&matrix));
    Ok(())
  }

  pub fn translate(&mut self, x: f32, y: f32) {
    self.with_matrix(|ctm| ctm.pre_translate((x, y)));
  }

  pub fn scale(&mut self, x: f32, y: f32) {
    self.with_matrix(|ctm| ctm.pre_scale((x, y), None));
  }

  pub fn rotate(&mut self, angle: f32) {
    self.with_matrix(|ctm| ctm.pre_rotate(angle.to_degrees(), None));
  }

  pub fn reset_transform(&mut self) {
    self.with_matrix(|ctm| ctm.reset());
  }

  pub fn create_projection(&mut self, dst: Vec<f32>, src: Vec<f32>) -> PyResult<Vec<f32>> {
    let dst_len = dst.len();
    let src_len = src.len();
    let dst = to_points(dst).ok_or_else(|| {
      pyo3::exceptions::PyValueError::new_err(format!(
        "Lists of x/y points must have an even number of values (got {dst_len} in dst argument)",
      ))
    })?;
    let src = to_points(src).ok_or_else(|| {
      pyo3::exceptions::PyValueError::new_err(format!(
        "Lists of x/y points must have an even number of values (got {src_len} in src argument)",
      ))
    })?;

    let basis: Vec<Point> = match src.len() {
      0 => self.bounds.to_quad(None).to_vec(), // use canvas dims
      1 => Rect::from_wh(src[0].x, src[0].y).to_quad(None).to_vec(), // implicit 0,0 origin
      2 => Rect::new(src[0].x, src[0].y, src[1].x, src[1].y)
        .to_quad(None)
        .to_vec(), // lf/top, rt/bot
      _ => src.clone(),
    };

    let quad: Vec<Point> = match dst.len() {
      1 => Rect::from_wh(dst[0].x, dst[0].y).to_quad(None).to_vec(), // implicit 0,0 origin
      2 => Rect::new(dst[0].x, dst[0].y, dst[1].x, dst[1].y)
        .to_quad(None)
        .to_vec(), // lf/top, rt/bot
      _ => dst.clone(),
    };

    match (
      Matrix::from_poly_to_poly(&basis, &quad),
      basis.len() == quad.len(),
    ) {
      (Some(projection), true) => {
        let mut array = Vec::with_capacity(9);
        for i in 0..9 {
          array.push(projection[i as usize])
        }
        Ok(array)
      }
      _ => Err(pyo3::exceptions::PyValueError::new_err(format!(
        "Expected 2 or 4 x/y points for output quad (got {}) and 0, 1, 2, or 4 points for the coordinate basis (got {})",
        quad.len(),
        basis.len()
      ))),
    }
  }

  // -- ctm property ----------------------------------------------------------------------

  pub fn get_current_transform(&self) -> Vec<f32> {
    let mut array = Vec::with_capacity(9);
    for i in 0..9 {
      array.push(self.state.matrix[i as usize])
    }
    array
  }

  pub fn set_current_transform(&mut self, matrix: Vec<f32>) -> PyResult<()> {
    let matrix = to_matrix(&matrix).ok_or_else(|| {
      pyo3::exceptions::PyValueError::new_err("Matrix must be a 6 or 9 element array")
    })?;
    self.with_matrix(|ctm| ctm.reset().pre_concat(&matrix));
    Ok(())
  }

  //
  // Bézier Paths
  //

  pub fn begin_path(&mut self) {
    self.path = Path::new();
  }

  // -- primitives ------------------------------------------------------------------------

  pub fn rect(&mut self, x: f32, y: f32, width: f32, height: f32) {
    let rect = Rect::from_xywh(x, y, width, height);
    let quad = self.state.matrix.map_rect_to_quad(rect);
    self.path.move_to(quad[0]);
    self.path.line_to(quad[1]);
    self.path.line_to(quad[2]);
    self.path.line_to(quad[3]);
    self.path.close();
  }

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

    let matrix = self.state.matrix;
    let path = Path::rrect(rrect, Some(direction));
    self
      .path
      .add_path(&path.with_transform(&matrix), (0, 0), Extend);
  }

  pub fn arc(
    &mut self,
    x: f32,
    y: f32,
    radius: f32,
    start_angle: f32,
    end_angle: f32,
    counterclockwise: bool,
  ) {
    let matrix = self.state.matrix;
    let mut arc = Path2D::default();
    arc.add_ellipse(
      (x, y),
      (radius, radius),
      0.0,
      start_angle,
      end_angle,
      counterclockwise,
    );
    self
      .path
      .add_path(&arc.path.with_transform(&matrix), (0, 0), Extend);
  }

  pub fn ellipse(
    &mut self,
    x: f32,
    y: f32,
    radius_x: f32,
    radius_y: f32,
    rotation: f32,
    start_angle: f32,
    end_angle: f32,
    counterclockwise: bool,
  ) -> PyResult<()> {
    if radius_x < 0.0 || radius_y < 0.0 {
      return Err(pyo3::exceptions::PyValueError::new_err(
        "Radius values must be positive",
      ));
    }
    let matrix = self.state.matrix;
    let mut arc = Path2D::default();
    arc.add_ellipse(
      (x, y),
      (radius_x, radius_y),
      rotation,
      start_angle,
      end_angle,
      counterclockwise,
    );
    self
      .path
      .add_path(&arc.path.with_transform(&matrix), (0, 0), Extend);
    Ok(())
  }

  // contour drawing ----------------------------------------------------------------------

  pub fn move_to(&mut self, x: f32, y: f32) {
    let xy = vec![x, y];
    if let Some(dst) = self.map_points(&xy).first() {
      self.path.move_to(*dst);
    }
  }

  pub fn line_to(&mut self, x: f32, y: f32) {
    let xy = vec![x, y];
    if let Some(dst) = self.map_points(&xy).first() {
      self.path.line_to(*dst);
    }
  }

  pub fn arc_to(&mut self, x1: f32, y1: f32, x2: f32, y2: f32, radius: f32) -> PyResult<()> {
    let coords = vec![x1, y1, x2, y2];
    if radius < 0.0 {
      return Err(pyo3::exceptions::PyValueError::new_err(
        "Radius value must be positive",
      ));
    }

    if let [src, dst] = self.map_points(&coords)[..2] {
      self.scoot(src);
      self.path.arc_to_tangent(src, dst, radius);
    }
    Ok(())
  }

  pub fn bezier_curve_to(&mut self, cp1x: f32, cp1y: f32, cp2x: f32, cp2y: f32, x: f32, y: f32) {
    let coords = vec![cp1x, cp1y, cp2x, cp2y, x, y];
    if let [cp1, cp2, dst] = self.map_points(&coords)[..3] {
      self.scoot(cp1);
      self.path.cubic_to(cp1, cp2, dst);
    }
  }

  pub fn quadratic_curve_to(&mut self, cpx: f32, cpy: f32, x: f32, y: f32) {
    let coords = vec![cpx, cpy, x, y];
    if let [cp, dst] = self.map_points(&coords)[..2] {
      self.scoot(cp);
      self.path.quad_to(cp, dst);
    }
  }

  pub fn conic_curve_to(&mut self, cpx: f32, cpy: f32, x: f32, y: f32, weight: f32) {
    let coords = vec![cpx, cpy, x, y];
    if let [src, dst] = self.map_points(&coords).as_slice() {
      self.scoot(*src);
      self.path.conic_to(*src, *dst, weight);
    }
  }

  pub fn close_path(&mut self) {
    self.path.close();
  }

  // hit testing --------------------------------------------------------------------------
  pub fn is_point_in_path(
    &mut self,
    path: Option<&Path2D>,
    x: f32,
    y: f32,
    fill_rule: Option<String>,
  ) -> PyResult<bool> {
    self._is_in(path, x, y, fill_rule, Fill)
  }

  pub fn is_point_in_stroke(&mut self, path: Option<&Path2D>, x: f32, y: f32) -> PyResult<bool> {
    self._is_in(path, x, y, None, Stroke)
  }

  // masking ------------------------------------------------------------------------------

  pub fn clip(&mut self, path: Option<&Path2D>, fill_rule: Option<String>) -> PyResult<()> {
    let path = path.map(|p| p.path.clone());

    let rule = to_fill_rule_or_error(&fill_rule.unwrap_or("nonzero".to_string()))?;

    self.clip_path(path, rule);
    Ok(())
  }

  //
  // Fill & Stroke
  //

  pub fn fill(&mut self, path: Option<&Path2D>, fill_rule: Option<String>) -> PyResult<()> {
    let path = path.map(|p| p.path.clone());

    let rule = to_fill_rule_or_error(&fill_rule.unwrap_or("nonzero".to_string()))?;

    self.draw_path(path, PaintStyle::Fill, Some(rule));
    Ok(())
  }

  pub fn stroke(&mut self, path: Option<&Path2D>) {
    let path = path.map(|p| p.path.clone());
    self.draw_path(path, PaintStyle::Stroke, None);
  }

  pub fn fill_rect(&mut self, x: f32, y: f32, width: f32, height: f32) {
    let rect = Rect::from_xywh(x, y, width, height);
    let path = Path::rect(rect, None);
    self.draw_path(Some(path), PaintStyle::Fill, None);
  }

  pub fn stroke_rect(&mut self, x: f32, y: f32, width: f32, height: f32) {
    let rect = Rect::from_xywh(x, y, width, height);
    let path = Path::rect(rect, None);
    self.draw_path(Some(path), PaintStyle::Stroke, None);
  }

  #[pyo3(name = "clear_rect")]
  pub fn clear_rect_py(&mut self, x: f32, y: f32, width: f32, height: f32) {
    let rect = Rect::from_xywh(x, y, width, height);
    self.clear_rect(&rect);
  }

  // fill & stoke properties --------------------------------------------------------------

  pub fn get_fill_style(&self) -> Option<String> {
    let dye = self.state.fill_style.clone();
    dye.value()
  }

  pub fn set_fill_style(&mut self, value: DyeValue) {
    if let Some(dye) = Dye::new(value) {
      self.state.fill_style = dye;
    }
  }

  pub fn get_stroke_style(&self) -> Option<String> {
    let dye = self.state.stroke_style.clone();
    dye.value()
  }

  pub fn set_stroke_style(&mut self, value: DyeValue) {
    if let Some(dye) = Dye::new(value) {
      self.state.stroke_style = dye;
    }
  }

  //
  // Line Style
  //

  pub fn set_line_dash_marker(&mut self, path: Option<&Path2D>) {
    self.state.line_dash_marker = path.map(|p| p.path.clone());
  }

  pub fn get_line_dash_marker(&self) -> Option<Path2D> {
    self
      .state
      .line_dash_marker
      .as_ref()
      .map(|path| Path2D { path: path.clone() })
  }

  pub fn set_line_dash_fit(&mut self, fit_style: String) {
    if let Some(fit) = to_1d_style(&fit_style) {
      self.state.line_dash_fit = fit;
    }
  }

  pub fn get_line_dash_fit(&self) -> String {
    from_1d_style(self.state.line_dash_fit)
  }

  pub fn get_line_dash(&self) -> Vec<f32> {
    self.state.line_dash_list.clone()
  }

  pub fn set_line_dash(&mut self, mut segments: Vec<f32>) {
    if segments.len() % 2 == 1 {
      segments.append(&mut segments.clone());
    }
    self.state.line_dash_list = segments;
  }

  // line style properties  -----------------------------------------------------------

  pub fn get_line_cap(&self) -> String {
    let mode = self.state.paint.stroke_cap();
    from_stroke_cap(mode)
  }

  pub fn set_line_cap(&mut self, cap: String) {
    if let Some(mode) = to_stroke_cap(&cap) {
      self.state.paint.set_stroke_cap(mode);
    }
  }

  pub fn get_line_dash_offset(&self) -> f32 {
    self.state.line_dash_offset
  }

  pub fn set_line_dash_offset(&mut self, offset: f32) {
    self.state.line_dash_offset = offset;
  }

  pub fn get_line_join(&self) -> String {
    let mode = self.state.paint.stroke_join();
    from_stroke_join(mode)
  }

  pub fn set_line_join(&mut self, join: String) {
    if let Some(mode) = to_stroke_join(&join) {
      self.state.paint.set_stroke_join(mode);
    }
  }

  pub fn get_line_width(&self) -> f32 {
    self.state.paint.stroke_width()
  }

  pub fn set_line_width(&mut self, num: f32) {
    if num > 0.0 {
      self.state.paint.set_stroke_width(num);
      self.state.stroke_width = num;
    }
  }

  pub fn get_miter_limit(&self) -> f32 {
    self.state.paint.stroke_miter()
  }

  pub fn set_miter_limit(&mut self, num: f32) {
    if num > 0.0 {
      self.state.paint.set_stroke_miter(num);
    }
  }

  #[pyo3(name = "draw_image")]
  pub fn draw_image_py(&mut self, source: ImageValue, nums: Vec<f32>) -> PyResult<()> {
    let (content, fit_to_canvas) = match source {
      ImageValue::Image(img) => (img.content.clone(), img.autosized),
      ImageValue::Context2D(mut ctx) => (Content::from_context(&mut ctx, false), false),
      ImageValue::ImageData(data) => (Content::from_image_data(data), false),
    };

    if let Content::Bitmap(img) = &content {
      let bounds_size = content.size();
      let (src, dst) = _layout_rects(bounds_size, &nums)?;

      content.snap_rects_to_bounds(src, dst);
      self.draw_image(img, &src, &dst);
    } else if let Content::Vector(pict, pict_size) = &content {
      let (mut src, mut dst) = _layout_rects(*pict_size, &nums)?;

      // for SVG images with no intrinsic size, use the canvas size as a default scale
      if fit_to_canvas && nums.len() != 4 {
        let canvas_size = self.bounds.size();
        let canvas_min = canvas_size.width.min(canvas_size.height);
        let pict_min = pict_size.width.min(pict_size.height);

        if nums.len() == 2 {
          // if the user doesn't specify a size, proportionally scale to fit within canvas
          let factor = canvas_min / pict_min;
          dst = Rect::from_point_and_size((dst.x(), dst.y()), dst.size() * factor);
        } else if nums.len() == 8 {
          // if clipping out part of the source, map the crop coordinates as if the image is canvas-sized
          let factor = (pict_size.width / canvas_min, pict_size.height / canvas_min);
          (src, _) = Matrix::scale(factor).map_rect(src);
        }
      }

      content.snap_rects_to_bounds(src, dst);
      self.draw_picture(pict, &src, &dst);
    }

    Ok(())
  }

  pub fn draw_canvas(&mut self, context: &mut Context2D, nums: Vec<f32>) -> PyResult<()> {
    let content = Content::from_context(context, true);
    if let Content::Vector(pict, size) = &content {
      let (src, dst) = _layout_rects(*size, &nums)?;
      let (src, dst) = content.snap_rects_to_bounds(src, dst);
      self.draw_picture(pict, &src, &dst);
      Ok(())
    } else {
      Err(pyo3::exceptions::PyRuntimeError::new_err(
        "Canvas's PictureRecorder failed to generate an image",
      ))
    }
  }

  pub fn get_image_data(
    &mut self,
    x: f32,
    y: f32,
    width: f32,
    height: f32,
    opts: Option<ImageDataExportArg>,
    canvas: &mut Canvas,
  ) -> PyResult<Vec<u8>> {
    let mut x = x.floor();
    let mut y = y.floor();
    let mut w = width.floor();
    let mut h = height.floor();
    let ImageDataExportArg {
      color_type,
      color_space,
      matte,
      density,
      msaa,
    } = image_data_export_arg(opts);

    // negative dimensions are valid, just shift the origin and absify
    if w < 0.0 {
      x += w;
      w *= -1.0;
    }
    if h < 0.0 {
      y += h;
      h *= -1.0;
    }

    let opts = ExportOptions {
      matte,
      density,
      msaa,
      color_type,
      color_space,
      ..canvas.export_options()
    };
    let crop =
      Rect::from_point_and_size((x * density, y * density), (w * density, h * density)).round();
    let engine = canvas.engine();

    let data = self
      .get_pixels(crop, opts, engine)
      .map_err(pyo3::exceptions::PyRuntimeError::new_err)?;

    Ok(data)
  }

  pub fn put_image_data(&mut self, img_data: ImageData, x: f32, y: f32, mut dirty: Vec<f32>) {
    let (src, dst) = match dirty.as_mut_slice() {
      [dx, dy, dw, dh] => {
        // negative dimensions are valid, just shift the origin and absify
        if *dw < 0.0 {
          *dw *= -1.0;
          *dx -= *dw;
        }
        if *dh < 0.0 {
          *dh *= -1.0;
          *dy -= *dh;
        }
        (
          Rect::from_xywh(*dx, *dy, *dw, *dh),
          Rect::from_xywh(*dx + x, *dy + y, *dw, *dh),
        )
      }
      _ => (
        Rect::from_xywh(0.0, 0.0, img_data.width, img_data.height),
        Rect::from_xywh(x, y, img_data.width, img_data.height),
      ),
    };

    self.blit_pixels(img_data, &src, &dst);
  }

  // -- image properties --------------------------------------------------------------

  pub fn get_image_smoothing_enabled(&self) -> bool {
    self.state.image_filter.smoothing
  }

  pub fn set_image_smoothing_enabled(&mut self, enabled: bool) {
    self.state.image_filter.smoothing = enabled;
  }

  pub fn get_image_smoothing_quality(&self) -> String {
    from_filter_quality(self.state.image_filter.quality)
  }

  pub fn set_image_smoothing_quality(&mut self, name: String) {
    if let Some(mode) = to_filter_quality(&name) {
      self.state.image_filter.quality = mode;
    }
  }

  //
  // Typography
  //

  pub fn fill_text(&mut self, text: String, x: f32, y: f32, width: Option<f32>) {
    self.draw_text(&text, x, y, width, Fill);
  }

  pub fn stroke_text(&mut self, text: String, x: f32, y: f32, width: Option<f32>) {
    self.draw_text(&text, x, y, width, Stroke);
  }

  #[pyo3(name = "measure_text")]
  pub fn measure_text_py(&mut self, text: String, width: Option<f32>) -> String {
    let text_matrics = self.measure_text(&text, width);
    text_matrics.to_string()
  }

  #[pyo3(name = "outline_text")]
  pub fn outline_text_py(&mut self, text: String, width: Option<f32>) -> Path2D {
    let path = self.outline_text(&text, width);
    Path2D { path }
  }

  // -- type properties ---------------------------------------------------------------

  pub fn get_font(&self) -> String {
    self.state.font.clone()
  }

  #[pyo3(name = "set_font")]
  pub fn set_font_py(&mut self, font: FontSpec) {
    self.set_font(font);
  }

  pub fn get_font_stretch(&self) -> String {
    from_width(self.state.font_width)
  }

  pub fn set_font_stretch(&mut self, stretch: String) {
    self.set_font_width(to_width(&stretch));
  }

  pub fn get_text_align(&self) -> String {
    from_text_align(self.state.graf_style.text_align())
  }

  pub fn set_text_align(&mut self, name: String) {
    if let Some(align) = to_text_align(&name) {
      self.state.graf_style.set_text_align(align);
    }
  }

  pub fn get_text_baseline(&self) -> String {
    from_text_baseline(self.state.text_baseline)
  }

  pub fn set_text_baseline(&mut self, name: String) {
    if let Some(baseline) = to_text_baseline(&name) {
      self.state.text_baseline = baseline;
    }
  }

  pub fn get_direction(&self) -> String {
    let name = match self.state.graf_style.text_direction() {
      TextDirection::LTR => "ltr",
      TextDirection::RTL => "rtl",
    };
    name.to_string()
  }

  pub fn set_direction(&mut self, name: String) {
    let direction = match name.to_lowercase().as_str() {
      "ltr" => Some(TextDirection::LTR),
      "rtl" => Some(TextDirection::RTL),
      _ => None,
    };

    if let Some(dir) = direction {
      self.state.graf_style.set_text_direction(dir);
    }
  }

  pub fn get_letter_spacing(&self) -> String {
    self.state.letter_spacing.to_string()
  }

  pub fn set_letter_spacing(&mut self, spacing: Spacing) {
    let em_size = self.state.char_style.font_size();
    self
      .state
      .char_style
      .set_letter_spacing(spacing.in_px(em_size));
    self.state.letter_spacing = spacing;
  }

  pub fn get_word_spacing(&self) -> String {
    self.state.word_spacing.to_string()
  }

  pub fn set_word_spacing(&mut self, spacing: Spacing) {
    let em_size = self.state.char_style.font_size();
    self
      .state
      .char_style
      .set_word_spacing(spacing.in_px(em_size));
    self.state.word_spacing = spacing;
  }

  // -- non-standard typography extensions --------------------------------------------

  pub fn get_font_hinting(&self) -> bool {
    self.state.font_hinting
  }

  pub fn set_font_hinting(&mut self, flag: bool) {
    self.state.font_hinting = flag;
  }

  pub fn get_font_variant(&self) -> String {
    self.state.font_variant.clone()
  }

  #[pyo3(name = "set_font_variant")]
  pub fn set_font_variant_py(&mut self, val: FontVariantPy) {
    self.set_font_variant(&val.variant, &val.features);
  }

  pub fn get_text_wrap(&self) -> bool {
    self.state.text_wrap
  }

  pub fn set_text_wrap(&mut self, flag: bool) {
    self.state.text_wrap = flag;
  }

  pub fn get_text_decoration(&self) -> String {
    self.state.text_decoration.css.clone()
  }

  pub fn set_text_decoration(&mut self, style: DecorationStyle) {
    self.state.text_decoration = style;
  }

  //
  // Effects
  //

  // -- compositing properties --------------------------------------------------------

  pub fn get_global_alpha(&self) -> f32 {
    self.state.global_alpha
  }

  pub fn set_global_alpha(&mut self, alpha: f32) {
    if (0.0..=1.0).contains(&alpha) {
      self.state.global_alpha = alpha;
    }
  }

  pub fn get_global_composite_operation(&self) -> String {
    from_blend_mode(self.state.global_composite_operation)
  }

  pub fn set_global_composite_operation(&mut self, name: String) {
    if let Some(mode) = to_blend_mode(&name) {
      self.state.global_composite_operation = mode;
      self.state.paint.set_blend_mode(mode);
    }
  }

  // -- css3 filters ------------------------------------------------------------------

  pub fn get_filter(&self) -> String {
    self.state.filter.to_string()
  }

  pub fn set_filter(&mut self, arg: FilterPy) {
    if arg.canonical != self.state.filter.to_string() {
      self.state.filter = Filter::new(&arg.canonical, &arg.filters);
    }
  }

  // -- dropshadow properties ---------------------------------------------------------

  pub fn get_shadow_blur(&self) -> f32 {
    self.state.shadow_blur
  }

  pub fn set_shadow_blur(&mut self, num: f32) {
    if num >= 0.0 {
      self.state.shadow_blur = num;
    }
  }

  pub fn get_shadow_color(&self) -> String {
    let shadow_color = self.state.shadow_color;
    color_to_css(&shadow_color)
  }

  pub fn set_shadow_color(&mut self, color: String) {
    if let Some(parsed_color) = css_to_color(&color) {
      self.state.shadow_color = parsed_color;
    }
  }

  pub fn get_shadow_offset_x(&self) -> f32 {
    self.state.shadow_offset.x
  }

  pub fn get_shadow_offset_y(&self) -> f32 {
    self.state.shadow_offset.y
  }

  pub fn set_shadow_offset_x(&mut self, num: f32) {
    self.state.shadow_offset.x = num;
  }

  pub fn set_shadow_offset_y(&mut self, num: f32) {
    self.state.shadow_offset.y = num;
  }
}

impl Context2D {
  pub fn _is_in(
    &mut self,
    path: Option<&Path2D>,
    x: f32,
    y: f32,
    fill_rule: Option<String>,
    style: PaintStyle,
  ) -> PyResult<bool> {
    let path = path.map(|p| p.path.clone());
    let mut target = match path {
      Some(p) => p,
      None => self.path.clone(),
    };

    let rule = match style {
      Stroke => None,
      _ => {
        let fill_rule = fill_rule.unwrap_or("nonzero".to_string());
        Some(to_fill_rule_or_error(&fill_rule)?)
      }
    };

    Ok(self.hit_test_path(&mut target, (x, y), rule, style))
  }
}

fn _layout_rects(intrinsic: Size, nums: &[f32]) -> PyResult<(Rect, Rect)> {
  let (src, dst) = match nums.len() {
    2 => (
      Rect::from_xywh(0.0, 0.0, intrinsic.width, intrinsic.height),
      Rect::from_xywh(nums[0], nums[1], intrinsic.width, intrinsic.height),
    ),
    4 => (
      Rect::from_xywh(0.0, 0.0, intrinsic.width, intrinsic.height),
      Rect::from_xywh(nums[0], nums[1], nums[2], nums[3]),
    ),
    8 => (
      Rect::from_xywh(nums[0], nums[1], nums[2], nums[3]),
      Rect::from_xywh(nums[4], nums[5], nums[6], nums[7]),
    ),
    9.. => Err(pyo3::exceptions::PyValueError::new_err(format!(
      "Expected 2, 4, or 8 coordinates (got {})",
      nums.len()
    )))?,
    _ => Err(pyo3::exceptions::PyValueError::new_err(format!(
      "not enough arguments: Expected 2, 4, or 8 coordinates (got {})",
      nums.len()
    )))?,
  };

  match intrinsic.is_empty() {
    true => Err(pyo3::exceptions::PyValueError::new_err(format!(
      "Dimensions must be non-zero (got {}×{})",
      intrinsic.width, intrinsic.height
    ))),
    false => Ok((src, dst)),
  }
}

#[derive(FromPyObject)]
pub enum ImageValue<'a> {
  Image(PyRef<'a, Image>),
  Context2D(PyRefMut<'a, Context2D>),
  ImageData(ImageData),
}

pub struct FontVariantPy {
  variant: String,
  features: Vec<(String, i32)>,
}

impl FromPyObject<'_, '_> for FontVariantPy {
  type Error = PyErr;

  fn extract(obj: Borrowed<'_, '_, PyAny>) -> Result<Self, Self::Error> {
    let variant = string_for_key(obj, "variant")?;
    let feat_obj = obj.getattr("features")?;
    let features = font_features(&feat_obj)?;
    Ok(FontVariantPy { variant, features })
  }
}
