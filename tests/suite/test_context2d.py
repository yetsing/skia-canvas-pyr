from __future__ import annotations

import dataclasses
import math
from pathlib import Path
from typing import Any, cast

import pytest

from skia_canvas_pyr import (
    Canvas,
    DOMMatrix,
    DOMPoint,
    FontLibrary,
    ImageData,
    Path2D,
    loadImage,
    CanvasRenderingContext2D,
)
from skia_canvas_pyr.classes import css

BLACK = (0, 0, 0, 255)
WHITE = (255, 255, 255, 255)
GREEN = (0, 128, 0, 255)
CLEAR = (0, 0, 0, 0)

WIDTH = 512
HEIGHT = 512

REPO_ROOT = Path(__file__).resolve().parents[2]
ASSETS_DIR = REPO_ROOT / "tests" / "assets"
FONTS_DIR = ASSETS_DIR / "fonts"

pytestmark = pytest.mark.skipif(
    not ASSETS_DIR.exists(),
    reason="tests/assets is missing; run tests/pretest.py first",
)


def bytearray_set(arr: bytearray, index: int, values: list[int]) -> None:
    for i, val in enumerate(values):
        arr[index + i] = val


def bytearray_some(arr: bytearray, func) -> bool:
    return any(func(val) for val in arr)


def near(a: float, b: float, eps: float = 0.005) -> None:
    assert abs(a - b) <= eps


def px(ctx, x: int | float, y: int | float) -> tuple[int, int, int, int]:
    data = ctx.getImageData(x, y, 1, 1).data
    return tuple(data[:4])


def load_asset(rel: str):
    return loadImage(str(ASSETS_DIR / rel))


def _each(args, func):
    for arg in args:
        func(*arg)


@pytest.fixture
def canvas_ctx():
    canvas = Canvas(WIDTH, HEIGHT)
    ctx = canvas.getContext("2d")
    return canvas, ctx


class TestGetSet:
    def test_current_transform(self, canvas_ctx):
        _, ctx = canvas_ctx
        ctx.scale(0.1, 0.3)
        matrix = ctx.currentTransform
        near(matrix.a, 0.1)
        near(matrix.b, 0)
        near(matrix.c, 0)
        near(matrix.d, 0.3)
        near(matrix.e, 0)
        near(matrix.f, 0)

        ctx.resetTransform()
        near(ctx.currentTransform.a, 1)
        near(ctx.currentTransform.d, 1)

        ctx.currentTransform = matrix
        near(ctx.currentTransform.a, 0.1)
        near(ctx.currentTransform.d, 0.3)

    def test_font(self, canvas_ctx):
        _, ctx = canvas_ctx
        assert ctx.font == "10px sans-serif"
        font = "16px Baskerville, serif"
        parsed = css.font(font)
        assert parsed is not None
        canonical = parsed.canonical
        ctx.font = font
        assert ctx.font == canonical
        ctx.font = "invalid"
        assert ctx.font == canonical

    def test_global_alpha(self, canvas_ctx):
        _, ctx = canvas_ctx
        assert ctx.globalAlpha == 1
        ctx.globalAlpha = 0.25
        near(ctx.globalAlpha, 0.25)
        ctx.globalAlpha = -1
        near(ctx.globalAlpha, 0.25)
        ctx.globalAlpha = 3
        near(ctx.globalAlpha, 0.25)
        ctx.globalAlpha = 0
        assert ctx.globalAlpha == 0

    def test_global_composite_operation(self, canvas_ctx):
        _, ctx = canvas_ctx
        ops = [
            "source-over",
            "destination-over",
            "copy",
            "destination",
            "clear",
            "source-in",
            "destination-in",
            "source-out",
            "destination-out",
            "source-atop",
            "destination-atop",
            "xor",
            "lighter",
            "multiply",
            "screen",
            "overlay",
            "darken",
            "lighten",
            "color-dodge",
            "color-burn",
            "hard-light",
            "soft-light",
            "difference",
            "exclusion",
            "hue",
            "saturation",
            "color",
            "luminosity",
        ]
        assert ctx.globalCompositeOperation == "source-over"
        ctx.globalCompositeOperation = "invalid"
        assert ctx.globalCompositeOperation == "source-over"
        for op in ops:
            ctx.globalCompositeOperation = op
            assert ctx.globalCompositeOperation == op

    def test_image_smoothing(self, canvas_ctx):
        _, ctx = canvas_ctx
        assert ctx.imageSmoothingEnabled is True
        ctx.imageSmoothingEnabled = False
        assert ctx.imageSmoothingEnabled is False

        assert ctx.imageSmoothingQuality == "low"
        ctx.imageSmoothingQuality = "invalid"
        assert ctx.imageSmoothingQuality == "low"
        for val in ["low", "medium", "high"]:
            ctx.imageSmoothingQuality = val
            assert ctx.imageSmoothingQuality == val

    def test_line_cap_dash_join_width_text_align(self, canvas_ctx):
        _, ctx = canvas_ctx
        assert ctx.lineCap == "butt"
        ctx.lineCap = "invalid"
        assert ctx.lineCap == "butt"
        for val in ["butt", "square", "round"]:
            ctx.lineCap = val
            assert ctx.lineCap == val

        assert ctx.getLineDash() == []
        ctx.setLineDash([1, 2, 3, 4])
        assert ctx.getLineDash() == [1, 2, 3, 4]
        ctx.setLineDash([math.nan])
        assert ctx.getLineDash() == [1, 2, 3, 4]

        assert ctx.lineJoin == "miter"
        ctx.lineJoin = "invalid"
        assert ctx.lineJoin == "miter"
        for val in ["miter", "round", "bevel"]:
            ctx.lineJoin = val
            assert ctx.lineJoin == val

        ctx.lineWidth = 10
        assert ctx.lineWidth == 10
        ctx.lineWidth = math.inf
        assert ctx.lineWidth == 10
        ctx.lineWidth = -math.inf
        assert ctx.lineWidth == 10
        ctx.lineWidth = -5
        assert ctx.lineWidth == 10
        ctx.lineWidth = 0
        assert ctx.lineWidth == 10

        assert ctx.textAlign == "start"
        ctx.textAlign = "invalid"
        assert ctx.textAlign == "start"
        for val in ["start", "end", "left", "center", "right", "justify"]:
            ctx.textAlign = val
            assert ctx.textAlign == val


class TestCreate:
    def test_context_and_pages(self, canvas_ctx):
        canvas, ctx = canvas_ctx
        assert canvas.getContext("invalid") is None
        assert canvas.getContext("2d") is ctx
        assert canvas.pages[0] is ctx
        assert ctx.canvas is canvas

    def test_multiple_pages(self, canvas_ctx):
        canvas, ctx = canvas_ctx
        ctx2 = canvas.newPage(WIDTH * 2, HEIGHT * 2)
        assert canvas.width == WIDTH * 2
        assert canvas.height == HEIGHT * 2
        assert canvas.pages[0] is ctx
        assert canvas.pages[1] is ctx2
        assert ctx.canvas is canvas
        assert ctx2.canvas is canvas

    def test_image_data(self, canvas_ctx):
        _, ctx = canvas_ctx
        width, height = 123, 456
        bmp = ctx.createImageData(width, height)
        assert bmp.width == width
        assert bmp.height == height
        assert len(bmp.data) == width * height * 4
        assert list(bmp.data[:4]) == list(CLEAR)

        blank = ImageData(width, height)
        assert blank.width == width
        assert blank.height == height
        assert len(blank.data) == width * height * 4
        assert list(blank.data[:4]) == list(CLEAR)

        ImageData(bytes(blank.data), width, height)
        ImageData(bytes(blank.data), height, width)
        ImageData(bytes(blank.data), width)
        ImageData(bytes(blank.data), height)

        with pytest.raises(Exception):
            ImageData(blank.data, width + 1, height)
        with pytest.raises(Exception):
            ImageData(blank.data, width + 1)
        with pytest.raises(Exception):
            ImageData(cast(Any, bytes(blank.data)))

        ImageData(blank)


