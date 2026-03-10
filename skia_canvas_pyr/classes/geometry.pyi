from __future__ import annotations

from typing import (
    Any,
    Awaitable,
    Callable,
    Dict,
    Iterable,
    Literal,
    Protocol,
    Sequence,
    TypedDict,
    TypeAlias,
    overload,
    Protocol,
    Optional,
    List,
    Tuple,
    Union,
)

#
# Geometry
#

class DOMPointInit(Protocol):
    x: float
    y: float
    z: float
    w: float

class DOMPoint(DOMPointReadOnly):
    """[MDN Reference](https://developer.mozilla.org/docs/Web/API/DOMPoint)"""

    # [MDN Reference](https://developer.mozilla.org/docs/Web/API/DOMPoint/x)
    x: float
    # [MDN Reference](https://developer.mozilla.org/docs/Web/API/DOMPoint/y)
    y: float
    # [MDN Reference](https://developer.mozilla.org/docs/Web/API/DOMPoint/z)
    z: float
    # [MDN Reference](https://developer.mozilla.org/docs/Web/API/DOMPoint/w)
    w: float

    def __init__(
        self, x: float = 0, y: float = 0, z: float = 0, w: float = 1
    ) -> None: ...
    @classmethod
    def fromPoint(cls, other: DOMPointInit) -> DOMPoint:
        """[MDN Reference](https://developer.mozilla.org/docs/Web/API/DOMPoint/fromPoint_static)"""

class DOMPointReadOnly:
    """[MDN Reference](https://developer.mozilla.org/docs/Web/API/DOMPointReadOnly)"""

    # [MDN Reference](https://developer.mozilla.org/docs/Web/API/DOMPointReadOnly/x)
    x: float
    # [MDN Reference](https://developer.mozilla.org/docs/Web/API/DOMPointReadOnly/y)
    y: float
    # [MDN Reference](https://developer.mozilla.org/docs/Web/API/DOMPointReadOnly/z)
    z: float
    # [MDN Reference](https://developer.mozilla.org/docs/Web/API/DOMPointReadOnly/w)
    w: float

    def __init__(
        self, x: float = 0, y: float = 0, z: float = 0, w: float = 1
    ) -> None: ...
    @classmethod
    def fromPoint(cls, other: DOMPointInit) -> DOMPointReadOnly:
        """[MDN Reference](https://developer.mozilla.org/docs/Web/API/DOMPointReadOnly/fromPoint_static)"""

    def matrixTransform(self, matrix: DOMMatrixInit) -> DOMPointReadOnly: ...
    def toJSON(self) -> Dict[str, float]:
        """[MDN Reference](https://developer.mozilla.org/docs/Web/API/DOMPointReadOnly/toJSON)"""

class DOMRectInit(Protocol):
    x: float
    y: float
    width: float
    height: float

class DOMRect(DOMRectReadOnly):
    """MDN Reference: https://developer.mozilla.org/docs/Web/API/DOMRect"""

    x: float
    y: float
    width: float
    height: float

    def __init__(
        self, x: float = 0, y: float = 0, width: float = 0, height: float = 0
    ) -> None: ...
    @classmethod
    def fromRect(cls, other: DOMRectInit | None = None) -> DOMRect:
        """[MDN Reference](https://developer.mozilla.org/docs/Web/API/DOMRect/fromRect_static)"""

class DOMRectList(Sequence[DOMRect]):
    @property
    def length(self) -> int: ...
    def item(self, index: int) -> DOMRect | None: ...

class DOMRectReadOnly:
    """[MDN Reference](https://developer.mozilla.org/docs/Web/API/DOMRectReadOnly)"""

    # [MDN Reference](https://developer.mozilla.org/docs/Web/API/DOMRectReadOnly/bottom)
    bottom: float
    # [MDN Reference](https://developer.mozilla.org/docs/Web/API/DOMRectReadOnly/height)
    height: float
    # [MDN Reference](https://developer.mozilla.org/docs/Web/API/DOMRectReadOnly/left)
    left: float
    # [MDN Reference](https://developer.mozilla.org/docs/Web/API/DOMRectReadOnly/right)
    right: float
    # [MDN Reference](https://developer.mozilla.org/docs/Web/API/DOMRectReadOnly/top)
    top: float
    # [MDN Reference](https://developer.mozilla.org/docs/Web/API/DOMRectReadOnly/width)
    width: float
    # [MDN Reference](https://developer.mozilla.org/docs/Web/API/DOMRectReadOnly/x)
    x: float
    # [MDN Reference](https://developer.mozilla.org/docs/Web/API/DOMRectReadOnly/y)
    y: float

    def __init__(
        self, x: float = 0, y: float = 0, width: float = 0, height: float = 0
    ) -> None: ...
    @classmethod
    def fromRect(cls, other: DOMRectInit | None = None) -> DOMRectReadOnly:
        """[MDN Reference](https://developer.mozilla.org/docs/Web/API/DOMRectReadOnly/fromRect_static)"""

    def toJSON(self) -> Any: ...

