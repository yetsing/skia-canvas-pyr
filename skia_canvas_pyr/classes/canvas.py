from __future__ import annotations

import math

from typing import TYPE_CHECKING

from ..skia_canvas_pyr import (
    CanvasTexture as CanvasTextureRs,
    CanvasGradient as CanvasGradientRs,
    CanvasPattern as CanvasPatternRs,
)
from .imagery import Image, ImageData
from .geometry import toSkMatrix

if TYPE_CHECKING:
    from typing import Any, TypeAlias, Literal, List, Tuple, overload
    from .geometry import Matrix
    from .path import Path2D

    Offset: TypeAlias = List[float] | Tuple[float, float] | float
    CanvasLineCap: TypeAlias = Literal["butt", "round", "square"]


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
        else:
            x = y = offset
        if isinstance(spacing, list):
            h, v = (spacing + spacing)[:2]
        elif isinstance(spacing, tuple):
            h, v = (spacing + spacing)[:2]
        else:
            h = v = spacing

        if path is not None and not isinstance(path, Path2D):
            raise TypeError("path must be a Path2D instance or None")

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

    def __init__(self, style: Literal["linear", "radial", "conic"], *args: float):
        match style:
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
        canvas: Any,
        src: Image | ImageData,
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
        # TODO: from canvas
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
