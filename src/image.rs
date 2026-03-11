use pyo3::prelude::*;
use skia_safe::{
  AlphaType, ColorSpace, ColorType, Data, FontMgr, ISize, Image as SkImage, ImageInfo, Picture,
  PictureRecorder, Rect, Size,
  image::images,
  svg::{self, Length, LengthUnit},
};
use std::cell::RefCell;

// TODO
// use crate::context::Context2D;
use crate::font_library::FontLibrary;
use crate::utils::*;

#[pyclass]
pub struct Image {
  src: String,
  pub autosized: bool,
  pub content: Content,
}

impl Default for Image {
  fn default() -> Self {
    Image {
      content: Content::Loading,
      autosized: false,
      src: "".to_string(),
    }
  }
}

pub enum Content {
  Bitmap(SkImage),
  Vector(Picture, Size),
  Loading,
  Broken,
}

impl Default for Content {
  fn default() -> Self {
    Content::Loading
  }
}

impl Clone for Content {
  fn clone(&self) -> Self {
    match self {
      Content::Bitmap(img) => Content::Bitmap(img.clone()),
      Content::Vector(pict, size) => Content::Vector(pict.clone(), size.clone()),
      _ => Content::default(),
    }
  }
}

impl Content {
  //   pub fn from_context(ctx: &mut Context2D, use_vector: bool) -> Self {
  //     match use_vector {
  //       true => ctx
  //         .get_picture()
  //         .map(|p| Content::Vector(p, ctx.bounds.size())),
  //       false => ctx.get_image().map(|i| Content::Bitmap(i)),
  //     }
  //     .unwrap_or_default()
  //   }

  pub fn from_image_data(image_data: ImageData) -> Self {
    let info = image_data.image_info();
    images::raster_from_data(&info, &image_data.buffer, info.min_row_bytes())
      .map(|image| Content::Bitmap(image))
      .unwrap_or_default()
  }

  pub fn size(&self) -> Size {
    match &self {
      Content::Bitmap(img) => img.dimensions().into(),
      Content::Vector(_, size) => *size,
      _ => Size::new_empty(),
    }
  }

  pub fn is_complete(&self) -> bool {
    match &self {
      Content::Loading => false,
      _ => true,
    }
  }

  pub fn is_drawable(&self) -> bool {
    match &self {
      Content::Loading | Content::Broken => false,
      _ => true,
    }
  }

  pub fn snap_rects_to_bounds(&self, mut src: Rect, mut dst: Rect) -> (Rect, Rect) {
    // Handle 'overdraw' of the src image where the crop coordinates are outside of its bounds
    // Snap the src rect to its actual bounds and shift/pad the dst rect to account for the
    // whitespace included in the crop.
    let scale_x = dst.width() / src.width();
    let scale_y = dst.height() / src.height();
    let size = self.size();

    if src.left < 0.0 {
      dst.left += -src.left * scale_x;
      src.left = 0.0;
    }

    if src.top < 0.0 {
      dst.top += -src.top * scale_y;
      src.top = 0.0;
    }

    if src.right > size.width {
      dst.right -= (src.right - size.width) * scale_x;
      src.right = size.width;
    }

    if src.bottom > size.height {
      dst.bottom -= (src.bottom - size.height) * scale_y;
      src.bottom = size.height;
    }

    (src, dst)
  }
}

#[derive(Debug)]
pub struct ImageData {
  pub width: f32,
  pub height: f32,
  pub buffer: Data,
  color_type: ColorType,
  color_space: ColorSpace,
}

impl ImageData {
  pub fn new(
    buffer: Data,
    width: f32,
    height: f32,
    color_type: String,
    color_space: String,
  ) -> Self {
    let color_type = to_color_type(&color_type);
    let color_space = to_color_space(&color_space);
    Self {
      buffer,
      width,
      height,
      color_type,
      color_space,
    }
  }

