from __future__ import annotations

import base64
import json
import math
import os
import re
import warnings

from typing import TYPE_CHECKING, Literal, List, overload, TypedDict

from ..skia_canvas_pyr import (
    CanvasTexture as CanvasTextureRs,
    CanvasGradient as CanvasGradientRs,
    CanvasPattern as CanvasPatternRs,
    Canvas as CanvasRs,
)
from .imagery import Image, ImageData, _pixel_size
from .geometry import toSkMatrix, Matrix
from .path import Path2D
from .sc_type import (
    CanvasLineCap,
    Offset,
    CanvasInitOptions,
    ExportOptions,
    SaveOptions,
    EngineDetails,
)

if TYPE_CHECKING:
    from .context import CanvasRenderingContext2D


class Canvas:
    __slots__ = ("__contexts", "__canvas", "__weakref__")

    def __init__(
        self,
        width: float | None = None,
        height: float | None = None,
        opt: CanvasInitOptions | None = None,
    ):
        opt = opt or {}
        self.__canvas = CanvasRs(
            opt.get("text_contrast", 0),
            opt.get("text_gamma", 1.4),
            opt.get("gpu", True),
        )
        self.__contexts: List[CanvasRenderingContext2D] = []
        self.width = width
        self.height = height

    def getContext(self, kind: Literal["2d"]):
        if kind == "2d":
            return self.__contexts[0] if self.__contexts else self.newPage()

    @property
    def gpu(self) -> bool:
        return self.__canvas.get_engine() == "gpu"

    @gpu.setter
    def gpu(self, mode: bool) -> None:
        self.__canvas.set_engine("gpu" if mode else "cpu")

    @property
    def engine(self) -> EngineDetails:
        return json.loads(self.__canvas.get_engine_status())

    @property
    def width(self) -> float:
        return self.__canvas.get_width()

    @width.setter
    def width(self, value: float | None) -> None:
        self.__canvas.set_width(
            value if value is not None and math.isfinite(value) and value >= 0 else 300
        )
        if self.__contexts:
            self.__contexts[0].raw_reset_size()

    @property
    def height(self) -> float:
        return self.__canvas.get_height()

    @height.setter
    def height(self, value: float | None) -> None:
        self.__canvas.set_height(
            value if value is not None and math.isfinite(value) and value >= 0 else 150
        )
        if self.__contexts:
            self.__contexts[0].raw_reset_size()

    def newPage(self, *args: float) -> CanvasRenderingContext2D:
        from .context import CanvasRenderingContext2D

        ctx = CanvasRenderingContext2D(self)
        self.__contexts.insert(0, ctx)
        if args:
            self.width, self.height = args
        return ctx

    @property
    def pages(self) -> List[CanvasRenderingContext2D]:
        ctxs = self.__contexts[:]
        ctxs.reverse()
        return ctxs

    def saveAsSync(self, filename: str, opt: SaveOptions | None = None) -> None:
        warnings.warn(
            "Canvas.saveAsSync is deprecated; use Canvas.toFileSync instead",
            DeprecationWarning,
            stacklevel=2,
        )
        self.toFileSync(filename, opt)

    def toFileSync(self, filename: str, opts: SaveOptions | None = None) -> None:
        result = _export_options(self, opts, filename)
        pages = list(map(lambda x: x.core(), result["pages"]))
        padding = result["padding"]
        pattern = result["pattern"]
        self.__canvas.save_sync(pages, pattern, padding, result)

    def toBufferSync(
        self, extension: str = "png", opts: ExportOptions | None = None
    ) -> bytes:
        result = _export_options(self, opts, extension=extension)
        pages = list(map(lambda x: x.core(), result["pages"]))
        return self.__canvas.to_buffer_sync(pages, result)

    def toURLSync(
        self, extension: str = "png", opts: ExportOptions | None = None
    ) -> str:
        result = _export_options(self, opts, extension=extension)
        mime = result["mime"]
        buffer = self.toBufferSync(extension, opts)
        return f"data:{mime};base64,{base64.b64encode(buffer).decode()}"

    def toDataURL(self, extension: str = "png", quality: float | None = None, /) -> str:
        if quality is not None and not isinstance(quality, (int, float)):
            raise TypeError("Expected a number between 0.0-1.0 for `quality`")
        return self.toURLSync(
            extension, {"quality": quality} if quality is not None else None
        )

    def core(self) -> CanvasRs:
        return self.__canvas

    def raw_set_width(self, value: float) -> None:
        self.__canvas.set_width(value)

    def raw_set_height(self, value: float) -> None:
        self.__canvas.set_height(value)


