import dataclasses
import weakref
import json
import math
import warnings

from typing import overload, Sequence, Literal, List, Tuple, TypedDict

from . import css
from .canvas import Canvas, CanvasGradient, CanvasPattern, CanvasTexture
from .imagery import Image, ImageData
from .geometry import fromSkMatrix, toSkMatrix, DOMMatrix
from .path import Path2D
from .typography import TextMetrics
from ..skia_canvas_pyr import Context2D as Context2DRs
from .sc_type import (
    QuadOrRect,
    CanvasFillRule,
    Offset,
    CanvasLineCap,
    CanvasLineDashFit,
    CanvasLineJoin,
    CanvasDirection,
    CanvasFontStretch,
    CanvasTextAlign,
    CanvasTextBaseline,
    FontVariantSetting,
    GlobalCompositeOperation,
    ImageSmoothingQuality,
    ImageDataSettings,
    ImageDataExportSettings,
)
from .geometry import Matrix, DOMPointInit


@dataclasses.dataclass
class ImageDataExportOptions:
    color_type: str | None
    color_space: str | None
    matte: str | None
    density: float | None
    msaa: float | None


class CreateTextureOptions(TypedDict, total=False):
    path: Path2D
    line: float
    cap: CanvasLineCap
    color: str
    angle: float
    offset: Offset
    outline: bool


def _is_finite_number(value) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(value)


