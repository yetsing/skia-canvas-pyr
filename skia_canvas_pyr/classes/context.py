import weakref

from typing import TYPE_CHECKING

from . import css
from .canvas import Canvas, CanvasGradient, CanvasPattern, CanvasTexture
from .imagery import Image, ImageData
from .geometry import fromSkMatrix, toSkMatrix, DOMMatrix
from .path import Path2D
from ..skia_canvas_pyr import Context2D as Context2DRs

if TYPE_CHECKING:
    from typing import overload, Sequence, Literal, List
    from .sc_type import (
        QuadOrRect,
        CanvasFillRule,
        Offset,
        CanvasLineCap,
        CanvasLineDashFit,
        CanvasLineJoin,
        ImageSmoothingQuality,
        ImageDataSettings,
        ImageDataExportSettings,
    )
    from .geometry import Matrix, DOMPointInit


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

    def createProjection(self, quad: QuadOrRect, basis: QuadOrRect) -> DOMMatrix:
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
    def fill(
        self, path: Path2D | None = None, rule: CanvasFillRule | None = None
    ) -> None:
        self.__context.fill(path and path.core(), rule)

    def stroke(self, path: Path2D | None = None) -> None:
        self.__context.stroke(path and path.core())

    def clip(
        self, path: Path2D | None = None, rule: CanvasFillRule | None = None
    ) -> None:
        self.__context.clip(path and path.core(), rule)

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
        path: Path2D | None = None,
        line: float | None = None,
        cap: CanvasLineCap = "butt",
        color: str | None = None,
        angle: float | None = None,
        offset: Offset = 0,
        outline: bool = False,
    ) -> CanvasTexture:
        return CanvasTexture(spacing, path, line, cap, color, angle, offset, outline)

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
        else:
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
        else:
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
        return ImageData(int(width), int(height), settings)

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

    def core(self) -> Context2DRs:
        return self.__context