class CanvasTexture:
    __slots__ = ("__texture",)

    def __init__(
        self,
        spacing: Offset,
        path: Path2D | None = None,
        line: float | None = None,
        cap: CanvasLineCap = "butt",
        color: str | None = None,
        angle: float | None = None,
        offset: Offset = 0,
        outline: bool = False,
    ):
        if isinstance(offset, list):
            x, y = (offset + offset)[:2]
        elif isinstance(offset, tuple):
            x, y = (offset + offset)[:2]
        elif isinstance(offset, (int, float)):
            x = y = offset
        else:
            raise TypeError("Expected a number or array for `offset`")
        if isinstance(spacing, list):
            h, v = (spacing + spacing)[:2]
        elif isinstance(spacing, tuple):
            h, v = (spacing + spacing)[:2]
        elif isinstance(spacing, (int, float)):
            h = v = spacing
        else:
            raise TypeError("Expected a number or array for `spacing`")

        if path is not None and not isinstance(path, Path2D):
            raise TypeError("Expected a Path2D for `path`")

        path_rs = path.core() if path is not None else None
        if line is None:
            line = 0 if path_rs else 1
        if angle is None:
            angle = 0 if path_rs else -math.pi / 4

        self.__texture = CanvasTextureRs(
            line,
            cap,
            angle,
            outline,
            h,
            v,
            x,
            y,
            path_rs,
            color,
        )

    def __repr__(self) -> str:
        return f"CanvasTexture({self.__texture.repr()})"

    __str__ = __repr__

    def core(self) -> CanvasTextureRs:
        return self.__texture


class CanvasGradient:
    __slots__ = ("__gradient",)

    def __init__(self, style: Literal["Linear", "Radial", "Conic"], *args: float):
        match style.lower():
            case "linear":
                self.__gradient = CanvasGradientRs.linear(*args)
            case "radial":
                self.__gradient = CanvasGradientRs.radial(*args)
            case "conic":
                self.__gradient = CanvasGradientRs.conic(*args)
            case _:
                raise ValueError("Invalid gradient style")

    def addColorStop(self, offset: float, color: str) -> None:
        self.__gradient.add_color_stop(offset, color)

    def core(self) -> CanvasGradientRs:
        return self.__gradient


class CanvasPattern:
    __slots__ = ("__pattern",)

    def __init__(
        self,
        canvas: Canvas,
        src: Canvas | Image | ImageData,
        repetition: (
            Literal["repeat", "repeat-x", "repeat-y", "no-repeat"] | None
        ) = None,
    ) -> None:
        if isinstance(src, Image):
            self.__pattern = CanvasPatternRs.from_image(
                src.core(), canvas.width, canvas.height, repetition
            )
        elif isinstance(src, ImageData):
            self.__pattern = CanvasPatternRs.from_image_data(src, repetition)
        elif isinstance(src, Canvas):
            ctx = src.getContext("2d")
            self.__pattern = CanvasPatternRs.from_canvas(ctx.core(), repetition)
        else:
            raise TypeError("CanvasPatterns require a source Image or a Canvas")

    @overload
    def setTransform(
        self, a: float, b: float, c: float, d: float, e: float, f: float, /
    ) -> None: ...
    @overload
    def setTransform(self, matrix: Matrix, /) -> None: ...

    def setTransform(self, *args) -> None:
        matrix = toSkMatrix(*args)
        self.__pattern.set_transform(matrix)

    def __repr__(self) -> str:
        return f"CanvasPattern({self.__pattern.repr()})"

    __str__ = __repr__

    def core(self) -> CanvasPatternRs:
        return self.__pattern


#
# Validation of the options dict shared by the `saveAs`, `toBuffer`, and `toDataURL` methods
#

if TYPE_CHECKING:

    class ExportOptionsReturn(TypedDict):
        filename: str
        pattern: str
        format: str
        mime: str | None
        pages: List[CanvasRenderingContext2D]
        padding: float | None
        quality: float
        matte: str | None
        density: float
        msaa: float | None
        outline: bool
        text_contrast: float
        text_gamma: float
        downsample: bool
        color_type: str | None