  pub fn image_info(&self) -> ImageInfo {
    ImageInfo::new(
      (self.width as _, self.height as _),
      self.color_type,
      AlphaType::Unpremul,
      self.color_space.clone(),
    )
  }
}

/* #region Python Methods */

#[pymethods]
impl Image {
  #[new]
  pub fn new() -> Self {
    Image::default()
  }

  pub fn get_src(&self) -> String {
    self.src.clone()
  }

  pub fn set_src(&mut self, src: String) {
    self.src = src;
  }

  pub fn set_data(&mut self, buffer: &[u8]) -> bool {
    let data = Data::new_copy(buffer);

    if let Some(image) = images::deferred_from_encoded_data(&data, None) {
      // Next, try interpreting the data as an encoded bitmap
      self.content = Content::Bitmap(image);
    } else if let Ok(mut dom) =
      svg::Dom::from_bytes(&data, FontLibrary::with_shared(|lib| lib.font_mgr()))
    {
      // Finally, try parsing as SVG
      let root = dom.root();

      let mut size = root.intrinsic_size();
      if size.is_empty() {
        // flag that image lacks an intrinsic size so it will be drawn to match the canvas size
        // if dimensions aren't provided in the drawImage() call
        self.autosized = true;

        // If width or height attributes aren't defined on the root `<svg>` element, they will be reported as "100%".
        // If only one is defined, use it for both dimensions, and if both are missing use the aspect ratio to scale the
        // width vs a fixed height of 150 (i.e., Chrome's behavior)
        let Length {
          value: width,
          unit: w_unit,
        } = root.width();
        let Length {
          value: height,
          unit: h_unit,
        } = root.height();
        size = match ((width, w_unit), (height, h_unit)) {
          // NB: only unitless numeric lengths are currently being handled; values in em, cm, in, etc. are ignored,
          // but perhaps they should be converted to px?
          ((100.0, LengthUnit::Percentage), (height, LengthUnit::Number)) => {
            (*height, *height).into()
          }
          ((width, LengthUnit::Number), (100.0, LengthUnit::Percentage)) => (*width, *width).into(),
          _ => {
            let aspect = root
              .view_box()
              .map(|vb| vb.width() / vb.height())
              .unwrap_or(1.0);
            (150.0 * aspect, 150.0).into()
          }
        };
      };

      // Save the SVG contents as a Picture (to be drawn later)
      let bounds = Rect::from_size(size);
      let mut compositor = PictureRecorder::new();
      dom.set_container_size(bounds.size());
      dom.render(compositor.begin_recording(bounds, true));
      self.content = match compositor.finish_recording_as_picture(None) {
        Some(picture) => Content::Vector(picture, size),
        None => Content::Broken,
      };
    } else {
      self.content = Content::Broken
    }

    self.content.is_drawable()
  }

  pub fn get_width(&self) -> f32 {
    self.content.size().width
  }

  pub fn get_height(&self) -> f32 {
    self.content.size().height
  }

  pub fn get_complete(&self) -> bool {
    self.content.is_complete()
  }

  pub fn pixels(
    &mut self,
    color_type: Option<String>,
    color_space: Option<String>,
  ) -> Option<Vec<u8>> {
    let color_type = color_type
      .map(|t| to_color_type(&t))
      .unwrap_or(ColorType::RGBA8888);
    let color_space = color_space
      .map(|m| to_color_space(&m))
      .unwrap_or(ColorSpace::new_srgb());

    let info = ImageInfo::new(
      self.content.size().to_floor(),
      color_type,
      AlphaType::Unpremul,
      color_space,
    );
    let mut pixels = vec![0; info.bytes_per_pixel() * (info.width() * info.height()) as usize];

    match &self.content {
      Content::Bitmap(image) => {
        match image.read_pixels(
          &info,
          pixels.as_mut_slice(),
          info.min_row_bytes(),
          (0, 0),
          skia_safe::image::CachingHint::Allow,
        ) {
          true => Some(pixels),
          false => None,
        }
      }
      _ => None,
    }
  }
}

/* #endregion */
