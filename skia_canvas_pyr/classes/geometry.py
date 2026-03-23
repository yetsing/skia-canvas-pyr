"""
Polyfill for DOMMatrix and friends
"""

import math
import re
from numbers import Number
from typing import (
    Any,
    Mapping,
    Sequence,
    TypeGuard,
    Union,
    Protocol,
    TypedDict,
    TypeAlias,
)

# region Type definitions


class DOMPointInit1(Protocol):
    x: float
    y: float
    z: float
    w: float


class DOMPointInit2(TypedDict):
    x: float
    y: float
    z: float
    w: float


DOMPointInit: TypeAlias = Union[DOMPointInit1, DOMPointInit2]


class DOMRectInit1(Protocol):
    x: float
    y: float
    width: float
    height: float


class DOMRectInit2(TypedDict):
    x: float
    y: float
    width: float
    height: float


DOMRectInit: TypeAlias = DOMRectInit1 | DOMRectInit2


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


class Abcdef(Protocol):
    a: float
    b: float
    c: float
    d: float
    e: float
    f: float


# endregion


# vendored in order to fix its dependence on the window global [@samizdatco 2020/08/04]
# removed SVGMatrix references that were guaranteed to be undefined on node [@mpaperno 2024/10/20]
# added support for parsing existing matrices (and matrix-like) objects in constructor [@mpaperno 2024/10/20]
# added `parseTransform*` helpers to enable CSS-style strings as constructor args [@samizdatco 2024/10/29]
# otherwise unchanged from https://github.com/jarek-foksa/geometry-polyfill/tree/f36bbc8f4bc43539d980687904ce46c8e915543d


# @info
#   DOMPoint polyfill
# @src
#   https://drafts.fxtf.org/geometry/#DOMPoint
#   https://github.com/chromium/chromium/blob/master/third_party/blink/renderer/core/geometry/dom_point_read_only.cc
class DOMPoint:
    __slots__ = ("x", "y", "z", "w")

    def __init__(
        self,
        x: Union[int, float] = 0,
        y: Union[int, float] = 0,
        z: Union[int, float] = 0,
        w: Union[int, float] = 1,
    ):
        self.x = x
        self.y = y
        self.z = z
        self.w = w

    @classmethod
    def fromPoint(cls, other):
        return DOMPoint(
            _get_prop(other, "x"),
            _get_prop(other, "y"),
            _get_prop(other, "z"),
            _get_prop(other, "w"),
        )

    def matrixTransform(self, matrix):
        if matrix.is2D and self.z == 0 and self.w == 1:
            return DOMPoint(
                self.x * matrix.a + self.y * matrix.c + matrix.e,
                self.x * matrix.b + self.y * matrix.d + matrix.f,
                0,
                1,
            )
        else:
            return DOMPoint(
                self.x * matrix.m11
                + self.y * matrix.m21
                + self.z * matrix.m31
                + self.w * matrix.m41,
                self.x * matrix.m12
                + self.y * matrix.m22
                + self.z * matrix.m32
                + self.w * matrix.m42,
                self.x * matrix.m13
                + self.y * matrix.m23
                + self.z * matrix.m33
                + self.w * matrix.m43,
                self.x * matrix.m14
                + self.y * matrix.m24
                + self.z * matrix.m34
                + self.w * matrix.m44,
            )

    def toJSON(self):
        return {
            "x": self.x,
            "y": self.y,
            "z": self.z,
            "w": self.w,
        }


# @info
#   DOMRect polyfill
# @src
#   https://drafts.fxtf.org/geometry/#DOMRect
#   https://github.com/chromium/chromium/blob/master/third_party/blink/renderer/core/geometry/dom_rect_read_only.cc


class DOMRect:
    __slots__ = ("x", "y", "width", "height")

    def __init__(
        self,
        x: Union[int, float] = 0,
        y: Union[int, float] = 0,
        width: Union[int, float] = 0,
        height: Union[int, float] = 0,
    ):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    @classmethod
    def fromRect(cls, other):
        return DOMRect(
            _get_prop(other, "x"),
            _get_prop(other, "y"),
            _get_prop(other, "width"),
            _get_prop(other, "height"),
        )

    @property
    def top(self):
        return self.y

    @property
    def left(self):
        return self.x

    @property
    def right(self):
        return self.x + self.width

    @property
    def bottom(self):
        return self.y + self.height

    def toJSON(self):
        return {
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "top": self.top,
            "left": self.left,
            "right": self.right,
            "bottom": self.bottom,
        }