class DOMMatrix2DInit(Protocol):
    a: float
    b: float
    c: float
    d: float
    e: float
    f: float
    m11: float
    m12: float
    m21: float
    m22: float
    m41: float
    m42: float

class DOMMatrixInit(DOMMatrix2DInit):
    is2D: bool
    m13: float
    m14: float
    m23: float
    m24: float
    m31: float
    m32: float
    m33: float
    m34: float
    m43: float
    m44: float

class DOMMatrix:
    a: float
    b: float
    c: float
    d: float
    e: float
    f: float
    m11: float
    m12: float
    m13: float
    m14: float
    m21: float
    m22: float
    m23: float
    m24: float
    m31: float
    m32: float
    m33: float
    m34: float
    m41: float
    m42: float
    m43: float
    m44: float

    def __init__(self, init: Matrix | None = None) -> None: ...
    @classmethod
    def fromFloat32Array(cls, array32: Sequence[float]) -> DOMMatrix: ...
    @classmethod
    def fromFloat64Array(cls, array64: Sequence[float]) -> DOMMatrix: ...
    @classmethod
    def fromMatrix(cls, other: DOMMatrixInit | None = None) -> DOMMatrix: ...
    def flipX(self) -> DOMMatrix: ...
    def flipY(self) -> DOMMatrix: ...
    def inverse(self) -> DOMMatrix: ...
    def invertSelf(self) -> DOMMatrix: ...
    def multiply(self, other: DOMMatrixInit | None = None) -> DOMMatrix: ...
    def multiplySelf(self, other: DOMMatrixInit | None = None) -> DOMMatrix: ...
    def preMultiplySelf(self, other: DOMMatrixInit | None = None) -> DOMMatrix: ...
    def rotate(
        self, rotX: float = 0, rotY: float = 0, rotZ: float = 0
    ) -> DOMMatrix: ...
    def rotateSelf(
        self, rotX: float = 0, rotY: float = 0, rotZ: float = 0
    ) -> DOMMatrix: ...
    def rotateAxisAngle(
        self, x: float = 0, y: float = 0, z: float = 0, angle: float = 0
    ) -> DOMMatrix: ...
    def rotateAxisAngleSelf(
        self, x: float = 0, y: float = 0, z: float = 0, angle: float = 0
    ) -> DOMMatrix: ...
    def rotateFromVector(self, x: float = 0, y: float = 0) -> DOMMatrix: ...
    def rotateFromVectorSelf(self, x: float = 0, y: float = 0) -> DOMMatrix: ...
    def scale(
        self,
        scaleX: float = 0,
        scaleY: float = 0,
        scaleZ: float = 0,
        originX: float = 0,
        originY: float = 0,
        originZ: float = 0,
    ) -> DOMMatrix: ...
    def scaleSelf(
        self,
        scaleX: float = 0,
        scaleY: float = 0,
        scaleZ: float = 0,
        originX: float = 0,
        originY: float = 0,
        originZ: float = 0,
    ) -> DOMMatrix: ...
    def scale3d(
        self,
        scale: float = 0,
        originX: float = 0,
        originY: float = 0,
        originZ: float = 0,
    ) -> DOMMatrix: ...
    def scale3dSelf(
        self,
        scale: float = 0,
        originX: float = 0,
        originY: float = 0,
        originZ: float = 0,
    ) -> DOMMatrix: ...
    def skew(self, sx: float = 0, sy: float = 0) -> DOMMatrix: ...
    def skewSelf(self, sx: float = 0, sy: float = 0) -> DOMMatrix: ...
    def skewX(self, sx: float = 0) -> DOMMatrix: ...
    def skewXSelf(self, sx: float = 0) -> DOMMatrix: ...
    def skewY(self, sy: float = 0) -> DOMMatrix: ...
    def skewYSelf(self, sy: float = 0) -> DOMMatrix: ...
    def translate(self, tx: float = 0, ty: float = 0, tz: float = 0) -> DOMMatrix: ...
    def translateSelf(
        self, tx: float = 0, ty: float = 0, tz: float = 0
    ) -> DOMMatrix: ...
    def setMatrixValue(self, transformList: str) -> DOMMatrix: ...
    def transformPoint(self, point: DOMPointInit | None = None) -> DOMPoint: ...
    def toFloat32Array(self) -> list[float]: ...
    def toFloat64Array(self) -> list[float]: ...
    def toJSON(self) -> Any: ...
    def toString(self) -> str: ...
    def clone(self) -> DOMMatrix: ...

class Abcdef(Protocol):
    a: float
    b: float
    c: float
    d: float
    e: float
    f: float

Matrix: TypeAlias = str | DOMMatrix | Abcdef | Sequence[float]

def toSkMatrix(*args) -> List[float]: ...
def fromSkMatrix(matrix: Sequence[float]) -> DOMMatrix: ...