class TestCanvasPattern:

    def test_from_image(self, canvas_ctx):
        _, ctx = canvas_ctx
        image = load_asset("checkers.png")
        pattern = ctx.createPattern(image, "repeat")
        width, height = 20, 20

        ctx.imageSmoothingEnabled = False
        ctx.fillStyle = pattern
        ctx.fillRect(0, 0, width, height)

        bmp = ctx.getImageData(0, 0, width, height)
        black_pixel = True
        assert len(bmp.data) == width * height * 4
        for i in range(0, len(bmp.data), 4):
            if (i % (bmp.width * 4)) != 0:
                black_pixel = not black_pixel
            assert tuple(bmp.data[i : i + 4]) == (BLACK if black_pixel else WHITE)

    def test_from_image_data(self, canvas_ctx):
        _, ctx = canvas_ctx

        blank = Canvas()
        ctx.fillStyle = ctx.createPattern(blank, "repeat")
        ctx.fillRect(0, 0, 20, 20)

        checkers = Canvas(2, 2)
        pat_ctx = checkers.getContext("2d")
        pat_ctx.fillStyle = "white"
        pat_ctx.fillRect(0, 0, 2, 2)
        pat_ctx.fillStyle = "black"
        pat_ctx.fillRect(0, 0, 1, 1)
        pat_ctx.fillRect(1, 1, 1, 1)

        checkers_data = pat_ctx.getImageData(0, 0, 2, 2)

        pattern = ctx.createPattern(checkers_data, "repeat")
        ctx.fillStyle = pattern
        ctx.fillRect(0, 0, 20, 20)

        bmp = ctx.getImageData(0, 0, 20, 20)
        black_pixel = True
        for i in range(0, len(bmp.data), 4):
            if (i % (bmp.width * 4)) != 0:
                black_pixel = not black_pixel
            assert tuple(bmp.data[i : i + 4]) == (BLACK if black_pixel else WHITE)

    def test_from_canvas(self, canvas_ctx):
        _, ctx = canvas_ctx

        blank = Canvas()
        ctx.fillStyle = ctx.createPattern(blank, "repeat")
        ctx.fillRect(0, 0, 20, 20)

        checkers = Canvas(2, 2)
        pat_ctx = checkers.getContext("2d")
        pat_ctx.fillStyle = "white"
        pat_ctx.fillRect(0, 0, 2, 2)
        pat_ctx.fillStyle = "black"
        pat_ctx.fillRect(0, 0, 1, 1)
        pat_ctx.fillRect(1, 1, 1, 1)

        pattern = ctx.createPattern(checkers, "repeat")
        ctx.fillStyle = pattern
        ctx.fillRect(0, 0, 20, 20)

        bmp = ctx.getImageData(0, 0, 20, 20)
        black_pixel = True
        for i in range(0, len(bmp.data), 4):
            if (i % (bmp.width * 4)) != 0:
                black_pixel = not black_pixel
            assert tuple(bmp.data[i : i + 4]) == (BLACK if black_pixel else WHITE)

    def test_with_local_transform(self, canvas_ctx):
        # call func with an ImageData-offset and pixel color value appropriate for a 4-quadrant pattern within
        # the width and height that's white in the upper-left & lower-right and black in the other corners
        def eachPixels(bmp, func):
            width = bmp.width
            height = bmp.height
            for x in range(width):
                for y in range(height):
                    i = y * 4 * width + x * 4
                    clr = (
                        255
                        if (x < width / 2 and y < height / 2)
                        or (x >= width / 2 and y >= height / 2)
                        else 0
                    )
                    func(i, clr)

        # create a canvas with a single repeat of the pattern within its dims
        def makeCheckerboard(w, h):
            check = Canvas(w, h)
            ctx = check.getContext("2d")
            bmp = ctx.createImageData(w, h)
            eachPixels(
                bmp, lambda i, clr: bytearray_set(bmp.data, i, [clr, clr, clr, 255])
            )
            ctx.putImageData(bmp, 0, 0)
            return check

        # verify that the region looks like a single 4-quadrant checkerboard cell
        def isCheckerboard(ctx, w, h):
            bmp = ctx.getImageData(0, 0, w, h)

            def _inner_check(i, clr):
                px = tuple(bmp.data[i : i + 4])
                assert px == (clr, clr, clr, 255)

            eachPixels(bmp, _inner_check)

        _, ctx = canvas_ctx
        w, h = 160, 160
        pat = ctx.createPattern(makeCheckerboard(w, h), "repeat")
        mat = DOMMatrix()

        ctx.fillStyle = pat

        # draw a single repeat of the pattern at each scale and then confirm that
        # the transformation succeeded
        for mag in [1, 0.5, 0.25, 0.125, 0.0625]:
            mat = DOMMatrix().scale(mag)
            pat.setTransform(mat)
            # make sure the alternative matrix syntaxes also work
            pat.setTransform(mag, 0, 0, mag, 0, 0)
            pat.setTransform([mag, 0, 0, mag, 0, 0])
            pat.setTransform({"a": mag, "b": 0, "c": 0, "d": mag, "e": 0, "f": 0})
            ctx.fillRect(0, 0, w * mag, h * mag)
            isCheckerboard(ctx, w * mag, h * mag)


class TestCanvasGradient:
    def test_linear(self, canvas_ctx):
        _, ctx = canvas_ctx
        gradient = ctx.createLinearGradient(1, 1, 19, 1)
        ctx.fillStyle = gradient
        gradient.addColorStop(0, "#fff")
        gradient.addColorStop(1, "#000")
        ctx.fillRect(0, 0, 21, 1)

        assert px(ctx, 0, 0) == WHITE
        assert px(ctx, 20, 0) == BLACK

    def test_radial(self, canvas_ctx):
        _, ctx = canvas_ctx
        x, y, inside, outside = 100, 100, 45, 55
        inner = [x, y, 25]
        outer = [x, y, 50]
        gradient = ctx.createRadialGradient(*inner, *outer)
        ctx.fillStyle = gradient
        gradient.addColorStop(0, "#fff")
        gradient.addColorStop(0.5, "#000")
        gradient.addColorStop(1, "#000")
        gradient.addColorStop(1, "red")
        ctx.fillRect(0, 0, 200, 200)

        assert px(ctx, x, y) == WHITE
        assert px(ctx, x + inside, y) == BLACK
        assert px(ctx, x, y + inside) == BLACK
        assert px(ctx, x + outside, y) == (255, 0, 0, 255)
        assert px(ctx, x, y + outside) == (255, 0, 0, 255)

    def test_conic(self, canvas_ctx):
        _, ctx = canvas_ctx
        # draw a sweep with white at top and black on bottom
        gradient = ctx.createConicGradient(0, 256, 256)
        ctx.fillStyle = gradient
        gradient.addColorStop(0, "#fff")
        gradient.addColorStop(0.5, "#000")
        gradient.addColorStop(1, "#fff")
        ctx.fillRect(0, 0, 512, 512)

        assert px(ctx, 5, 256) == BLACK
        assert px(ctx, 500, 256) == WHITE

        # rotate 90° so black is left and white is right
        gradient = ctx.createConicGradient(math.pi / 2, 256, 256)
        ctx.fillStyle = gradient
        gradient.addColorStop(0, "#fff")
        gradient.addColorStop(0.5, "#000")
        gradient.addColorStop(1, "#fff")
        ctx.fillRect(0, 0, 512, 512)

        assert px(ctx, 256, 500) == WHITE
        assert px(ctx, 256, 5) == BLACK