class CanvasRenderingContext2D:
    __slots__ = (
        "__context",
        "__canvas",
        "__fill",
        "__stroke",
    )

    def __init__(self, canvas: Canvas) -> None:
        self.__context = Context2DRs(canvas.core())
        self.__canvas = weakref.ref(canvas)
        self.__fill: CanvasGradient | CanvasPattern | CanvasTexture | None = None
        self.__stroke: CanvasGradient | CanvasPattern | CanvasTexture | None = None

    @property
    def canvas(self) -> Canvas | None:
        return self.__canvas()

    # -- global state & content reset ------------------------------------------
    def reset(self) -> None:
        self.__context.reset()

    # -- grid state ------------------------------------------------------------
    def save(self) -> None:
        self.__context.save()

    def restore(self) -> None:
        self.__context.restore()

    @property
    def currentTransform(self) -> DOMMatrix:
        return fromSkMatrix(self.__context.get_current_transform())

    @currentTransform.setter
    def currentTransform(self, value: Matrix) -> None:
        self.setTransform(value)

    def resetTransform(self) -> None:
        self.__context.reset_transform()

    def getTransform(self) -> DOMMatrix:
        return self.currentTransform

    def setTransform(self, matrix: Matrix) -> None:
        self.__context.set_current_transform(toSkMatrix(matrix))

    @overload
    def transform(self, transform: Matrix, /) -> None: ...
    @overload
    def transform(
        self,
        a: float,
        b: float,
        c: float,
        d: float,
        e: float,
        f: float,
        /,
    ) -> None: ...
    def transform(self, *args) -> None:
        matrix = toSkMatrix(*args)
        self.__context.transform(matrix)

    def translate(self, x: float, y: float) -> None:
        self.__context.translate(x, y)

    def scale(self, x: float, y: float) -> None:
        self.__context.scale(x, y)

    def rotate(self, angle: float) -> None:
        self.__context.rotate(angle)

    def createProjection(
        self, quad: QuadOrRect, basis: QuadOrRect | Tuple = ()
    ) -> DOMMatrix:
        return fromSkMatrix(self.__context.create_projection(quad, basis))

    # -- bézier paths ----------------------------------------------------------
    def beginPath(self) -> None:
        self.__context.begin_path()

    def rect(self, x: float, y: float, width: float, height: float) -> None:
        self.__context.rect(x, y, width, height)

    def arc(
        self,
        x: float,
        y: float,
        radius: float,
        start_angle: float,
        end_angle: float,
        counterclockwise: bool = False,
    ) -> None:
        self.__context.arc(x, y, radius, start_angle, end_angle, counterclockwise)

    def ellipse(
        self,
        x: float,
        y: float,
        radius_x: float,
        radius_y: float,
        rotation: float,
        start_angle: float,
        end_angle: float,
        counterclockwise: bool = False,
    ) -> None:
        self.__context.ellipse(
            x, y, radius_x, radius_y, rotation, start_angle, end_angle, counterclockwise
        )

    def moveTo(self, x: float, y: float) -> None:
        self.__context.move_to(x, y)

    def lineTo(self, x: float, y: float) -> None:
        self.__context.line_to(x, y)

    def arcTo(self, x1: float, y1: float, x2: float, y2: float, radius: float) -> None:
        self.__context.arc_to(x1, y1, x2, y2, radius)

    def bezierCurveTo(
        self, cp1x: float, cp1y: float, cp2x: float, cp2y: float, x: float, y: float
    ) -> None:
        self.__context.bezier_curve_to(cp1x, cp1y, cp2x, cp2y, x, y)

    def quadraticCurveTo(self, cpx: float, cpy: float, x: float, y: float) -> None:
        self.__context.quadratic_curve_to(cpx, cpy, x, y)

    def conicCurveTo(
        self, cpx: float, cpy: float, x: float, y: float, weight: float
    ) -> None:
        self.__context.conic_curve_to(cpx, cpy, x, y, weight)

    def closePath(self) -> None:
        self.__context.close_path()

    def roundRect(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        radii: float | DOMPointInit | Sequence[float | DOMPointInit],
    ):
        parsed = css.radii(radii)
        if parsed:
            if width < 0:
                parsed = [parsed[1], parsed[0], parsed[3], parsed[2]]
            if height < 0:
                parsed = [parsed[3], parsed[2], parsed[1], parsed[0]]
            radii_args = []
            for r in parsed:
                radii_args.append(r["x"])
                radii_args.append(r["y"])
            self.__context.round_rect(x, y, width, height, *radii_args)

    # -- using paths -----------------------------------------------------------
    @overload
    def fill(self) -> None: ...
    @overload
    def fill(self, path: Path2D, /) -> None: ...
    @overload
    def fill(self, rule: CanvasFillRule, /) -> None: ...
    @overload
    def fill(self, path: Path2D, rule: CanvasFillRule, /) -> None: ...
    def fill(
        self,
        *args,
    ) -> None:
        path_rs = None
        rule = None
        match len(args):
            case 0:
                pass
            case 1:
                if not isinstance(args[0], (Path2D, str)):
                    raise TypeError("Expected a Path2D or a CanvasFillRule argument")
                if isinstance(args[0], Path2D):
                    path_rs = args[0].core()
                else:
                    rule = args[0]
            case 2:
                if not isinstance(args[0], Path2D):
                    raise TypeError("Expected a Path2D as the first argument")
                if not isinstance(args[1], str):
                    raise TypeError("Expected a CanvasFillRule as the second argument")

                path_rs = args[0].core()
                rule = args[1]
            case _:
                raise TypeError("too many arguments for fill()")
        self.__context.fill(path_rs, rule)

    def stroke(self, path: Path2D | None = None) -> None:
        if path is not None and not isinstance(path, Path2D):
            raise TypeError("Expected a Path2D")
        self.__context.stroke(path and path.core())

    @overload
    def clip(self) -> None: ...
    @overload
    def clip(self, path: Path2D, /) -> None: ...
    @overload
    def clip(self, rule: CanvasFillRule, /) -> None: ...
    @overload
    def clip(self, path: Path2D, rule: CanvasFillRule, /) -> None: ...
    def clip(
        self,
        *args,
    ) -> None:
        path_rs = None
        rule = None
        match len(args):
            case 0:
                pass
            case 1:
                if not isinstance(args[0], (Path2D, str)):
                    raise TypeError("Expected a Path2D or a CanvasFillRule argument")
                if isinstance(args[0], Path2D):
                    path_rs = args[0].core()
                else:
                    rule = args[0]
            case 2:
                if not isinstance(args[0], Path2D):
                    raise TypeError("Expected a Path2D as the first argument")
                if not isinstance(args[1], str):
                    raise TypeError("Expected a CanvasFillRule as the second argument")

                path_rs = args[0].core()
                rule = args[1]
            case _:
                raise TypeError("too many arguments for clip()")
        self.__context.clip(path_rs, rule)

    @overload
    def isPointInPath(self, x: float, y: float, /) -> bool: ...
    @overload
    def isPointInPath(self, x: float, y: float, rule: CanvasFillRule, /) -> bool: ...
    @overload
    def isPointInPath(self, path: Path2D, x: float, y: float, /) -> bool: ...
    @overload
    def isPointInPath(
        self, path: Path2D, x: float, y: float, rule: CanvasFillRule, /
    ) -> bool: ...
    def isPointInPath(self, *args) -> bool:
        if isinstance(args[0], Path2D):
            match len(args):
                case 3:
                    return self.__context.is_point_in_path(
                        args[0].core(), args[1], args[2], None
                    )
                case 4:
                    return self.__context.is_point_in_path(
                        args[0].core(), args[1], args[2], args[3]
                    )
        else:
            match len(args):
                case 2:
                    return self.__context.is_point_in_path(None, args[0], args[1], None)
                case 3:
                    return self.__context.is_point_in_path(
                        None, args[0], args[1], args[2]
                    )
        raise TypeError("invalid arguments for isPointInPath")

    @overload
    def isPointInStroke(self, x: float, y: float, /) -> bool: ...
    @overload
    def isPointInStroke(self, path: Path2D, x: float, y: float, /) -> bool: ...
    def isPointInStroke(self, *args) -> bool:
        if isinstance(args[0], Path2D):
            if len(args) == 3:
                return self.__context.is_point_in_stroke(
                    args[0].core(), args[1], args[2]
                )
        else:
            if len(args) == 2:
                return self.__context.is_point_in_stroke(None, args[0], args[1])
        raise TypeError("invalid arguments for isPointInStroke")

    # -- shaders ---------------------------------------------------------------
    def createPattern(
        self,
        image: Image | Canvas,
        repetition: Literal["repeat", "repeat-x", "repeat-y", "no-repeat"] | None,
    ) -> CanvasPattern:
        assert self.canvas is not None
        return CanvasPattern(self.canvas, image, repetition)

    def createLinearGradient(
        self, x0: float, y0: float, x1: float, y1: float
    ) -> CanvasGradient:
        return CanvasGradient("Linear", x0, y0, x1, y1)

    def createRadialGradient(
        self, x0: float, y0: float, r0: float, x1: float, y1: float, r1: float
    ) -> CanvasGradient:
        return CanvasGradient("Radial", x0, y0, r0, x1, y1, r1)

    def createConicGradient(
        self, start_angle: float, x: float, y: float
    ) -> CanvasGradient:
        return CanvasGradient("Conic", start_angle, x, y)

    def createTexture(
        self,
        spacing: Offset,
        options: CreateTextureOptions | None = None,
    ) -> CanvasTexture:
        options = options or {}
        return CanvasTexture(spacing, **options)

    # -- fill & stroke ---------------------------------------------------------
    def fillRect(self, x: float, y: float, width: float, height: float) -> None:
        self.__context.fill_rect(x, y, width, height)

    def strokeRect(self, x: float, y: float, width: float, height: float) -> None:
        self.__context.stroke_rect(x, y, width, height)

    def clearRect(self, x: float, y: float, width: float, height: float) -> None:
        self.__context.clear_rect(x, y, width, height)

    @property
    def fillStyle(self) -> str | CanvasGradient | CanvasPattern | CanvasTexture | None:
        style = self.__context.get_fill_style()
        if style is None:
            return self.__fill
        else:
            return style

    @fillStyle.setter
    def fillStyle(
        self, value: str | CanvasGradient | CanvasPattern | CanvasTexture
    ) -> None:
        if isinstance(value, (CanvasGradient, CanvasPattern, CanvasTexture)):
            self.__context.set_fill_style(value.core())
            self.__fill = value
        elif isinstance(value, str):
            self.__context.set_fill_style(value)
            self.__fill = None

    @property
    def strokeStyle(
        self,
    ) -> str | CanvasGradient | CanvasPattern | CanvasTexture | None:
        style = self.__context.get_stroke_style()
        if style is None:
            return self.__stroke
        else:
            return style

    @strokeStyle.setter
    def strokeStyle(
        self, value: str | CanvasGradient | CanvasPattern | CanvasTexture
    ) -> None:
        if isinstance(value, (CanvasGradient, CanvasPattern, CanvasTexture)):
            self.__context.set_stroke_style(value.core())
            self.__stroke = value
        elif isinstance(value, str):
            self.__context.set_stroke_style(value)
            self.__stroke = None

    # -- line style ------------------------------------------------------------
    def getLineDash(self) -> List[float]:
        return self.__context.get_line_dash()

    def setLineDash(self, segments: Sequence[float]) -> None:
        self.__context.set_line_dash(segments)

    @property
    def lineCap(self) -> CanvasLineCap:
        return self.__context.get_line_cap()  # type: ignore

    @lineCap.setter
    def lineCap(self, value: str) -> None:
        self.__context.set_line_cap(value)

    @property
    def lineDashFit(self) -> CanvasLineDashFit:
        return self.__context.get_line_dash_fit()  # type: ignore

    @lineDashFit.setter
    def lineDashFit(self, value: str) -> None:
        self.__context.set_line_dash_fit(value)

    @property
    def lineDashMarker(self) -> Path2D:
        path = self.__context.get_line_dash_marker()
        return Path2D(path)

    @lineDashMarker.setter
    def lineDashMarker(self, value: Path2D | None) -> None:
        self.__context.set_line_dash_marker(value.core() if value is not None else None)

    @property
    def lineDashOffset(self) -> float:
        return self.__context.get_line_dash_offset()

    @lineDashOffset.setter
    def lineDashOffset(self, value: float) -> None:
        self.__context.set_line_dash_offset(value)

    @property
    def lineJoin(self) -> CanvasLineJoin:
        return self.__context.get_line_join()  # type: ignore

    @lineJoin.setter
    def lineJoin(self, value: str) -> None:
        self.__context.set_line_join(value)

    @property
    def lineWidth(self) -> float:
        return self.__context.get_line_width()

    @lineWidth.setter
    def lineWidth(self, value: float) -> None:
        self.__context.set_line_width(value)

    @property
    def miterLimit(self) -> float:
        return self.__context.get_miter_limit()

    @miterLimit.setter
    def miterLimit(self, value: float) -> None:
        self.__context.set_miter_limit(value)

    # -- imagery ---------------------------------------------------------------
    @property
    def imageSmoothingEnabled(self) -> bool:
        return self.__context.get_image_smoothing_enabled()

    @imageSmoothingEnabled.setter
    def imageSmoothingEnabled(self, value: bool) -> None:
        self.__context.set_image_smoothing_enabled(value)

    @property
    def imageSmoothingQuality(self) -> ImageSmoothingQuality:
        return self.__context.get_image_smoothing_quality()  # type: ignore

    @imageSmoothingQuality.setter
    def imageSmoothingQuality(self, value: str) -> None:
        self.__context.set_image_smoothing_quality(value)

    def createImageData(
        self, width: float, height: float, settings: ImageDataSettings | None = None
    ) -> ImageData:
        if not _is_finite_number(width) or not _is_finite_number(height):
            raise TypeError("Expected a finite number for width and height")
        return ImageData(width, height, settings)

    def getImageData(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        settings: ImageDataExportSettings | None = None,
    ) -> ImageData:
        settings = settings or {}
        color_type = settings.get("color_type", "rgba")
        color_space = settings.get("color_space", "srgb")
        density = settings.get("density", 1)
        matte = settings.get("matte")
        msaa = settings.get("msaa")

        if (
            not isinstance(density, (int, float))
            or isinstance(density, bool)
            or not float(density).is_integer()
            or density < 1
        ):
            raise TypeError("Expected a non-negative integer for `density`")
        density = int(density)

        if msaa is None or msaa is True:
            msaa = None
        elif not math.isfinite(float(msaa)) or float(msaa) < 0:
            raise TypeError("The number of MSAA samples must be an integer >=0")
        else:
            msaa = float(msaa)

        opts = {
            "color_type": color_type,
            "color_space": color_space,
            "density": int(density),
            "matte": matte,
            "msaa": msaa,
        }

        canvas = self.canvas
        if canvas is None:
            raise RuntimeError("Canvas context has been detached from canvas")

        if (
            not math.isfinite(x)
            or not math.isfinite(y)
            or not math.isfinite(width)
            or not math.isfinite(height)
        ):
            raise TypeError("Expected a finite number for x, y, width and height")
        buffer = self.__context.get_image_data(
            x, y, width, height, ImageDataExportOptions(**opts), canvas.core()
        )
        return ImageData(
            buffer,
            int(width) * density,
            int(height) * density,
            {
                "color_type": color_type,
                "color_space": color_space,
            },
        )

    @overload
    def putImageData(self, image_data: ImageData, x: float, y: float, /) -> None: ...
    @overload
    def putImageData(
        self,
        image_data: ImageData,
        x: float,
        y: float,
        dirty_x: float,
        dirty_y: float,
        dirty_width: float,
        dirty_height: float,
        /,
    ) -> None: ...

    def putImageData(
        self, image_data: ImageData, x: float, y: float, *args: float
    ) -> None:
        if not isinstance(image_data, ImageData):
            raise TypeError("Expected an ImageData as 1st arg")
        if not math.isfinite(x) or not math.isfinite(y):
            raise TypeError("Expected a finite number for x and y")
        for arg in args:
            if not math.isfinite(arg):
                raise TypeError("Expected a finite number for dirty rectangle")
        self.__context.put_image_data(image_data, x, y, args)

    @overload
    def drawImage(
        self, image: Image | Canvas | ImageData, dx: float, dy: float, /
    ) -> None: ...
    @overload
    def drawImage(
        self,
        image: Image | Canvas | ImageData,
        dx: float,
        dy: float,
        dw: float,
        dh: float,
        /,
    ) -> None: ...
    @overload
    def drawImage(
        self,
        image: Image | Canvas | ImageData,
        sx: float,
        sy: float,
        sw: float,
        sh: float,
        dx: float,
        dy: float,
        dw: float,
        dh: float,
        /,
    ) -> None: ...

    def drawImage(self, image: Image | Canvas | ImageData, *coords: float) -> None:
        if isinstance(image, Canvas):
            source = image.getContext("2d")
            if source is None:
                raise TypeError("Expected an Image or a Canvas argument")
            self.__context.draw_image(source.core(), coords)
        elif isinstance(image, Image):
            if image.complete:
                self.__context.draw_image(image.core(), coords)
            else:
                raise ValueError(
                    "Image has not completed loading: await loading before drawing"
                )
        elif isinstance(image, ImageData):
            self.__context.draw_image(image, coords)
        else:
            raise TypeError(
                f"Expected an Image or a Canvas argument (got: {type(image).__name__})"
            )

    @overload
    def drawCanvas(self, image: Canvas, dx: float, dy: float, /) -> None: ...
    @overload
    def drawCanvas(
        self,
        image: Canvas,
        dx: float,
        dy: float,
        dw: float,
        dh: float,
        /,
    ) -> None: ...
    @overload
    def drawCanvas(
        self,
        image: Canvas,
        sx: float,
        sy: float,
        sw: float,
        sh: float,
        dx: float,
        dy: float,
        dw: float,
        dh: float,
        /,
    ) -> None: ...

    def drawCanvas(self, image: Canvas, *coords: float) -> None:
        if isinstance(image, Canvas):
            # 如果是同一个对象，传入 None ，避免 rust 端借用冲突
            ctx_rs = None
            if self.canvas is not image:
                source = image.getContext("2d")
                if source is None:
                    raise TypeError("Expected an Image or a Canvas argument")
                ctx_rs = source.core()
            self.__context.draw_canvas(ctx_rs, coords)
        else:
            self.drawImage(image, *coords)

    # -- typography ------------------------------------------------------------
    @property
    def font(self) -> str:
        return self.__context.get_font()

    @font.setter
    def font(self, value: str) -> None:
        parsed = css.font(value)
        if parsed is not None:
            self.__context.set_font(parsed)

    @property
    def textAlign(self) -> CanvasTextAlign:
        return self.__context.get_text_align()  # type: ignore

    @textAlign.setter
    def textAlign(self, value: str) -> None:
        self.__context.set_text_align(value)

    @property
    def textBaseline(self) -> CanvasTextBaseline:
        return self.__context.get_text_baseline()  # type: ignore

    @textBaseline.setter
    def textBaseline(self, value: str) -> None:
        self.__context.set_text_baseline(value)

    @property
    def direction(self) -> CanvasDirection:
        return self.__context.get_direction()  # type: ignore

    @direction.setter
    def direction(self, value: str) -> None:
        self.__context.set_direction(value)

    @property
    def fontStretch(self) -> CanvasFontStretch:
        return self.__context.get_font_stretch()  # type: ignore

    @fontStretch.setter
    def fontStretch(self, value: str) -> None:
        parsed = css.stretch(value)
        if parsed is not None:
            self.__context.set_font_stretch(parsed)

    @property
    def letterSpacing(self) -> str:
        return self.__context.get_letter_spacing()

    @letterSpacing.setter
    def letterSpacing(self, value: str) -> None:
        parsed = css.spacing(value)
        if parsed is not None:
            self.__context.set_letter_spacing(parsed)

    @property
    def wordSpacing(self) -> str:
        return self.__context.get_word_spacing()

    @wordSpacing.setter
    def wordSpacing(self, value: str) -> None:
        parsed = css.spacing(value)
        if parsed is not None:
            self.__context.set_word_spacing(parsed)

    def measureText(self, text: str, max_width: float | None = None) -> TextMetrics:
        metrics = self.__context.measure_text(str(text), max_width)
        v = json.loads(metrics)
        return TextMetrics(**v)

    def fillText(
        self, text: str, x: float, y: float, max_width: float | None = None
    ) -> None:
        self.__context.fill_text(str(text), x, y, max_width)

    def strokeText(
        self, text: str, x: float, y: float, max_width: float | None = None
    ) -> None:
        self.__context.stroke_text(text, x, y, max_width)

    def outlineText(self, text: str, max_width: float | None = None) -> Path2D:
        path = self.__context.outline_text(text, max_width)
        return Path2D(path)

    # -- non-standard typography extensions -----------------------------------
    @property
    def fontHinting(self) -> bool:
        return self.__context.get_font_hinting()

    @fontHinting.setter
    def fontHinting(self, flag: bool) -> None:
        self.__context.set_font_hinting(flag)

    @property
    def fontVariant(self) -> FontVariantSetting:
        return self.__context.get_font_variant()  # type: ignore

    @fontVariant.setter
    def fontVariant(self, value: str) -> None:
        parsed = css.variant(value)
        if parsed is not None:
            self.__context.set_font_variant(parsed)

    @property
    def textWrap(self) -> bool:
        return self.__context.get_text_wrap()

    @textWrap.setter
    def textWrap(self, flag: bool) -> None:
        self.__context.set_text_wrap(flag)

    @property
    def textDecoration(self) -> str:
        return self.__context.get_text_decoration()

    @textDecoration.setter
    def textDecoration(self, value: str) -> None:
        parsed = css.decoration(value)
        if parsed is not None:
            self.__context.set_text_decoration(parsed)

    @property
    def textTracking(self) -> None:
        return None

    @textTracking.setter
    def textTracking(self, _value) -> None:
        warnings.warn(
            "The .textTracking property has been removed; use .letterSpacing instead",
            DeprecationWarning,
            stacklevel=2,
        )

    # -- effects ---------------------------------------------------------------
    @property
    def globalCompositeOperation(self) -> GlobalCompositeOperation:
        return self.__context.get_global_composite_operation()  # type: ignore

    @globalCompositeOperation.setter
    def globalCompositeOperation(self, blend: str) -> None:
        self.__context.set_global_composite_operation(blend)

    @property
    def globalAlpha(self) -> float:
        return self.__context.get_global_alpha()

    @globalAlpha.setter
    def globalAlpha(self, alpha: float) -> None:
        self.__context.set_global_alpha(alpha)

    @property
    def shadowBlur(self) -> float:
        return self.__context.get_shadow_blur()

    @shadowBlur.setter
    def shadowBlur(self, value: float) -> None:
        self.__context.set_shadow_blur(value)

    @property
    def shadowColor(self) -> str:
        return self.__context.get_shadow_color()

    @shadowColor.setter
    def shadowColor(self, value: str) -> None:
        self.__context.set_shadow_color(value)

    @property
    def shadowOffsetX(self) -> float:
        return self.__context.get_shadow_offset_x()

    @shadowOffsetX.setter
    def shadowOffsetX(self, value: float) -> None:
        self.__context.set_shadow_offset_x(value)

    @property
    def shadowOffsetY(self) -> float:
        return self.__context.get_shadow_offset_y()

    @shadowOffsetY.setter
    def shadowOffsetY(self, value: float) -> None:
        self.__context.set_shadow_offset_y(value)

    @property
    def filter(self) -> str:
        return self.__context.get_filter()

    @filter.setter
    def filter(self, value: str) -> None:
        parsed = css.filter(value)
        if parsed is not None:
            self.__context.set_filter(parsed)

    def core(self) -> Context2DRs:
        return self.__context

    def raw_reset_size(self) -> None:
        canvas = self.canvas
        if canvas is not None:
            self.__context.reset_size(canvas.core())

    def raw_size(self) -> Tuple[float, float]:
        return self.__context.get_size()

    def raw_set_size(self, width: float, height: float):
        self.__context.set_size(width, height)