# @info
#   DOMMatrix polyfill (SVG 2)
# @src
#   https://github.com/chromium/chromium/blob/master/third_party/blink/renderer/core/geometry/dom_matrix_read_only.cc
#   https://github.com/tocharomera/generativecanvas/blob/master/node-canvas/lib/DOMMatrix.js

M11 = 0
M12 = 1
M13 = 2
M14 = 3
M21 = 4
M22 = 5
M23 = 6
M24 = 7
M31 = 8
M32 = 9
M33 = 10
M34 = 11
M41 = 12
M42 = 13
M43 = 14
M44 = 15

A = M11
B = M12
C = M21
D = M22
E = M41
F = M42

DEGREE_PER_RAD = 180 / math.pi
RAD_PER_DEGREE = math.pi / 180

# Parsers for CSS-style string initializers
_transform_name_re = re.compile(
    r"^(matrix(3d)?|(rotate|translate|scale)(3d|X|Y|Z)?|skew(X|Y)?)$"
)


def _is_plain_object(o):
    return isinstance(o, Mapping)


def _get_prop(obj, key):
    if isinstance(obj, Mapping):
        return obj[key]
    return getattr(obj, key)


def _get_prop_default(obj, key, default=None):
    if isinstance(obj, Mapping):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _is_numeric(value: Any) -> TypeGuard[float | int]:
    return isinstance(value, Number) and not isinstance(value, bool) and not math.isnan(value)  # type: ignore


def _parse_angle(value):
    if isinstance(value, str):
        if value.endswith("deg"):
            return float(value[:-3])
        if value.endswith("rad"):
            return float(value[:-3]) / math.pi * 180
        if value.endswith("turn"):
            return float(value[:-4]) * 360
    raise TypeError(
        f"Angles must be in 'deg', 'rad', or 'turn' units (got: \"{value}\")"
    )


def _parse_length(value):
    if isinstance(value, str):
        if value.endswith("px"):
            return float(value[:-2])
        try:
            return float(value)
        except ValueError:
            pass
    elif _is_numeric(value):
        return float(value)
    raise TypeError(f"Lengths must be in 'px' or numeric units (got: \"{value}\")")


def _parse_scalar(value):
    if isinstance(value, str):
        if value.endswith("%"):
            return float(value[:-1]) / 100
        try:
            return float(value)
        except ValueError:
            pass
    elif _is_numeric(value):
        return float(value)
    raise TypeError(f"Scales must be in '%' or numeric units (got: \"{value}\")")


def _parse_numeric(value):
    if _is_numeric(value):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            pass
    raise TypeError(f'Matrix values must be in plain, numeric units (got: "{value}")')