class TestCanvasTexture:
    @staticmethod
    def before_each(ctx: CanvasRenderingContext2D):
        w = 40
        wavePath = Path2D()
        wavePath.moveTo(-w / 2, w / 2)
        wavePath.bezierCurveTo(-w * 3 / 8, w * 3 / 4, -w / 8, w * 3 / 4, 0, w / 2)
        wavePath.bezierCurveTo(w / 8, w / 4, w * 3 / 8, w / 4, w / 2, w / 2)
        wavePath.bezierCurveTo(w * 5 / 8, w * 3 / 4, w * 7 / 8, w * 3 / 4, w, w / 2)
        wavePath.bezierCurveTo(w * 9 / 8, w / 4, w * 11 / 8, w / 4, w * 3 / 2, w / 2)
        waves = ctx.createTexture(
            [w, w / 2],
            {"path": wavePath, "color": "black", "line": 3, "angle": math.pi / 7},
        )

        n = 50
        nylonPath = Path2D()
        nylonPath.moveTo(0, n / 4)
        nylonPath.lineTo(n / 4, n / 4)
        nylonPath.lineTo(n / 4, 0)
        nylonPath.moveTo(n * 3 / 4, n)
        nylonPath.lineTo(n * 3 / 4, n * 3 / 4)
        nylonPath.lineTo(n, n * 3 / 4)
        nylonPath.moveTo(n / 4, n / 2)
        nylonPath.lineTo(n / 4, n * 3 / 4)
        nylonPath.lineTo(n / 2, n * 3 / 4)
        nylonPath.moveTo(n / 2, n / 4)
        nylonPath.lineTo(n * 3 / 4, n / 4)
        nylonPath.lineTo(n * 3 / 4, n / 2)
        nylon = ctx.createTexture(
            n,
            {
                "path": nylonPath,
                "color": "black",
                "line": 5,
                "cap": "square",
                "angle": math.pi / 8,
            },
        )

        lines = ctx.createTexture(8, {"line": 4, "color": "black"})

        return waves, nylon, lines

    def test_with_filled_path2d(self, canvas_ctx):
        _, ctx = canvas_ctx
        _, nylon, _ = self.before_each(ctx)
        ctx.fillStyle = nylon
        ctx.fillRect(10, 10, 80, 80)

        assert px(ctx, 26, 24) == CLEAR
        assert px(ctx, 28, 26) == BLACK
        assert px(ctx, 48, 48) == BLACK
        assert px(ctx, 55, 40) == CLEAR

    def test_with_stroked_path2d(self, canvas_ctx):
        _, ctx = canvas_ctx
        waves, _, _ = self.before_each(ctx)
        ctx.strokeStyle = waves
        ctx.lineWidth = 10
        ctx.moveTo(0, 0)
        ctx.lineTo(100, 100)
        ctx.stroke()

        assert px(ctx, 10, 10) == CLEAR
        assert px(ctx, 16, 16) == BLACK
        assert px(ctx, 73, 73) == BLACK
        assert px(ctx, 75, 75) == CLEAR

    def test_with_lines(self, canvas_ctx):
        _, ctx = canvas_ctx
        _, _, lines = self.before_each(ctx)
        ctx.fillStyle = lines
        ctx.fillRect(10, 10, 80, 80)

        assert px(ctx, 22, 22) == CLEAR
        assert px(ctx, 25, 25) == BLACK
        assert px(ctx, 73, 73) == CLEAR
        assert px(ctx, 76, 76) == BLACK


