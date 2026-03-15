from typing import Literal, TypeAlias, TypedDict, Tuple, Union, List

CanvasDirection: TypeAlias = Literal["ltr", "rtl", "inherit"]
CanvasFillRule: TypeAlias = Literal["nonzero", "evenodd"]
CanvasFontStretch: TypeAlias = Literal[
    "condensed",
    "expanded",
    "extra-condensed",
    "extra-expanded",
    "normal",
    "semi-condensed",
    "semi-expanded",
    "ultra-condensed",
    "ultra-expanded",
]
CanvasTextAlign: TypeAlias = Literal[
    "center", "end", "left", "right", "start", "justify"
]
CanvasTextBaseline: TypeAlias = Literal[
    "alphabetic", "hanging", "ideographic", "middle", "top", "bottom"
]
CanvasLineCap: TypeAlias = Literal["butt", "round", "square"]
CanvasLineJoin: TypeAlias = Literal["bevel", "round", "miter"]
CanvasLineDashFit: TypeAlias = Literal["move", "turn", "follow"]

Offset: TypeAlias = List[float] | Tuple[float, float] | float
QuadOrRect: TypeAlias = Union[
    # [x1:number, y1:number, x2:number, y2:number, x3:number, y3:number, x4:number, y4:number]
    Tuple[float, float, float, float, float, float, float, float],
    # [left:number, top:number, right:number, bottom:number]
    Tuple[float, float, float, float],
    # [width:number, height:number]
    Tuple[float, float],
]
GlobalCompositeOperation: TypeAlias = Literal[
    "color",
    "color-burn",
    "color-dodge",
    "copy",
    "darken",
    "destination-atop",
    "destination-in",
    "destination-out",
    "destination-over",
    "difference",
    "exclusion",
    "hard-light",
    "hue",
    "lighten",
    "lighter",
    "luminosity",
    "multiply",
    "overlay",
    "saturation",
    "screen",
    "soft-light",
    "source-atop",
    "source-in",
    "source-out",
    "source-over",
    "xor",
]
ImageSmoothingQuality: TypeAlias = Literal["high", "medium", "low"]

FontVariantSetting: TypeAlias = Literal[
    "normal",
    "historical-forms",
    "small-caps",
    "all-small-caps",
    "petite-caps",
    "all-petite-caps",
    "unicase",
    "titling-caps",
    "lining-nums",
    "oldstyle-nums",
    "proportional-nums",
    "tabular-nums",
    "diagonal-fractions",
    "stacked-fractions",
    "ordinal",
    "slashed-zero",
    "common-ligatures",
    "no-common-ligatures",
    "discretionary-ligatures",
    "no-discretionary-ligatures",
    "historical-ligatures",
    "no-historical-ligatures",
    "contextual",
    "no-contextual",
    "jis78",
    "jis83",
    "jis90",
    "jis04",
    "simplified",
    "traditional",
    "full-width",
    "proportional-width",
    "ruby",
    "super",
    "sub",
]

ColorSpace: TypeAlias = Literal["srgb"]
ColorType: TypeAlias = Literal[
    "Alpha8",
    "Gray8",
    "R8UNorm",
    "A16Float",
    "A16UNorm",
    "ARGB4444",
    "R8G8UNorm",
    "RGB565",
    "rgb",
    "RGB888x",
    "rgba",
    "RGBA8888",
    "bgra",
    "BGRA8888",
    "BGR101010x",
    "BGRA1010102",
    "R16G16Float",
    "R16G16UNorm",
    "RGB101010x",
    "RGBA1010102",
    "RGBA8888",
    "SRGBA8888",
    "R16G16B16A16UNorm",
    "RGBAF16",
    "RGBAF16Norm",
    "RGBAF32",
]

ExportFormat: TypeAlias = Literal[
    "png",
    "jpg",
    "jpeg",
    "webp",
    "raw",
    "pdf",
    "svg",
]

FontOptions: TypeAlias = Literal["outline", "device-independent"]


class ImageDataSettings(TypedDict, total=False):
    color_type: str
    color_space: str


class ImageDataExportSettings(TypedDict, total=False):
    # Background color to draw beneath transparent parts of the canvas
    matte: str
    # Number of pixels per grid ‘point’ (defaults to 1)
    density: float
    # Number of samples used for antialising each pixel
    msaa: float | bool
    # Color space (must be "srgb")
    color_space: ColorSpace
    # Color type to use when exporting in "raw" format
    color_type: ColorType