def _parse_transform_string(transform_string):
    out = []
    chunks = [s for s in re.split(r"\)\s*", transform_string) if s.strip()]
    for transform in chunks:
        parts = [s.strip() for s in transform.split("(", 1)]

        # catch single-word initializers
        if len(parts) == 1:
            name = parts[0]
            if re.match(r"^(inherit|initial|revert(-layer)?|unset|none)$", name):
                out.append({"op": "matrix", "vals": [1, 0, 0, 1, 0, 0]})
                continue
            raise SyntaxError("The string did not match the expected pattern")

        name, transform_value = parts
        # otherwise check that the last term was well formed before splitting based on `)`
        if not transform_string.strip().endswith(")"):
            raise SyntaxError("Expected a closing ')'")

        # validate & normalize op names
        if not _transform_name_re.match(name):
            raise SyntaxError(f"Unknown transform operation: {name}")
        elif name == "rotate3d":
            name = "rotateAxisAngle"

        # validate the individual values & units
        raw_vals = [s.strip() for s in transform_value.split(",")]
        if name.startswith("rotate"):
            values = [_parse_length(v) for v in raw_vals[:-1]] + [
                _parse_angle(raw_vals[-1])
            ]
        elif name.startswith("skew"):
            values = [_parse_angle(v) for v in raw_vals]
        elif name.startswith("scale"):
            values = [_parse_scalar(v) for v in raw_vals]
        elif name.startswith("matrix"):
            values = [_parse_numeric(v) for v in raw_vals]
        else:
            values = [_parse_length(v) for v in raw_vals]

        # special case validation for the matrix/3d ops
        for form, length in (("matrix", 6), ("matrix3d", 16)):
            if name == form and len(values) != length:
                raise TypeError(
                    f"{name}() requires 6 numeric values (got {len(values)})"
                )

        # catch single-dimension ops and route them to the corresponding 3D matrix method
        m = re.match(r"^(rotate|translate|scale)(3d|X|Y|Z)$", name)
        if m:
            op, dim = m.group(1), m.group(2)
            fill = 1 if op == "scale" else 0
            if dim == "X":
                vals = [values[0], fill, fill]
            elif dim == "Y":
                vals = [fill, values[0], fill]
            elif dim == "Z":
                vals = [fill, fill, values[0]]
            else:
                vals = values
            out.append({"op": op, "vals": vals})
        else:
            out.append({"op": name, "vals": values})
    return out


def _set_number_2d(receiver, index, value):
    if not isinstance(value, (int, float)):
        raise TypeError("Expected number")
    receiver._values[index] = float(value)


def _set_number_3d(receiver, index, value):
    if not isinstance(value, (int, float)):
        raise TypeError("Expected number")

    fval = float(value)
    if index in (M33, M44):
        if fval != 1:
            receiver._is2d = False
    elif fval != 0:
        receiver._is2d = False

    receiver._values[index] = fval


def _multiply(first, second):
    dest = [0.0] * 16
    for i in range(4):
        for j in range(4):
            acc = 0.0
            for k in range(4):
                acc += first[i * 4 + k] * second[k * 4 + j]
            dest[i * 4 + j] = acc
    return dest


def _coerce_matrix(other):
    if isinstance(other, DOMMatrix):
        return other
    if other is None:
        return DOMMatrix()
    return DOMMatrix(other)