class TestSupports:
    def test_filter(self, canvas_ctx):
        canvas, ctx = canvas_ctx
        gpu = canvas.gpu
        canvas.gpu = False
        ctx.filter = "blur(5px) invert(56%) sepia(63%) saturate(4837%) hue-rotate(163deg) brightness(96%) contrast(101%)"
        ctx.fillRect(0, 0, 20, 20)
        assert px(ctx, 10, 10) == (0, 162, 213, 245)
        canvas.gpu = gpu

    def test_shadow(self, canvas_ctx):
        _, ctx = canvas_ctx
        sin = math.sin(1.15 * math.pi)
        cos = math.cos(1.15 * math.pi)
        ctx.translate(150, 150)
        ctx.transform(cos, sin, -sin, cos, 0, 0)

        ctx.shadowColor = "#000"
        ctx.shadowBlur = 5
        ctx.shadowOffsetX = 10
        ctx.shadowOffsetY = 10
        ctx.fillStyle = "#eee"
        ctx.fillRect(25, 25, 65, 10)

        # ensure that the shadow is actually fuzzy despite the transforms
        assert not px(ctx, 143, 117) == BLACK

    def test_clip(self, canvas_ctx):
        _, ctx = canvas_ctx
        ctx.fillStyle = "white"
        ctx.fillRect(0, 0, 2, 2)

        # overlapping rectangles to use as a clipping mask
        ctx.rect(0, 0, 2, 1)
        ctx.rect(1, 0, 1, 2)

        # b | w
        # -----
        # w | b
        ctx.save()
        ctx.clip("evenodd")
        ctx.fillStyle = "black"
        ctx.fillRect(0, 0, 2, 2)
        ctx.restore()

        assert px(ctx, 0, 0) == BLACK
        assert px(ctx, 1, 0) == WHITE
        assert px(ctx, 0, 1) == WHITE
        assert px(ctx, 1, 1) == BLACK

        # b | b
        # -----
        # w | b
        ctx.save()
        ctx.clip()  # nonzero
        ctx.fillStyle = "black"
        ctx.fillRect(0, 0, 2, 2)
        ctx.restore()

        assert px(ctx, 0, 0) == BLACK
        assert px(ctx, 1, 0) == BLACK
        assert px(ctx, 0, 1) == WHITE
        assert px(ctx, 1, 1) == BLACK

        # test intersection of sequential clips while incorporating transform
        ctx.fillStyle = "black"
        ctx.fillRect(0, 0, WIDTH, HEIGHT)

        ctx.save()
        ctx.beginPath()
        ctx.rect(20, 20, 60, 60)
        ctx.clip()
        ctx.fillStyle = "white"
        ctx.fillRect(0, 0, WIDTH, HEIGHT)

        ctx.beginPath()
        ctx.translate(20, 20)
        ctx.rect(0, 0, 30, 30)
        ctx.clip()
        ctx.fillStyle = "green"
        ctx.fillRect(0, 0, WIDTH, HEIGHT)
        ctx.restore()

        assert px(ctx, 10, 10) == BLACK
        assert px(ctx, 90, 90) == BLACK
        assert px(ctx, 22, 22) == GREEN
        assert px(ctx, 48, 48) == GREEN
        assert px(ctx, 52, 52) == WHITE

        # non-overlapping clips & empty clips should prevent drawing altogether
        ctx.beginPath()
        ctx.rect(20, 20, 30, 30)
        ctx.clip()
        ctx.fillStyle = "black"
        ctx.fillRect(0, 0, WIDTH, HEIGHT)

        ctx.save()
        ctx.beginPath()
        ctx.rect(25, 25, 0, 0)
        ctx.clip()
        ctx.fillStyle = "green"
        ctx.fillRect(0, 0, WIDTH, HEIGHT)
        ctx.restore()

        ctx.save()
        ctx.beginPath()
        ctx.rect(0, 0, 10, 10)
        ctx.clip()
        ctx.fillStyle = "green"
        ctx.fillRect(0, 0, WIDTH, HEIGHT)
        ctx.restore()

        assert px(ctx, 30, 30) == BLACK

    def test_fill(self, canvas_ctx):
        _, ctx = canvas_ctx
        ctx.fillStyle = "white"
        ctx.fillRect(0, 0, 2, 2)

        # set the current path to a pair of overlapping rects
        ctx.fillStyle = "black"
        ctx.rect(0, 0, 2, 1)
        ctx.rect(1, 0, 1, 2)

        # b | w
        # -----
        # w | b
        ctx.fill("evenodd")
        assert px(ctx, 0, 0) == BLACK
        assert px(ctx, 1, 0) == WHITE
        assert px(ctx, 0, 1) == WHITE
        assert px(ctx, 1, 1) == BLACK

        # b | b
        # -----
        # w | b
        ctx.fill()  # nonzero
        assert px(ctx, 0, 0) == BLACK
        assert px(ctx, 1, 0) == BLACK
        assert px(ctx, 0, 1) == WHITE
        assert px(ctx, 1, 1) == BLACK

    def test_fill_text(self, canvas_ctx):
        canvas, ctx = canvas_ctx

        argsets = [
            (("A", 10, 10), True),
            (("A", 10, 10, None), True),
            (("A", 10, 10, math.nan), False),
            (("A", 10, 10, math.inf), False),
            (("A", 10, 10, -math.inf), False),
            ((1234, 10, 10), True),
            ((False, 10, 10), True),
            (({}, 10, 10), True),
        ]
        for args, should_draw in argsets:
            canvas.width = WIDTH
            ctx.textBaseline = "middle"
            ctx.textAlign = "center"
            ctx.fillText(*args)

            data = ctx.getImageData(0, 0, 20, 20).data
            has_ink = bytearray_some(data, lambda a: a)
            assert has_ink == should_draw

    def test_round_rect(self, canvas_ctx):
        _, ctx = canvas_ctx
        dim = WIDTH / 2
        radii = [50, 25, {"x": 15, "y": 15}, DOMPoint(20, 10)]
        ctx.beginPath()
        ctx.roundRect(dim, dim, dim, dim, radii)
        ctx.roundRect(dim, dim, -dim, -dim, radii)
        ctx.roundRect(dim, dim, -dim, dim, radii)
        ctx.roundRect(dim, dim, dim, -dim, radii)
        ctx.fill()

        off = [[3, 3], [dim - 14, dim - 14], [dim - 4, 3], [7, dim - 6]]
        on = [[5, 5], [dim - 17, dim - 17], [dim - 9, 3], [9, dim - 9]]

        for x, y in on:
            assert px(ctx, x, y) == BLACK
            assert px(ctx, x, HEIGHT - y - 1) == BLACK
            assert px(ctx, WIDTH - x - 1, y) == BLACK
            assert px(ctx, WIDTH - x - 1, HEIGHT - y - 1) == BLACK

        for x, y in off:
            assert px(ctx, x, y) == CLEAR
            assert px(ctx, x, HEIGHT - y - 1) == CLEAR
            assert px(ctx, WIDTH - x - 1, y) == CLEAR
            assert px(ctx, WIDTH - x - 1, HEIGHT - y - 1) == CLEAR

    def test_get_image_data(self, canvas_ctx):
        _, ctx = canvas_ctx
        ctx.fillStyle = "rgba(255,0,0, 0.25)"
        ctx.fillRect(0, 0, 1, 6)

        ctx.fillStyle = "rgba(0,255,0, 0.5)"
        ctx.fillRect(1, 0, 1, 6)

        ctx.fillStyle = "rgba(0,0,255, 0.75)"
        ctx.fillRect(2, 0, 1, 6)

        width, height = 3, 6
        bmp1 = ctx.getImageData(0, 0, width, height)
        bmp2 = ctx.getImageData(
            width, height, -width, -height
        )  # negative dimensions shift origin
        for bmp in [bmp1, bmp2]:
            assert bmp.width == width
            assert bmp.height == height
            assert len(bmp.data) == width * height * 4
            assert tuple(bmp.data[:4]) == (255, 0, 0, 64)
            assert tuple(bmp.data[4:8]) == (0, 255, 0, 128)
            assert tuple(bmp.data[8:12]) == (0, 0, 255, 191)
            for x in range(width):
                for y in range(height):
                    i = 4 * (y * width + x)
                    pixel = tuple(bmp.data[i : i + 4])
                    assert px(ctx, x, y) == pixel

    def test_put_image_data(self, canvas_ctx):
        _, ctx = canvas_ctx
        with pytest.raises(TypeError):
            ctx.putImageData({}, 0, 0)
        with pytest.raises(TypeError):
            ctx.putImageData(None, 0, 0)

        srcImageData = ctx.createImageData(2, 2)
        bytearray_set(
            srcImageData.data,
            0,
            [1, 2, 3, 255, 5, 6, 7, 255, 0, 1, 2, 255, 4, 5, 6, 255],
        )

        ctx.putImageData(srcImageData, -1, -1)
        resImageData = ctx.getImageData(0, 0, 2, 2)
        assert bytes(resImageData.data) == bytes(
            [4, 5, 6, 255, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        )

        # try mask rect
        ctx.reset()
        ctx.putImageData(srcImageData, 0, 0, 1, 1, 1, 1)
        resImageData = ctx.getImageData(0, 0, 2, 2)
        assert bytes(resImageData.data) == bytes(
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 5, 6, 255]
        )

        # try negative dimensions
        ctx.reset()
        ctx.putImageData(srcImageData, 0, 0, 1, 1, -1, -1)
        resImageData = ctx.getImageData(0, 0, 2, 2)
        assert bytes(resImageData.data) == bytes(
            [1, 2, 3, 255, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        )

    def test_is_point_in_path(self, canvas_ctx):
        _, ctx = canvas_ctx
        inStroke = [100, 94]
        inFill = [150, 150]
        inBoth = [100, 100]

        ctx.rect(100, 100, 100, 100)
        ctx.lineWidth = 12

        assert ctx.isPointInPath(*inStroke) == False
        assert ctx.isPointInStroke(*inStroke) == True

        assert ctx.isPointInPath(*inFill) == True
        assert ctx.isPointInStroke(*inFill) == False

        assert ctx.isPointInPath(*inBoth) == True
        assert ctx.isPointInStroke(*inBoth) == True

    def test_is_point_in_path_with_path2d(self, canvas_ctx):
        _, ctx = canvas_ctx
        inStroke = [100, 94]
        inFill = [150, 150]
        inBoth = [100, 100]

        p2d = Path2D()
        p2d.rect(100, 100, 100, 100)
        ctx.lineWidth = 12

        assert ctx.isPointInPath(p2d, *inStroke) == False
        assert ctx.isPointInStroke(p2d, *inStroke) == True

        assert ctx.isPointInPath(p2d, *inFill) == True
        assert ctx.isPointInStroke(p2d, *inFill) == False

        assert ctx.isPointInPath(p2d, *inBoth) == True
        assert ctx.isPointInStroke(p2d, *inBoth) == True

    def test_letter_spacing(self, canvas_ctx):
        FontLibrary.use(FONTS_DIR / "Monoton-Regular.woff")
        _, ctx = canvas_ctx
        x, y = 40, 100
        size = 32
        text = "RR"
        ctx.font = f"{size}px Monoton"
        ctx.letterSpacing = "20px"
        ctx.fillStyle = "black"
        ctx.fillText(text, x, y)

        # there should be no initial added space indenting the beginning of the line
        assert (
            bytearray_some(ctx.getImageData(x, y - size, 10, size).data, lambda a: a)
            == True
        )

        # there should be whitespace between the first and second characters
        assert (
            bytearray_some(
                ctx.getImageData(x + 28, y - size, 18, size).data, lambda a: a
            )
            == False
        )

        # check whether upstream has fixed the indent bug and our compensation is now outdenting
        assert (
            bytearray_some(
                ctx.getImageData(x - 20, y - size, 18, size).data, lambda a: a
            )
            == False
        )

        # make sure the extra space skia adds to the beginning/end have been subtracted
        near(ctx.measureText(text).width, 74)
        ctx.textWrap = True
        near(ctx.measureText(text).width, 74)

    def test_measure_text(self, canvas_ctx):
        _, ctx = canvas_ctx
        ctx.font = "20px Arial, DejaVu Sans"

        ø = ctx.measureText("").width
        _ = ctx.measureText(" ").width
        __ = ctx.measureText("  ").width
        foo = ctx.measureText("foo").width
        foobar = ctx.measureText("foobar").width
        __foo = ctx.measureText("  foo").width
        __foo__ = ctx.measureText("  foo  ").width

        assert ø < _
        assert _ < __
        assert foo < foobar
        assert __foo > foo
        assert __foo__ > __foo

        # start from the default, alphabetic baseline
        msg = "Lordran gypsum"
        metrics = ctx.measureText(msg)

        # + means up, - means down when it comes to baselines
        assert metrics.alphabeticBaseline == 0
        assert metrics.hangingBaseline > 0
        assert metrics.ideographicBaseline < 0

        # for ascenders + means up, for descenders + means down
        assert metrics.actualBoundingBoxAscent > 0
        assert metrics.actualBoundingBoxDescent > 0
        assert metrics.actualBoundingBoxAscent > metrics.actualBoundingBoxDescent

        # make sure the polarity has flipped for 'top' baseline
        ctx.textBaseline = "top"
        metrics = ctx.measureText("Lordran gypsum")
        assert metrics.alphabeticBaseline < 0
        assert metrics.hangingBaseline < 0
        assert metrics.actualBoundingBoxAscent < 0
        assert metrics.actualBoundingBoxDescent > 0

        # width calculations should be the same (modulo rounding) for any alignment
        width_list = []
        for align in ["left", "center", "right"]:
            ctx.textAlign = align
            width_list.append(ctx.measureText(msg).width)
        lft, cnt, rgt = width_list
        near(lft, cnt)
        near(cnt, rgt)

        # make sure string indices account for trailing whitespace and non-8-bit characters
        text = " 石 "
        indexes = ctx.measureText(text).lines[0]
        startIndex = indexes.get("startIndex")
        endIndex = indexes.get("endIndex")
        assert text[startIndex:endIndex] == text

    def test_create_projection(self, canvas_ctx):
        _, ctx = canvas_ctx
        quad = [
            WIDTH * 0.33,
            HEIGHT / 2,
            WIDTH * 0.66,
            HEIGHT / 2,
            WIDTH,
            HEIGHT * 0.9,
            0,
            HEIGHT * 0.9,
        ]

        matrix = ctx.createProjection(quad)
        ctx.setTransform(matrix)

        ctx.fillStyle = "black"
        ctx.fillRect(0, 0, WIDTH / 4, HEIGHT)
        ctx.fillStyle = "white"
        ctx.fillRect(WIDTH / 4, 0, WIDTH / 4, HEIGHT)
        ctx.fillStyle = "green"
        ctx.fillRect(WIDTH / 2, 0, WIDTH / 4, HEIGHT)
        ctx.resetTransform()

        x = WIDTH / 2
        y = HEIGHT / 2 + 2
        assert px(ctx, x, y - 5) == CLEAR
        assert px(ctx, x + 25, y) == GREEN
        assert px(ctx, x + 75, y) == CLEAR
        assert px(ctx, x - 25, y) == WHITE
        assert px(ctx, x - 75, y) == BLACK
        assert px(ctx, x - 100, y) == CLEAR

        y = HEIGHT * 0.9 - 2
        assert px(ctx, x + 100, y) == GREEN
        assert px(ctx, x + 130, y) == CLEAR
        assert px(ctx, x - 75, y) == WHITE
        assert px(ctx, x - 200, y) == BLACK
        assert px(ctx, 0, y) == CLEAR

    def test_draw_image(self, canvas_ctx):
        _, ctx = canvas_ctx
        image = load_asset("checkers.png")
        ctx.imageSmoothingEnabled = False

        ctx.drawImage(image, 0, 0)
        assert px(ctx, 0, 0) == BLACK
        assert px(ctx, 1, 0) == WHITE
        assert px(ctx, 0, 1) == WHITE
        assert px(ctx, 1, 1) == BLACK

        ctx.drawImage(image, -256, -256, 512, 512)
        assert px(ctx, 0, 0) == BLACK
        assert px(ctx, 149, 149) == BLACK

        ctx.clearRect(0, 0, WIDTH, HEIGHT)
        ctx.save()
        ctx.translate(WIDTH / 2, HEIGHT / 2)
        ctx.rotate(0.25 * math.pi)
        ctx.drawImage(image, -256, -256, 512, 512)
        ctx.restore()
        assert px(ctx, 0, 0) == CLEAR
        assert px(ctx, WIDTH / 2, HEIGHT * 0.25) == BLACK
        assert px(ctx, WIDTH / 2, HEIGHT * 0.75) == BLACK
        assert px(ctx, WIDTH * 0.25, HEIGHT / 2) == WHITE
        assert px(ctx, WIDTH * 0.75, HEIGHT / 2) == WHITE
        assert px(ctx, WIDTH - 1, HEIGHT - 1) == CLEAR

        srcCanvas = Canvas(3, 3)
        srcCtx = srcCanvas.getContext("2d")
        srcCtx.fillStyle = "green"
        srcCtx.fillRect(0, 0, 3, 3)
        srcCtx.clearRect(1, 1, 1, 1)

        ctx.drawImage(srcCanvas, 0, 0)
        assert px(ctx, 0, 0) == GREEN
        assert px(ctx, 1, 1) == CLEAR
        assert px(ctx, 2, 2) == GREEN

        ctx.clearRect(0, 0, WIDTH, HEIGHT)
        ctx.drawImage(srcCanvas, -2, -2, 6, 6)
        assert px(ctx, 0, 0) == CLEAR
        assert px(ctx, 2, 0) == GREEN
        assert px(ctx, 2, 2) == GREEN

        ctx.clearRect(0, 0, WIDTH, HEIGHT)
        ctx.save()
        ctx.translate(WIDTH / 2, HEIGHT / 2)
        ctx.rotate(0.25 * math.pi)
        ctx.drawImage(srcCanvas, -256, -256, 512, 512)
        ctx.restore()
        assert px(ctx, WIDTH / 2, HEIGHT * 0.25) == GREEN
        assert px(ctx, WIDTH / 2, HEIGHT * 0.75) == GREEN
        assert px(ctx, WIDTH * 0.25, HEIGHT / 2) == GREEN
        assert px(ctx, WIDTH * 0.75, HEIGHT / 2) == GREEN
        assert px(ctx, WIDTH / 2, HEIGHT / 2) == CLEAR

    def test_draw_canvas(self, canvas_ctx):
        _, ctx = canvas_ctx
        srcCanvas = Canvas(3, 3)
        srcCtx = srcCanvas.getContext("2d")
        srcCtx.fillStyle = "green"
        srcCtx.fillRect(0, 0, 3, 3)
        srcCtx.clearRect(1, 1, 1, 1)

        ctx.drawCanvas(srcCanvas, 0, 0)
        assert px(ctx, 0, 0) == GREEN
        assert px(ctx, 1, 1) == CLEAR
        assert px(ctx, 2, 2) == GREEN

        ctx.clearRect(0, 0, WIDTH, HEIGHT)
        ctx.drawCanvas(srcCanvas, -2, -2, 6, 6)
        assert px(ctx, 0, 0) == CLEAR
        assert px(ctx, 2, 0) == GREEN
        assert px(ctx, 2, 2) == GREEN

        ctx.clearRect(0, 0, WIDTH, HEIGHT)
        ctx.save()
        ctx.translate(WIDTH / 2, HEIGHT / 2)
        ctx.rotate(0.25 * math.pi)
        ctx.drawCanvas(srcCanvas, -256, -256, 512, 512)
        ctx.restore()
        assert px(ctx, WIDTH / 2, HEIGHT * 0.25) == GREEN
        assert px(ctx, WIDTH / 2, HEIGHT * 0.75) == GREEN
        assert px(ctx, WIDTH * 0.25, HEIGHT / 2) == GREEN
        assert px(ctx, WIDTH * 0.75, HEIGHT / 2) == GREEN
        assert px(ctx, WIDTH / 2, HEIGHT / 2) == CLEAR

        ctx.clearRect(0, 0, WIDTH, HEIGHT)
        ctx.drawCanvas(srcCanvas, 1, 1, 2, 2, 0, 0, 2, 2)
        assert px(ctx, 0, 0) == CLEAR
        assert px(ctx, 0, 1) == GREEN
        assert px(ctx, 1, 0) == GREEN
        assert px(ctx, 1, 1) == GREEN

        image = load_asset("checkers.png")
        ctx.drawCanvas(image, 0, 0)

    def test_reset(self, canvas_ctx):
        _, ctx = canvas_ctx
        ctx.fillStyle = "green"
        ctx.scale(2, 2)
        ctx.translate(0, -HEIGHT / 4)

        ctx.fillRect(WIDTH / 4, HEIGHT / 4, WIDTH / 8, HEIGHT / 8)
        assert px(ctx, WIDTH * 0.5 + 1, 0) == GREEN
        assert px(ctx, WIDTH * 0.75 - 1, 0) == GREEN

        ctx.beginPath()
        ctx.rect(WIDTH / 4, HEIGHT / 2, 100, 100)
        ctx.reset()
        ctx.fill()
        assert px(ctx, WIDTH / 2 + 1, HEIGHT / 2 + 1) == CLEAR
        assert px(ctx, WIDTH * 0.5 + 1, 0) == CLEAR
        assert px(ctx, WIDTH * 0.75 - 1, 0) == CLEAR

        ctx.globalAlpha = 0.4
        ctx.reset()
        ctx.fillRect(WIDTH / 2, HEIGHT / 2, 3, 3)
        assert px(ctx, WIDTH / 2 + 1, HEIGHT / 2 + 1) == BLACK


class TestTransform:
    a = 0.1
    b = 0
    c = 0
    d = 0.3
    e = 0
    f = 0

    def test_with_args_list(self, canvas_ctx):
        _, ctx = canvas_ctx
        ctx.transform(self.a, self.b, self.c, self.d, self.e, self.f)
        matrix = ctx.currentTransform
        near(matrix.a, self.a)
        near(matrix.b, self.b)
        near(matrix.c, self.c)
        near(matrix.d, self.d)
        near(matrix.e, self.e)
        near(matrix.f, self.f)

    def test_with_dommatrix(self, canvas_ctx):
        _, ctx = canvas_ctx
        ctx.transform(DOMMatrix().scale(0.1, 0.3))
        matrix = ctx.currentTransform
        near(matrix.a, self.a)
        near(matrix.b, self.b)
        near(matrix.c, self.c)
        near(matrix.d, self.d)
        near(matrix.e, self.e)
        near(matrix.f, self.f)

    def test_with_matrix_like_object(self, canvas_ctx):
        _, ctx = canvas_ctx
        ctx.transform(
            {
                "a": self.a,
                "b": self.b,
                "c": self.c,
                "d": self.d,
                "e": self.e,
                "f": self.f,
            }
        )
        matrix = ctx.currentTransform
        near(matrix.a, self.a)
        near(matrix.b, self.b)
        near(matrix.c, self.c)
        near(matrix.d, self.d)
        near(matrix.e, self.e)
        near(matrix.f, self.f)

    def test_with_css_style_string(self, canvas_ctx):
        _, ctx = canvas_ctx
        transforms = {
            "matrix(1, 2, 3, 4, 5, 6)": "matrix(1, 2, 3, 4, 5, 6)",
            "matrix3d(1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1)": "matrix(1, 0, 0, 1, 0, 0)",
            "rotate(0.5turn)": "matrix(-1, 0, 0, -1, 0, 0)",
            "rotate3d(1, 2, 3, 10deg)": "matrix3d(0.985892913511, 0.141398603856, -0.089563373741, 0, -0.137057961859, 0.989148395009, 0.052920390614, 0, 0.096074336736, -0.039898464624, 0.994574197504, 0, 0, 0, 0, 1)",
            "rotateX(10deg)": "matrix3d(1, 0, 0, 0, 0, 0.984807753012, 0.173648177667, 0, 0, -0.173648177667, 0.984807753012, 0, 0, 0, 0, 1)",
            "rotateY(10deg)": "matrix3d(0.984807753012, 0, -0.173648177667, 0, 0, 1, 0, 0, 0.173648177667, 0, 0.984807753012, 0, 0, 0, 0, 1)",
            "rotateZ(10deg)": "matrix(0.984807753012, 0.173648177667, -0.173648177667, 0.984807753012, 0, 0)",
            "translate(12px, 50px)": "matrix(1, 0, 0, 1, 12, 50)",
            "translate3d(12px, 50px, 3px)": "matrix3d(1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 12, 50, 3, 1)",
            "translateX(2px)": "matrix(1, 0, 0, 1, 2, 0)",
            "translateY(3px)": "matrix(1, 0, 0, 1, 0, 3)",
            "translateZ(2px)": "matrix3d(1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 2, 1)",
            "scale(2, 0.5)": "matrix(2, 0, 0, 0.5, 0, 0)",
            "scale3d(2.5, 120%, 0.3)": "matrix3d(2.5, 0, 0, 0, 0, 1.2, 0, 0, 0, 0, 0.3, 0, 0, 0, 0, 1)",
            "scaleX(2)": "matrix(2, 0, 0, 1, 0, 0)",
            "scaleY(0.5)": "matrix(1, 0, 0, 0.5, 0, 0)",
            "scaleZ(0.3)": "matrix3d(1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0.3, 0, 0, 0, 0, 1)",
            "skew(30deg, 20deg)": "matrix(1, 0.363970234266, 0.577350269190, 1, 0, 0)",
            "skewX(30deg)": "matrix(1, 0, 0.577350269190, 1, 0, 0)",
            "skewY(1.07rad)": "matrix(1, 1.827028196535, 0, 1, 0, 0)",
            "translate(10px, 20px) matrix(1, 2, 3, 4, 5, 6)": "matrix(1, 2, 3, 4, 15, 26)",
            "translate(5px, 6px) scale(2) translate(7px,8px)": "matrix(2, 0, 0, 2, 19, 22)",
            "rotate(30deg) rotate(-.1turn) rotate(.444rad)": "matrix(0.942994450354, 0.332808453321, -0.332808453321, 0.942994450354, 0, 0)",
            "none": "matrix(1, 0, 0, 1, 0, 0)",
            "unset": "matrix(1, 0, 0, 1, 0, 0)",
        }

        for input in transforms:
            matrix = DOMMatrix(input)
            roundtrip = DOMMatrix(matrix.toString())
            assert matrix.toString() == transforms[input]
            assert roundtrip.toString() == transforms[input]

        # check that the context can also take a string
        ctx.transform(f"scale({self.a}, {self.d})")
        matrix = ctx.currentTransform
        near(matrix.a, self.a)
        near(matrix.b, self.b)
        near(matrix.c, self.c)
        near(matrix.d, self.d)
        near(matrix.e, self.e)
        near(matrix.f, self.f)

    def test_rejects_invalid_args(self, canvas_ctx):
        _, ctx = canvas_ctx
        with pytest.raises(Exception, match="Invalid transform matrix"):
            ctx.transform("nonesuch")
        with pytest.raises(Exception, match="not enough arguments"):
            ctx.transform(0, 0, 0)
        ctx.transform(0, 0, 0, math.nan, 0, 0)


class TestParses:

    def test_fonts(self):
        cases = {
            "20px Arial": {"size": 20, "family": ["Arial"]},
            "33pt Arial": {"size": 44, "family": ["Arial"]},
            "75pt Arial": {"size": 100, "family": ["Arial"]},
            "20% Arial": {"size": 16 * 0.2, "family": ["Arial"]},
            "20mm Arial": {"size": 75.59055118110237, "family": ["Arial"]},
            "20px serif": {"size": 20, "family": ["serif"]},
            "20px sans-serif": {"size": 20, "family": ["sans-serif"]},
            "20px monospace": {"size": 20, "family": ["monospace"]},
            "50px Arial, sans-serif": {"size": 50, "family": ["Arial", "sans-serif"]},
            "bold italic 50px Arial, sans-serif": {
                "style": "italic",
                "weight": 700,
                "size": 50,
                "family": ["Arial", "sans-serif"],
            },
            "50px Helvetica ,  Arial, sans-serif": {
                "size": 50,
                "family": ["Helvetica", "Arial", "sans-serif"],
            },
            '50px "Helvetica Neue", sans-serif': {
                "size": 50,
                "family": ["Helvetica Neue", "sans-serif"],
            },
            '50px "Helvetica Neue", "foo bar baz" , sans-serif': {
                "size": 50,
                "family": ["Helvetica Neue", "foo bar baz", "sans-serif"],
            },
            "50px 'Helvetica Neue'": {"size": 50, "family": ["Helvetica Neue"]},
            "italic 20px Arial": {"size": 20, "style": "italic", "family": ["Arial"]},
            "oblique 20px Arial": {"size": 20, "style": "oblique", "family": ["Arial"]},
            "normal 20px Arial": {"size": 20, "style": "normal", "family": ["Arial"]},
            "300 20px Arial": {"size": 20, "weight": 300, "family": ["Arial"]},
            "800 20px Arial": {"size": 20, "weight": 800, "family": ["Arial"]},
            "bolder 20px Arial": {"size": 20, "weight": 800, "family": ["Arial"]},
            "lighter 20px Arial": {"size": 20, "weight": 300, "family": ["Arial"]},
            "normal normal normal 16px Impact": {
                "size": 16,
                "weight": 400,
                "family": ["Impact"],
                "style": "normal",
                "variant": "normal",
            },
            "italic small-caps bolder 16px cursive": {
                "size": 16,
                "style": "italic",
                "variant": "small-caps",
                "weight": 800,
                "family": ["cursive"],
            },
            '20px "new century schoolbook", serif': {
                "size": 20,
                "family": ["new century schoolbook", "serif"],
            },
            '20px "Arial bold 300"': {
                "size": 20,
                "family": ["Arial bold 300"],
                "variant": "normal",
            },  # synthetic case with weight keyword inside family
        }
        for font, spec in cases.items():
            expected = {
                "style": "normal",
                "stretch": "normal",
                "variant": "normal",
                **spec,
            }
            parsed = css.font(font)
            assert parsed is not None
            got = dataclasses.asdict(parsed)
            for k, v in expected.items():
                assert k in got
                assert got[k] == v

    def test_colors(self, canvas_ctx):
        _, ctx = canvas_ctx
        ctx.fillStyle = "#ffccaa"
        assert ctx.fillStyle == "#ffccaa"

        ctx.fillStyle = "#FFCCAA"
        assert ctx.fillStyle == "#ffccaa"

        ctx.fillStyle = "#FCA"
        assert ctx.fillStyle == "#ffccaa"

        ctx.fillStyle = "#0ff"
        ctx.fillStyle = "#FGG"
        assert ctx.fillStyle == "#00ffff"

        ctx.fillStyle = "#fff"
        ctx.fillStyle = "afasdfasdf"
        assert ctx.fillStyle == "#ffffff"

        # #rgba and #rrggbbaa

        ctx.fillStyle = "#ffccaa80"
        assert ctx.fillStyle == "rgba(255, 204, 170, 0.502)"

        ctx.fillStyle = "#acf8"
        assert ctx.fillStyle == "rgba(170, 204, 255, 0.533)"

        ctx.fillStyle = "#BEAD"
        assert ctx.fillStyle == "rgba(187, 238, 170, 0.867)"

        ctx.fillStyle = "rgb(255,255,255)"
        assert ctx.fillStyle == "#ffffff"

        ctx.fillStyle = "rgb(0,0,0)"
        assert ctx.fillStyle == "#000000"

        ctx.fillStyle = "rgb( 0  ,   0  ,  0)"
        assert ctx.fillStyle == "#000000"

        ctx.fillStyle = "rgba( 0  ,   0  ,  0, 1)"
        assert ctx.fillStyle == "#000000"

        ctx.fillStyle = "rgba( 255, 200, 90, 0.5)"
        assert ctx.fillStyle == "rgba(255, 200, 90, 0.502)"

        ctx.fillStyle = "rgba( 255, 200, 90, 0.75)"
        assert ctx.fillStyle == "rgba(255, 200, 90, 0.749)"

        ctx.fillStyle = "rgba( 255, 200, 90, 0.7555)"
        assert ctx.fillStyle == "rgba(255, 200, 90, 0.757)"

        ctx.fillStyle = "rgba( 255, 200, 90, .7555)"
        assert ctx.fillStyle == "rgba(255, 200, 90, 0.757)"

        ctx.fillStyle = "rgb(0, 0, 9000)"
        assert ctx.fillStyle == "#0000ff"

        ctx.fillStyle = "rgba(0, 0, 0, 42.42)"
        assert ctx.fillStyle == "#000000"

        # hsl / hsla tests

        ctx.fillStyle = "hsl(0, 0%, 0%)"
        assert ctx.fillStyle == "#000000"

        ctx.fillStyle = "hsl(3600, -10%, -10%)"
        assert ctx.fillStyle == "#000000"

        ctx.fillStyle = "hsl(10, 100%, 42%)"
        assert ctx.fillStyle == "#d62400"

        ctx.fillStyle = "hsl(370, 120%, 42%)"
        assert ctx.fillStyle == "#d62400"

        ctx.fillStyle = "hsl(0, 100%, 100%)"
        assert ctx.fillStyle == "#ffffff"

        ctx.fillStyle = "hsl(0, 150%, 150%)"
        assert ctx.fillStyle == "#ffffff"

        ctx.fillStyle = "hsl(237, 76%, 25%)"
        assert ctx.fillStyle == "#0f1470"

        ctx.fillStyle = "hsl(240, 73%, 25%)"
        assert ctx.fillStyle == "#11116e"

        ctx.fillStyle = "hsl(262, 32%, 42%)"
        assert ctx.fillStyle == "#62498d"

        ctx.fillStyle = "hsla(0, 0%, 0%, 1)"
        assert ctx.fillStyle == "#000000"

        ctx.fillStyle = "hsla(0, 100%, 100%, 1)"
        assert ctx.fillStyle == "#ffffff"

        ctx.fillStyle = "hsla(120, 25%, 75%, 0.5)"
        assert ctx.fillStyle == "rgba(175, 207, 175, 0.502)"

        ctx.fillStyle = "hsla(240, 75%, 25%, 0.75)"
        assert ctx.fillStyle == "rgba(16, 16, 112, 0.749)"

        ctx.fillStyle = "hsla(172.0, 33.00000e0%, 42%, 1)"
        assert ctx.fillStyle == "#488e85"

        ctx.fillStyle = "hsl(124.5, 76.1%, 47.6%)"
        assert ctx.fillStyle == "#1dd62b"

        ctx.fillStyle = "hsl(1.24e2, 760e-1%, 4.7e1%)"
        assert ctx.fillStyle == "#1dd329"

        # case-insensitive css names

        ctx.fillStyle = "sILveR"
        assert ctx.fillStyle == "#c0c0c0"

        # wrong type args

        transparent = "rgba(0, 0, 0, 0)"
        ctx.fillStyle = "transparent"
        assert ctx.fillStyle == transparent

        ctx.fillStyle = None
        assert ctx.fillStyle == transparent

        ctx.fillStyle = float("nan")
        assert ctx.fillStyle == transparent

        ctx.fillStyle = [None, 255, False]
        assert ctx.fillStyle == transparent

        ctx.fillStyle = True
        assert ctx.fillStyle == transparent

        ctx.fillStyle = {}
        assert ctx.fillStyle == transparent


class TestValidation:
    def before_each(self, ctx: CanvasRenderingContext2D):
        self.g = ctx.createLinearGradient(0, 0, 10, 10)
        self.id = ctx.getImageData(0, 0, 10, 10)
        self.img = load_asset("checkers.png")
        self.p2d = Path2D()
        self.p2d.rect(0, 0, 100, 100)
        ctx.rect(0, 0, 100, 100)

    def test_not_enough_arguments(self, canvas_ctx):
        canvas, ctx = canvas_ctx
        self.before_each(ctx)
        img = self.img
        g = self.g

        calls = [
            lambda: ctx.transform(),
            lambda: ctx.transform(0, 0, 0, 0, 0),
            lambda: ctx.setTransform(0, 0, 0, 0, 0),
            lambda: ctx.translate(0),
            lambda: ctx.scale(0),
            lambda: ctx.rotate(),
            lambda: ctx.rect(0, 0, 0),
            lambda: ctx.arc(0, 0, 0, 0),
            lambda: ctx.arcTo(0, 0, 0, 0),
            lambda: ctx.ellipse(0, 0, 0, 0, 0, 0),
            lambda: ctx.moveTo(0),
            lambda: ctx.lineTo(0),
            lambda: ctx.bezierCurveTo(0, 0, 0, 0, 0),
            lambda: ctx.quadraticCurveTo(0, 0, 0),
            lambda: ctx.conicCurveTo(0, 0, 0, 0),
            lambda: ctx.roundRect(0, 0, 0),
            lambda: ctx.fillRect(0, 0, 0),
            lambda: ctx.strokeRect(0, 0, 0),
            lambda: ctx.clearRect(0, 0, 0),
            lambda: ctx.fillText("text", 0),
            lambda: ctx.isPointInPath(10),
            lambda: ctx.isPointInStroke(10),
            lambda: ctx.createLinearGradient(0, 0, 1),
            lambda: ctx.createRadialGradient(0, 0, 0, 0, 0),
            lambda: ctx.createConicGradient(0, 0),
            lambda: ctx.setLineDash(),
            lambda: ctx.createImageData(),
            lambda: ctx.createPattern(img),
            lambda: ctx.createTexture(),
            lambda: ctx.getImageData(1, 1, 10),
            lambda: ctx.putImageData({}, 0),
            lambda: ctx.putImageData(id, 0, 0, 0, 0, 0),
            lambda: ctx.drawImage(img),
            lambda: ctx.drawImage(img, 0),
            lambda: ctx.drawImage(img, 0, 0, 0),
            lambda: ctx.drawImage(img, 0, 0, 0, 0, 0),
            lambda: ctx.drawImage(img, 0, 0, 0, 0, 0, 0),
            lambda: ctx.drawImage(img, 0, 0, 0, 0, 0, 0, 0),
            lambda: ctx.drawCanvas(canvas),
            lambda: ctx.drawCanvas(canvas, 0),
            lambda: ctx.drawCanvas(canvas, 0, 0, 0),
            lambda: ctx.drawCanvas(canvas, 0, 0, 0, 0, 0),
            lambda: ctx.drawCanvas(canvas, 0, 0, 0, 0, 0, 0),
            lambda: ctx.drawCanvas(canvas, 0, 0, 0, 0, 0, 0, 0),
            lambda: g.addColorStop(0),  # type: ignore
        ]
        for fn in calls:
            with pytest.raises((TypeError, ValueError)):
                fn()

    def test_value_errors(self, canvas_ctx):
        canvas, ctx = canvas_ctx
        self.before_each(ctx)
        p2d = self.p2d
        img = self.img
        g = self.g
        id = self.id

        calls = [
            (
                lambda: ctx.ellipse(0, 0, -10, -10, 0, 0, 0, False),
                "Radius value must be positive",
            ),
            (lambda: ctx.arcTo(0, 0, 0, 0, -10), "Radius value must be positive"),
            (
                lambda: ctx.roundRect(0, 0, 0, 0, -10),
                "Corner radius cannot be negative",
            ),
            (lambda: ctx.createImageData(1, 0), "Dimensions must be non-zero"),
            (lambda: ctx.getImageData(1, 1, math.nan, 10), "Expected a finite number"),
            (lambda: ctx.getImageData(1, math.nan, 10, 10), "Expected a finite number"),
            (lambda: ctx.createImageData(1, {}), "Expected a finite number"),
            (lambda: ctx.createImageData(1, math.nan), "Expected a finite number"),
            (lambda: ctx.putImageData(id, math.nan, 0), "Expected a finite number"),
            (
                lambda: ctx.putImageData(id, 0, 0, 0, 0, math.nan, 0),
                "Expected a finite number",
            ),
            (lambda: ctx.putImageData({}, 0, 0), "Expected an ImageData as 1st arg"),
            (lambda: ctx.drawImage(), None),
            (lambda: ctx.drawCanvas(), None),
            (
                lambda: ctx.fill(math.nan),
                "Expected a Path2D or a CanvasFillRule argument",
            ),
            (
                lambda: ctx.clip(math.nan),
                "Expected a Path2D or a CanvasFillRule argument",
            ),
            (lambda: ctx.stroke(math.nan), "Expected a Path2D"),
            (lambda: ctx.fill(math.nan, "evenodd"), "Expected a Path2D"),
            (lambda: ctx.clip(math.nan, "evenodd"), "Expected a Path2D"),
            (
                lambda: ctx.fill(p2d, {}),
                "Expected a CanvasFillRule as the second argument",
            ),
            (lambda: ctx.createTexture([1, math.nan]), "Expected a finite number"),
            # (lambda:ctx.createTexture(1, {"path":None}), "Expected a Path2D"),
            (
                lambda: ctx.createTexture(20, {"line": {}}),
                "argument 'line': must be real number, not dict",
            ),
            (
                lambda: ctx.createTexture(20, {"angle": {}}),
                "argument 'angle': must be real number, not dict",
            ),
            (
                lambda: ctx.createTexture(20, {"offset": {}}),
                "Expected a number or array",
            ),
            (
                lambda: ctx.createTexture(20, {"cap": {}}),
                "argument 'cap': 'dict' object is not an instance of 'str'",
            ),
            (lambda: ctx.createTexture(20, {"cap": ""}), 'Expected "butt", "square"'),
            (
                lambda: ctx.createTexture(20, {"offset": [1, math.nan]}),
                "Expected a finite number",
            ),
            (
                lambda: ctx.isPointInPath(0, 10, 10),
                "argument 'fill_rule': 'int' object is not an instance of 'str'",
            ),
            (
                lambda: ctx.isPointInPath(False, 10, 10),
                "argument 'fill_rule': 'int' object is not an instance of 'str'",
            ),
            (
                lambda: ctx.isPointInPath({}, 10, 10),
                "argument 'x': must be real number, not dict",
            ),
            (
                lambda: ctx.isPointInPath({}, 10, 10, "___"),
                "invalid arguments for isPointInPath",
            ),
            (
                lambda: ctx.isPointInPath({}, 10, 10, "evenodd"),
                "invalid arguments for isPointInPath",
            ),
            (lambda: ctx.isPointInPath(10, 10, "___"), "Invalid fill rule"),
            (lambda: ctx.isPointInPath(p2d, 10, 10, ""), "Invalid fill rule"),
            (
                lambda: ctx.createLinearGradient(0, 0, math.nan, 1),
                "Expected a finite number",
            ),
            (
                lambda: ctx.createRadialGradient(0, 0, math.nan, 0, 0, 0),
                "Expected a finite number",
            ),
            (
                lambda: ctx.createConicGradient(0, math.nan, 0),
                "Expected a finite number",
            ),
            (lambda: ctx.createPattern(img, "___"), "Invalid repetition mode"),
            (
                lambda: g.addColorStop(math.nan, "#000"),
                "Color stop offsets must be between 0.0 and 1.0",
            ),
            (lambda: g.addColorStop(0, {}), "argument 'color': 'dict' object is not an instance of 'str'"),  # type: ignore
            (
                lambda: ctx.setLineDash(math.nan),
                "argument 'segments': 'float' object is not an instance of 'Sequence'",
            ),
        ]

        for fn, msg in calls:
            with pytest.raises(Exception, match=msg):
                fn()