def _export_options(
    canvas: Canvas,
    opts: ExportOptions | SaveOptions | float | None,
    filename="",
    extension="",
) -> ExportOptionsReturn:
    options: ExportOptions
    if opts is None:
        options = {}
    elif isinstance(opts, (int, float)):
        options = {"quality": opts}
    else:
        options = opts

    page = options.get("page")
    quality = options.get("quality")
    matte = options.get("matte")
    density = options.get("density")
    msaa = options.get("msaa")
    outline = options.get("outline")
    downsample = options.get("downsample")
    color_type = options.get("color_type", options.get("colorType"))

    # Only allow format overrides when exporting to file.
    image_format = options.get("format") if filename else None

    # Ensure the canvas has at least one context so we can export an empty image.
    if not canvas.pages:
        canvas.getContext("2d")

    formats = {
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "webp": "image/webp",
        "pdf": "application/pdf",
        "svg": "image/svg+xml",
        "raw": "application/octet-stream",
    }
    mimes = {
        "image/png": "png",
        "image/jpeg": "jpg",
        "image/webp": "webp",
        "application/octet-stream": "raw",
        "application/pdf": "pdf",
        "image/svg+xml": "svg",
    }
    expected = '"png", "jpg", "webp", "raw", "pdf", or "svg"'

    def to_mime(ext: str) -> str | None:
        return formats.get((ext or "").lstrip(".").lower())

    def from_mime(mime: str) -> str | None:
        return mimes.get((mime or "").lower())

    ext_raw = (
        image_format
        or re.sub(r"@\d+x$", "", extension or "", flags=re.IGNORECASE)
        or os.path.splitext(str(filename))[1]
    )
    ext = "" if ext_raw is None else str(ext_raw)
    fmt = from_mime(to_mime(ext) or str(ext))
    mime = to_mime(fmt or "")

    if not ext:
        raise ValueError(
            "Cannot determine image format (use a filename extension or 'format' argument)"
        )
    if not fmt:
        raise ValueError(f'Unsupported file format "{ext}" (expected {expected})')

    name = str(filename)
    padding: int | None = None
    is_sequence = False

    def _replace_pattern(match: re.Match[str]) -> str:
        nonlocal is_sequence, padding
        is_sequence = True
        width_str = match.group(1)
        width = int(width_str) if width_str else None
        if width is not None:
            padding = width
        elif padding is None:
            padding = -1
        return "{}"

    pattern = re.sub(r"{(\d*)}", _replace_pattern, name)

    pages = canvas.pages
    page_count = len(pages)

    idx: int | None = None
    if (
        isinstance(page, (int, float))
        and not isinstance(page, bool)
        and math.isfinite(page)
    ):
        raw_idx = page - 1 if page > 0 else (page_count + page if page < 0 else None)
        if raw_idx is not None:
            if int(raw_idx) != raw_idx:
                raise TypeError("Expected an integer value for `page`")
            idx = int(raw_idx)

    if idx is not None and (idx < 0 or idx >= page_count):
        if page_count == 1:
            raise IndexError(f"Canvas only has a page 1 ({idx} is out of bounds)")
        raise IndexError(f"Canvas has pages 1-{page_count} ({idx} is out of bounds)")

    if idx is not None:
        pages = [pages[idx]]
    elif is_sequence or fmt == "pdf":
        pages = pages
    else:
        pages = pages[-1:]

    # Keep canvas-level text rendering settings with the export options.
    engine = canvas.engine
    text_contrast = engine.get(
        "textContrast",
    )
    text_gamma = engine.get("textGamma")

    if quality is None:
        quality = 0.92
    elif (
        isinstance(quality, bool)
        or not isinstance(quality, (int, float))
        or not math.isfinite(float(quality))
        or quality < 0
        or quality > 1
    ):
        raise TypeError("Expected a number between 0.0-1.0 for `quality`")

    if density is None:
        base = extension or os.path.basename(name)
        stem = os.path.splitext(base)[0]
        match = re.search(r"@(\d+)x$", stem, flags=re.IGNORECASE)
        density = int(match.group(1), 10) if match else 1
    elif (
        isinstance(density, bool)
        or not isinstance(density, (int, float))
        or not float(density).is_integer()
        or density < 1
    ):
        raise TypeError("Expected a non-negative integer for `density`")
    else:
        density = int(density)

    if msaa is None or msaa is True:
        msaa = None
    else:
        try:
            msaa = float(msaa)
        except (TypeError, ValueError):
            raise TypeError(
                "The number of MSAA samples must be an integer >=0"
            ) from None
        if not math.isfinite(msaa) or msaa < 0:
            raise TypeError("The number of MSAA samples must be an integer >=0")

    if color_type is not None:
        if not isinstance(color_type, str):
            raise TypeError("Expected a string value for `color_type`")
        _pixel_size(color_type)

    return {
        "filename": name,
        "pattern": pattern,
        "format": fmt,
        "mime": mime,
        "pages": pages,
        "padding": padding,
        "quality": float(quality),
        "matte": matte,
        "density": density,
        "msaa": float(msaa) if msaa is not None else None,
        "outline": bool(outline),
        "text_contrast": text_contrast,
        "text_gamma": text_gamma,
        "downsample": bool(downsample),
        "color_type": color_type,
    }
