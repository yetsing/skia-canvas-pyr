import math

from typing import TYPE_CHECKING

from ..skia_canvas_pyr import (
    CanvasTexture as CanvasTextureRs,
    CanvasGradient as CanvasGradientRs,
)

if TYPE_CHECKING:
    from typing import TypeAlias, Literal, List, Tuple
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
