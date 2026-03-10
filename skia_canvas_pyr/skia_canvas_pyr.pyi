from __future__ import annotations

from typing import Literal, Sequence, TypeAlias, Tuple, List

PathOpName = Literal[
    "difference",
    "intersect",
    "union",
    "xor",
    "reversedifference",
    "complement",
]
FillRule = Literal["nonzero", "evenodd"]
EdgeCommand = Literal[
    "moveTo",
    "lineTo",
    "quadraticCurveTo",
    "bezierCurveTo",
    "conicCurveTo",
    "closePath",
]

# 实际上第一个是命令字符串，第二个及以后的都是 float 参数
Path2DEdge: TypeAlias = Tuple[EdgeCommand | float, ...]

class Path2D:
    def __init__(self) -> None: ...
    @staticmethod
    def from_path(other_path: Path2D) -> Path2D: ...
    @staticmethod
    def from_svg(d: str) -> Path2D: ...
    def add_path(
        self, other: Path2D, transform: Sequence[float] | None = None
    ) -> None: ...
    def close_path(self) -> None: ...
    def move_to(self, x: float, y: float) -> None: ...
    def line_to(self, x: float, y: float) -> None: ...
    def bezier_curve_to(
        self, cp1x: float, cp1y: float, cp2x: float, cp2y: float, x: float, y: float
    ) -> None: ...
    def quadratic_curve_to(
        self, cpx: float, cpy: float, x: float, y: float
    ) -> None: ...
    def conic_curve_to(
        self, cpx: float, cpy: float, x: float, y: float, weight: float
    ) -> None: ...
    def arc(
        self,
        x: float,
        y: float,
        radius: float,
        start_angle: float,
        end_angle: float,
        counterclockwise: bool | None = None,
    ) -> None: ...
    def arc_to(
        self, x1: float, y1: float, x2: float, y2: float, radius: float
    ) -> None: ...
    def ellipse(
        self,
        x: float,
        y: float,
        radius_x: float,
        radius_y: float,
        rotation: float,
        start_angle: float,
        end_angle: float,
        counterclockwise: bool | None = None,
    ) -> None: ...
    def rect(self, x: float, y: float, width: float, height: float) -> None: ...
    def round_rect(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        top_left_radius_x: float,
        top_left_radius_y: float,
        top_right_radius_x: float,
        top_right_radius_y: float,
        bottom_right_radius_x: float,
        bottom_right_radius_y: float,
        bottom_left_radius_x: float,
        bottom_left_radius_y: float,
    ) -> None: ...
    def op(self, other: Path2D, operation: PathOpName) -> Path2D: ...
    def interpolate(self, other: Path2D, weight: float) -> Path2D: ...
    def simplify(self, fill_rule: FillRule | None = None) -> Path2D: ...
    def unwind(self) -> Path2D: ...
    def offset(self, dx: float, dy: float) -> Path2D: ...
    def transform(self, matrix: Sequence[float]) -> Path2D: ...
    def round(self, radius: float) -> Path2D: ...
    def trim(
        self,
        begin: float,
        end: float,
        inverted: bool | None = None,
    ) -> Path2D: ...
    def jitter(
        self, segment_length: float, variance: float, seed: float | None = None
    ) -> Path2D: ...
    def bounds(self) -> Path2DBounds: ...
    def contains(self, x: float, y: float) -> bool: ...
    def edges(self) -> List[Path2DEdge]: ...
    def get_d(self) -> str: ...
    def set_d(self, p: str) -> None: ...

class Path2DBounds:
    top: float
    left: float
    bottom: float
    right: float
    width: float
    height: float
