from __future__ import annotations

from typing import TYPE_CHECKING

from . import css
from .geometry import toSkMatrix
from ..skia_canvas_pyr import Path2D as Path2DRs

if TYPE_CHECKING:
    from typing import overload, Literal, List, Sequence, Tuple
    from .geometry import DOMMatrix2DInit, DOMPointInit, Matrix
    from ..skia_canvas_pyr import Path2DBounds, Path2DEdge


class Path2D:
    """ref: https://skia-canvas.org/api/path2d"""

    __slots__ = ("__path",)

    def __init__(self, source: Path2D | str | Path2DRs | None = None):
        if isinstance(source, Path2D):
            self.__path = Path2DRs.from_path(source.__path)
        elif isinstance(source, str):
            self.__path = Path2DRs.from_svg(source)
        elif isinstance(source, Path2DRs):
            self.__path = source
        else:
            self.__path = Path2DRs()

    @property
    def bounds(self) -> Path2DBounds:
        return self.__path.bounds()

    @property
    def edges(self) -> List[Path2DEdge]:
        return self.__path.edges()

    @property
    def d(self) -> str:
        return self.__path.get_d()

    @d.setter
    def d(self, value: str):
        self.__path.set_d(value)

    def contains(self, x: float, y: float) -> bool:
        return self.__path.contains(x, y)

    def points(self, step: float = 1) -> List[Tuple[float, float]]:
        edges = self.jitter(step, 0).edges
        it = map(lambda edge: tuple(edge[1:][-2:]), edges)
        return list(filter(lambda x: x, it))  # type: ignore

    def addPath(self, path: Path2D, matrix: DOMMatrix2DInit | None = None):
        sk_matrix = None
        if matrix is not None:
            sk_matrix = toSkMatrix(matrix)
        self.__path.add_path(path.__path, sk_matrix)

    def moveTo(self, x: float, y: float):
        self.__path.move_to(x, y)

    def lineTo(self, x: float, y: float):
        self.__path.line_to(x, y)

    def closePath(self):
        self.__path.close_path()

    def arcTo(self, x1: float, y1: float, x2: float, y2: float, radius: float):
        self.__path.arc_to(x1, y1, x2, y2, radius)

    def bezierCurveTo(
        self, cp1x: float, cp1y: float, cp2x: float, cp2y: float, x: float, y: float
    ):
        self.__path.bezier_curve_to(cp1x, cp1y, cp2x, cp2y, x, y)

    def quadraticCurveTo(self, cpx: float, cpy: float, x: float, y: float):
        self.__path.quadratic_curve_to(cpx, cpy, x, y)

    def conicCurveTo(self, cpx: float, cpy: float, x: float, y: float, weight: float):
        self.__path.conic_curve_to(cpx, cpy, x, y, weight)

    def ellipse(
        self,
        x: float,
        y: float,
        radiusX: float,
        radiusY: float,
        rotation: float,
        startAngle: float,
        endAngle: float,
        counterclockwise: bool = False,
    ):
        self.__path.ellipse(
            x, y, radiusX, radiusY, rotation, startAngle, endAngle, counterclockwise
        )

    def rect(self, x: float, y: float, width: float, height: float):
        self.__path.rect(x, y, width, height)

    def arc(
        self,
        x: float,
        y: float,
        radius: float,
        startAngle: float,
        endAngle: float,
        counterclockwise: bool = False,
    ):
        self.__path.arc(x, y, radius, startAngle, endAngle, counterclockwise)

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
            self.__path.round_rect(x, y, width, height, *radii_args)

    def interpolate(self, other: Path2D, weight: float) -> Path2D:
        path = self.__path.interpolate(other.__path, weight)
        return Path2D(path)

    def complement(self, other: Path2D) -> Path2D:
        path = self.__path.op(other.__path, "complement")
        return Path2D(path)

    def difference(self, other: Path2D) -> Path2D:
        path = self.__path.op(other.__path, "difference")
        return Path2D(path)

    def intersect(self, other: Path2D) -> Path2D:
        path = self.__path.op(other.__path, "intersect")
        return Path2D(path)

    def union(self, other: Path2D) -> Path2D:
        path = self.__path.op(other.__path, "union")
        return Path2D(path)

    def xor(self, other: Path2D) -> Path2D:
        path = self.__path.op(other.__path, "xor")
        return Path2D(path)

    def jitter(self, segmentLength: float, amount: float, seed: float = 0) -> Path2D:
        path = self.__path.jitter(segmentLength, amount, seed)
        return Path2D(path)

    def simplify(self, rule: Literal["nonzero", "evenodd"] = "nonzero") -> Path2D:
        path = self.__path.simplify(rule)
        return Path2D(path)

    def unwind(self) -> Path2D:
        path = self.__path.unwind()
        return Path2D(path)

    def round(self, radius: float) -> Path2D:
        path = self.__path.round(radius)
        return Path2D(path)

    def offset(self, dx: float, dy: float) -> Path2D:
        path = self.__path.offset(dx, dy)
        return Path2D(path)

    @overload
    def transform(self, transform: Matrix, /) -> Path2D: ...
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
    ) -> Path2D: ...

    def transform(self, *args) -> Path2D:
        matrix = toSkMatrix(*args)
        path = self.__path.transform(matrix)
        return Path2D(path)

    def trim(
        self, start: float, end: float | None = None, inverted: bool = False
    ) -> Path2D:
        if end is None:
            if start > 0:
                end = start
                start = 0
            elif start < 0:
                end = 1
            else:
                end = 0
        if start < 0:
            start = max(-1, start) + 1
        if end < 0:
            end = max(-1, end) + 1
        path = self.__path.trim(start, end, inverted)
        return Path2D(path)

    def __repr__(self) -> str:
        return f"Path2D(d={self.d!r}, bounds={self.bounds!r}, edges={self.edges!r})"

    def __str__(self) -> str:
        return f"Path2D(d={self.d}, bounds={self.bounds}, edges={self.edges})"

    def core(self) -> Path2DRs:
        return self.__path