class DOMMatrix:
    # @type
    # (Float64Array) => void
    def __init__(self, init=None, *rest):
        if rest:
            init = [init, *rest]

        self._is2d = True
        # fmt: off
        self._values = [
            1, 0, 0, 0,
            0, 1, 0, 0,
            0, 0, 1, 0,
            0, 0, 0, 1,
        ]
        # fmt: on

        if isinstance(init, DOMMatrix) or _is_plain_object(init):
            other = DOMMatrix.fromMatrix(init)
            self._is2d = other._is2d
            self._values = other._values[:]
            return

        # Parse CSS transformList and accumulate transforms sequentially
        if isinstance(init, str):
            if init == "":
                return

            acc = DOMMatrix()
            for item in _parse_transform_string(init):
                op = item["op"]
                vals = item["vals"]
                if op.startswith("matrix"):
                    acc = acc.multiply(DOMMatrix(vals))
                elif hasattr(acc, op):
                    acc = getattr(acc, op)(*vals)

            init = acc._values

        if init is not None:
            seq = list(init)
            i = 0
            if len(seq) == 6:
                _set_number_2d(self, A, seq[i])
                i += 1
                _set_number_2d(self, B, seq[i])
                i += 1
                _set_number_2d(self, C, seq[i])
                i += 1
                _set_number_2d(self, D, seq[i])
                i += 1
                _set_number_2d(self, E, seq[i])
                i += 1
                _set_number_2d(self, F, seq[i])
            elif len(seq) == 16:
                _set_number_2d(self, M11, seq[i])
                i += 1
                _set_number_2d(self, M12, seq[i])
                i += 1
                _set_number_3d(self, M13, seq[i])
                i += 1
                _set_number_3d(self, M14, seq[i])
                i += 1
                _set_number_2d(self, M21, seq[i])
                i += 1
                _set_number_2d(self, M22, seq[i])
                i += 1
                _set_number_3d(self, M23, seq[i])
                i += 1
                _set_number_3d(self, M24, seq[i])
                i += 1
                _set_number_3d(self, M31, seq[i])
                i += 1
                _set_number_3d(self, M32, seq[i])
                i += 1
                _set_number_3d(self, M33, seq[i])
                i += 1
                _set_number_3d(self, M34, seq[i])
                i += 1
                _set_number_2d(self, M41, seq[i])
                i += 1
                _set_number_2d(self, M42, seq[i])
                i += 1
                _set_number_3d(self, M43, seq[i])
                i += 1
                _set_number_3d(self, M44, seq[i])
            else:
                raise TypeError(
                    "Expected string, array(length 6 or 16), or matrix object."
                )

    @property
    def m11(self):
        return self._values[M11]

    @m11.setter
    def m11(self, value):
        _set_number_2d(self, M11, value)

    @property
    def m12(self):
        return self._values[M12]

    @m12.setter
    def m12(self, value):
        _set_number_2d(self, M12, value)

    @property
    def m13(self):
        return self._values[M13]

    @m13.setter
    def m13(self, value):
        _set_number_3d(self, M13, value)

    @property
    def m14(self):
        return self._values[M14]

    @m14.setter
    def m14(self, value):
        _set_number_3d(self, M14, value)

    @property
    def m21(self):
        return self._values[M21]

    @m21.setter
    def m21(self, value):
        _set_number_2d(self, M21, value)

    @property
    def m22(self):
        return self._values[M22]

    @m22.setter
    def m22(self, value):
        _set_number_2d(self, M22, value)

    @property
    def m23(self):
        return self._values[M23]

    @m23.setter
    def m23(self, value):
        _set_number_3d(self, M23, value)

    @property
    def m24(self):
        return self._values[M24]

    @m24.setter
    def m24(self, value):
        _set_number_3d(self, M24, value)

    @property
    def m31(self):
        return self._values[M31]

    @m31.setter
    def m31(self, value):
        _set_number_3d(self, M31, value)

    @property
    def m32(self):
        return self._values[M32]

    @m32.setter
    def m32(self, value):
        _set_number_3d(self, M32, value)

    @property
    def m33(self):
        return self._values[M33]

    @m33.setter
    def m33(self, value):
        _set_number_3d(self, M33, value)

    @property
    def m34(self):
        return self._values[M34]

    @m34.setter
    def m34(self, value):
        _set_number_3d(self, M34, value)

    @property
    def m41(self):
        return self._values[M41]

    @m41.setter
    def m41(self, value):
        _set_number_2d(self, M41, value)

    @property
    def m42(self):
        return self._values[M42]

    @m42.setter
    def m42(self, value):
        _set_number_2d(self, M42, value)

    @property
    def m43(self):
        return self._values[M43]

    @m43.setter
    def m43(self, value):
        _set_number_3d(self, M43, value)

    @property
    def m44(self):
        return self._values[M44]

    @m44.setter
    def m44(self, value):
        _set_number_3d(self, M44, value)

    @property
    def a(self):
        return self._values[A]

    @a.setter
    def a(self, value):
        _set_number_2d(self, A, value)

    @property
    def b(self):
        return self._values[B]

    @b.setter
    def b(self, value):
        _set_number_2d(self, B, value)

    @property
    def c(self):
        return self._values[C]

    @c.setter
    def c(self, value):
        _set_number_2d(self, C, value)

    @property
    def d(self):
        return self._values[D]

    @d.setter
    def d(self, value):
        _set_number_2d(self, D, value)

    @property
    def e(self):
        return self._values[E]

    @e.setter
    def e(self, value):
        _set_number_2d(self, E, value)

    @property
    def f(self):
        return self._values[F]

    @f.setter
    def f(self, value):
        _set_number_2d(self, F, value)

    @property
    def is2D(self):
        return self._is2d

    @property
    def isIdentity(self):
        v = self._values
        return (
            v[M11] == 1
            and v[M12] == 0
            and v[M13] == 0
            and v[M14] == 0
            and v[M21] == 0
            and v[M22] == 1
            and v[M23] == 0
            and v[M24] == 0
            and v[M31] == 0
            and v[M32] == 0
            and v[M33] == 1
            and v[M34] == 0
            and v[M41] == 0
            and v[M42] == 0
            and v[M43] == 0
            and v[M44] == 1
        )

    @classmethod
    def fromMatrix(cls, init=None):
        if isinstance(init, DOMMatrix):
            return DOMMatrix(init._values)
        if cls.isMatrix4(init):
            return DOMMatrix(
                [
                    _get_prop(init, "m11"),
                    _get_prop(init, "m12"),
                    _get_prop(init, "m13"),
                    _get_prop(init, "m14"),
                    _get_prop(init, "m21"),
                    _get_prop(init, "m22"),
                    _get_prop(init, "m23"),
                    _get_prop(init, "m24"),
                    _get_prop(init, "m31"),
                    _get_prop(init, "m32"),
                    _get_prop(init, "m33"),
                    _get_prop(init, "m34"),
                    _get_prop(init, "m41"),
                    _get_prop(init, "m42"),
                    _get_prop(init, "m43"),
                    _get_prop(init, "m44"),
                ]
            )
        if cls.isMatrix3(init) or _is_plain_object(init):
            a = _get_prop_default(init, "a", 1)
            b = _get_prop_default(init, "b", 0)
            c = _get_prop_default(init, "c", 0)
            d = _get_prop_default(init, "d", 1)
            e = _get_prop_default(init, "e", 0)
            f = _get_prop_default(init, "f", 0)
            return DOMMatrix([a, b, c, d, e, f])
        raise TypeError(f"Expected DOMMatrix, got: '{init}'")

    @classmethod
    def fromFloat32Array(cls, init):
        if not isinstance(init, Sequence):
            raise TypeError("Expected Float32Array")
        return DOMMatrix(init)

    @classmethod
    def fromFloat64Array(cls, init):
        if not isinstance(init, Sequence):
            raise TypeError("Expected Float64Array")
        return DOMMatrix(init)

    @staticmethod
    def isMatrix3(matrix):
        if isinstance(matrix, DOMMatrix):
            return True
        if matrix is None:
            return False
        for p in ("a", "b", "c", "d", "e", "f"):
            if not _is_numeric(_get_prop_default(matrix, p)):
                return False
        return True

    @staticmethod
    def isMatrix4(matrix):
        if isinstance(matrix, DOMMatrix):
            return True
        if matrix is None:
            return False
        for p in (
            "m11",
            "m12",
            "m13",
            "m14",
            "m21",
            "m22",
            "m23",
            "m24",
            "m31",
            "m32",
            "m33",
            "m34",
            "m41",
            "m42",
            "m43",
            "m44",
        ):
            if not _is_numeric(_get_prop_default(matrix, p)):
                return False
        return True

    def dump(self):
        mat = self._values
        print(
            [
                mat[0:4],
                mat[4:8],
                mat[8:12],
                mat[12:16],
            ]
        )

    def __repr__(self):
        if self.is2D:
            return f"DOMMatrix {{'a': {self.a}, 'b': {self.b}, 'c': {self.c}, 'd': {self.d}, 'e': {self.e}, 'f': {self.f}, 'is2D': {self.is2D}, 'isIdentity': {self.isIdentity}}}"
        return (
            "DOMMatrix {'a': %s, 'b': %s, 'c': %s, 'd': %s, 'e': %s, 'f': %s, "
            "'m11': %s, 'm12': %s, 'm13': %s, 'm14': %s, 'm21': %s, 'm22': %s, "
            "'m23': %s, 'm24': %s, 'm31': %s, 'm32': %s, 'm33': %s, 'm34': %s, "
            "'m41': %s, 'm42': %s, 'm43': %s, 'm44': %s, 'is2D': %s, 'isIdentity': %s}"
            % (
                self.a,
                self.b,
                self.c,
                self.d,
                self.e,
                self.f,
                self.m11,
                self.m12,
                self.m13,
                self.m14,
                self.m21,
                self.m22,
                self.m23,
                self.m24,
                self.m31,
                self.m32,
                self.m33,
                self.m34,
                self.m41,
                self.m42,
                self.m43,
                self.m44,
                self.is2D,
                self.isIdentity,
            )
        )

    def multiply(self, other=None):
        return DOMMatrix(self._values).multiplySelf(other)

    def multiplySelf(self, other=None):
        other = _coerce_matrix(other)
        self._values = _multiply(other._values, self._values)
        if not other.is2D:
            self._is2d = False
        return self

    def preMultiplySelf(self, other=None):
        other = _coerce_matrix(other)
        self._values = _multiply(self._values, other._values)
        if not other.is2D:
            self._is2d = False
        return self

    def translate(self, tx=0.0, ty=0.0, tz=0.0):
        return DOMMatrix(self._values).translateSelf(tx, ty, tz)

    def translateSelf(self, tx=0.0, ty=0.0, tz=0.0):
        # fmt: off
        self._values = _multiply(
            [
                1, 0, 0, 0,
                0, 1, 0, 0,
                0, 0, 1, 0,
                tx, ty, tz, 1,
            ],
            self._values,
        )
        # fmt: on

        if tz != 0:
            self._is2d = False

        return self

    def scale(
        self,
        scaleX=None,
        scaleY=None,
        scaleZ=None,
        originX=None,
        originY=None,
        originZ=None,
    ):
        return DOMMatrix(self._values).scaleSelf(
            scaleX, scaleY, scaleZ, originX, originY, originZ
        )

    def scale3d(self, scale=1.0, originX=None, originY=None, originZ=None):
        return DOMMatrix(self._values).scale3dSelf(scale, originX, originY, originZ)

    def scale3dSelf(self, scale=1.0, originX=None, originY=None, originZ=None):
        return self.scaleSelf(scale, scale, scale, originX, originY, originZ)

    def scaleSelf(
        self,
        scaleX=None,
        scaleY=None,
        scaleZ=None,
        originX=None,
        originY=None,
        originZ=None,
    ):
        # Not redundant with translate's checks because we need to negate the values later.
        originX = float(originX) if _is_numeric(originX) else 0.0
        originY = float(originY) if _is_numeric(originY) else 0.0
        originZ = float(originZ) if _is_numeric(originZ) else 0.0

        self.translateSelf(originX, originY, originZ)

        scaleX = float(scaleX) if _is_numeric(scaleX) else 1.0
        scaleY = float(scaleY) if _is_numeric(scaleY) else scaleX
        scaleZ = float(scaleZ) if _is_numeric(scaleZ) else 1.0

        # fmt: off
        self._values = _multiply(
            [
                scaleX, 0, 0, 0,
                0, scaleY, 0, 0,
                0, 0, scaleZ, 0,
                0, 0, 0, 1,
            ],
            self._values,
        )
        # fmt: on

        self.translateSelf(-originX, -originY, -originZ)

        if scaleZ != 1 or originZ != 0:
            self._is2d = False

        return self

    def rotateFromVector(self, x=0.0, y=0.0):
        return DOMMatrix(self._values).rotateFromVectorSelf(x, y)

    def rotateFromVectorSelf(self, x=0.0, y=0.0):
        theta = 0.0 if (x == 0 and y == 0) else math.atan2(y, x) * DEGREE_PER_RAD
        return self.rotateSelf(theta)

    def rotate(self, rotX=0.0, rotY=None, rotZ=None):
        return DOMMatrix(self._values).rotateSelf(rotX, rotY, rotZ)

    def rotateSelf(self, rotX=0.0, rotY=None, rotZ=None):
        if rotY is None and rotZ is None:
            rotZ = rotX
            rotX = 0.0
            rotY = 0.0

        rotX = float(rotX) if _is_numeric(rotX) else 0.0
        rotY = 0.0 if not _is_numeric(rotY) else float(rotY)
        rotZ = 0.0 if not _is_numeric(rotZ) else float(rotZ)

        if rotX != 0 or rotY != 0:
            self._is2d = False

        rotX *= RAD_PER_DEGREE
        rotY *= RAD_PER_DEGREE
        rotZ *= RAD_PER_DEGREE

        c = math.cos(rotZ)
        s = math.sin(rotZ)
        # fmt: off
        self._values = _multiply(
            [
                c, s, 0, 0,
                -s, c, 0, 0,
                0, 0, 1, 0,
                0, 0, 0, 1,
            ],
            self._values,
        )
        # fmt: on

        c = math.cos(rotY)
        s = math.sin(rotY)
        # fmt: off
        self._values = _multiply(
            [
                c, 0, -s, 0,
                0, 1, 0, 0,
                s, 0, c, 0,
                0, 0, 0, 1,
            ],
            self._values,
        )
        # fmt: on

        c = math.cos(rotX)
        s = math.sin(rotX)
        # fmt: off
        self._values = _multiply(
            [
                1, 0, 0, 0,
                0, c, s, 0,
                0, -s, c, 0,
                0, 0, 0, 1,
            ],
            self._values,
        )
        # fmt: on

        return self

    def rotateAxisAngle(self, x=0.0, y=0.0, z=0.0, angle=0.0):
        return DOMMatrix(self._values).rotateAxisAngleSelf(x, y, z, angle)

    def rotateAxisAngleSelf(self, x=0.0, y=0.0, z=0.0, angle=0.0):
        length = math.sqrt(x * x + y * y + z * z)
        if length == 0:
            return self

        if length != 1:
            x /= length
            y /= length
            z /= length

        angle *= RAD_PER_DEGREE

        c = math.cos(angle)
        s = math.sin(angle)
        t = 1 - c
        tx = t * x
        ty = t * y

        # fmt: off
        self._values = _multiply(
            [
                tx * x + c, tx * y + s * z, tx * z - s * y, 0,
                tx * y - s * z, ty * y + c, ty * z + s * x, 0,
                tx * z + s * y, ty * z - s * x, t * z * z + c, 0,
                0, 0, 0, 1,
            ],
            self._values,
        )
        # fmt: on

        if x != 0 or y != 0:
            self._is2d = False

        return self

    def skew(self, sx=None, sy=None):
        return DOMMatrix(self._values).skewSelf(sx, sy)

    def skewSelf(self, sx=None, sy=None):
        if not _is_numeric(sx) and not _is_numeric(sy):
            return self

        x = 0.0 if not _is_numeric(sx) else math.tan(float(sx) * RAD_PER_DEGREE)
        y = 0.0 if not _is_numeric(sy) else math.tan(float(sy) * RAD_PER_DEGREE)

        # fmt: off
        self._values = _multiply(
            [
                1, y, 0, 0,
                x, 1, 0, 0,
                0, 0, 1, 0,
                0, 0, 0, 1,
            ],
            self._values,
        )
        # fmt: on

        return self

    def skewX(self, sx):
        return DOMMatrix(self._values).skewXSelf(sx)

    def skewXSelf(self, sx):
        if not _is_numeric(sx):
            return self

        t = math.tan(sx * RAD_PER_DEGREE)

        # fmt: off
        self._values = _multiply(
            [
                1, 0, 0, 0,
                t, 1, 0, 0,
                0, 0, 1, 0,
                0, 0, 0, 1,
            ],
            self._values,
        )
        # fmt: on

        return self

    def skewY(self, sy):
        return DOMMatrix(self._values).skewYSelf(sy)

    def skewYSelf(self, sy):
        if not _is_numeric(sy):
            return self

        t = math.tan(sy * RAD_PER_DEGREE)

        # fmt: off
        self._values = _multiply(
            [
                1, t, 0, 0,
                0, 1, 0, 0,
                0, 0, 1, 0,
                0, 0, 0, 1,
            ],
            self._values,
        )
        # fmt: on

        return self

    def flipX(self):
        # fmt: off
        return DOMMatrix(
            _multiply(
                [
                    -1, 0, 0, 0,
                    0, 1, 0, 0,
                    0, 0, 1, 0,
                    0, 0, 0, 1,
                ],
                self._values,
            )
        )
        # fmt: on

    def flipY(self):
        # fmt: off
        return DOMMatrix(
            _multiply(
                [
                    1, 0, 0, 0,
                    0, -1, 0, 0,
                    0, 0, 1, 0,
                    0, 0, 0, 1,
                ],
                self._values,
            )
        )
        # fmt: on

    def inverse(self):
        return DOMMatrix(self._values).invertSelf()

    def invertSelf(self):
        if self._is2d:
            det = self._values[A] * self._values[D] - self._values[B] * self._values[C]

            # Invertable
            if det != 0:
                result = DOMMatrix()
                result.a = self._values[D] / det
                result.b = -self._values[B] / det
                result.c = -self._values[C] / det
                result.d = self._values[A] / det
                result.e = (
                    self._values[C] * self._values[F]
                    - self._values[D] * self._values[E]
                ) / det
                result.f = (
                    self._values[B] * self._values[E]
                    - self._values[A] * self._values[F]
                ) / det
                return result

            # Not invertable
            self._is2d = False
            self._values = [math.nan] * 16
            return self

        raise RuntimeError("3D matrix inversion is not implemented.")

    def setMatrixValue(self, transformList):
        temp = DOMMatrix(transformList)
        self._values = temp._values[:]
        self._is2d = temp._is2d
        return self

    def transformPoint(self, point=None):
        point = DOMPoint.fromPoint(point or {})
        x = point.x
        y = point.y
        z = point.z
        w = point.w

        values = self._values
        nx = values[M11] * x + values[M21] * y + values[M31] * z + values[M41] * w
        ny = values[M12] * x + values[M22] * y + values[M32] * z + values[M42] * w
        nz = values[M13] * x + values[M23] * y + values[M33] * z + values[M43] * w
        nw = values[M14] * x + values[M24] * y + values[M34] * z + values[M44] * w

        return DOMPoint(nx, ny, nz, nw)

    def toFloat32Array(self):
        return [float(v) for v in self._values]

    def toFloat64Array(self):
        return self._values[:]

    def toJSON(self):
        return {
            "a": self.a,
            "b": self.b,
            "c": self.c,
            "d": self.d,
            "e": self.e,
            "f": self.f,
            "m11": self.m11,
            "m12": self.m12,
            "m13": self.m13,
            "m14": self.m14,
            "m21": self.m21,
            "m22": self.m22,
            "m23": self.m23,
            "m24": self.m24,
            "m31": self.m31,
            "m32": self.m32,
            "m33": self.m33,
            "m34": self.m34,
            "m41": self.m41,
            "m42": self.m42,
            "m43": self.m43,
            "m44": self.m44,
            "is2D": self.is2D,
            "isIdentity": self.isIdentity,
        }

    def toString(self):
        name = "matrix" if self.is2D else "matrix3d"
        values = (
            [self.a, self.b, self.c, self.d, self.e, self.f]
            if self.is2D
            else self._values
        )

        def simplify(n):
            s = f"{float(n):.12f}"
            s = re.sub(r"\.([^0])?0*$", r".\1", s)
            s = re.sub(r"\.$", "", s)
            s = re.sub(r"^-0$", "0", s)
            return s

        return f"{name}({', '.join(simplify(v) for v in values)})"

    def clone(self):
        return DOMMatrix(self)


#
# Helpers to reconcile Skia and DOMMatrix's disagreement about row/col orientation
#

Matrix: TypeAlias = str | DOMMatrix | Abcdef | Sequence[float]


def toSkMatrix(*args):
    if len(args) != 1 and len(args) < 6:
        raise TypeError("not enough arguments")
    try:
        m = DOMMatrix(*args)
        return [m.a, m.c, m.e, m.b, m.d, m.f, m.m14, m.m24, m.m44]
    except Exception as exc:
        raise TypeError(f"Invalid transform matrix argument(s): {exc}") from exc


def fromSkMatrix(skMatrix):
    a, b, c, d, e, f, p0, p1, p2 = skMatrix
    # fmt: off
    return DOMMatrix(
        [
            a, d, 0, p0,
            b, e, 0, p1,
            0, 0, 1, 0,
            c, f, 0, p2,
        ]
    )
    #fmt: on


__all__ = ["DOMPoint", "DOMMatrix", "DOMRect", "toSkMatrix", "fromSkMatrix"]
