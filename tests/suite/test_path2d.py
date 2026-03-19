from __future__ import annotations

import math

import pytest

from skia_canvas_pyr import Canvas, DOMMatrix, DOMPoint, Path2D

BLACK = (0, 0, 0, 255)
WHITE = (255, 255, 255, 255)
CLEAR = (0, 0, 0, 0)
TAU = math.tau
WIDTH = 512
HEIGHT = 512


def pixel(ctx, x: int | float, y: int | float) -> tuple[int, int, int, int]:
    data = ctx.getImageData(x, y, 1, 1).data
    return tuple(data[:4])


def scrub(ctx):
    ctx.clearRect(0, 0, WIDTH, HEIGHT)


def bounds_subset(path: Path2D, **expected):
    b = path.bounds
    for key, value in expected.items():
        assert getattr(b, key) == value


@pytest.fixture
def path_ctx():
    canvas = Canvas(WIDTH, HEIGHT)
    ctx = canvas.getContext("2d")
    ctx.lineWidth = 4
    p = Path2D()
    return canvas, ctx, p


def test_can_init_no_args():
    p = Path2D()
    p.rect(10, 10, 100, 100)


def test_can_init_with_path2d():
    p1 = Path2D()
    p1.rect(10, 10, 100, 100)
    p2 = Path2D(p1)
    bounds_subset(
        p2,
        left=p1.bounds.left,
        top=p1.bounds.top,
        right=p1.bounds.right,
        bottom=p1.bounds.bottom,
    )


def test_can_init_with_svg_string():
    p1 = Path2D()
    p1.rect(10, 10, 100, 100)
    p2 = Path2D("M 10,10 h 100 v 100 h -100 Z")
    bounds_subset(
        p2,
        left=p1.bounds.left,
        top=p1.bounds.top,
        right=p1.bounds.right,
        bottom=p1.bounds.bottom,
    )


def test_can_init_with_stream_of_edges(path_ctx):
    _, ctx, _ = path_ctx
    p = Path2D()

    p.moveTo(100, 100)
    p.lineTo(200, 100)
    p.lineTo(200, 200)
    p.lineTo(100, 200)
    p.closePath()
    p.moveTo(250, 200)
    p.arc(200, 200, 50, 0, TAU)
    p.moveTo(300, 100)
    p.bezierCurveTo(400, 100, 300, 200, 400, 200)
    p.moveTo(400, 220)
    p.quadraticCurveTo(400, 320, 300, 320)

    clone = Path2D()
    for edge in p.edges:
        verb, *pts = edge
        getattr(clone, str(verb))(*pts)

    ctx.fillStyle = "white"
    ctx.fillRect(0, 0, WIDTH, HEIGHT)

    ctx.lineWidth = 1
    ctx.stroke(p)
    pixels = ctx.getImageData(0, 0, WIDTH, HEIGHT).data
    assert not all(px == 255 for px in pixels)

    ctx.lineWidth = 4
    ctx.strokeStyle = "white"
    ctx.stroke(clone)
    pixels = ctx.getImageData(0, 0, WIDTH, HEIGHT).data
    assert all(px == 255 for px in pixels)


def test_move_to(path_ctx):
    _, _, p = path_ctx
    left, top = 20, 30
    p.moveTo(left, top)
    bounds_subset(p, left=left, top=top)
    with pytest.raises(TypeError):
        p.moveTo(120)  # type: ignore[arg-type]


def test_line_to(path_ctx):
    _, ctx, p = path_ctx
    left, top = 20, 30
    width, height = 37, 86
    p.moveTo(left, top)
    p.lineTo(left + width, top + height)
    ctx.stroke(p)
    bounds_subset(p, left=left, top=top, width=width, height=height)
    assert pixel(ctx, left + width / 2, top + height / 2) == BLACK
    with pytest.raises(TypeError):
        p.lineTo(120)  # type: ignore[arg-type]


def test_bezier_curve_to(path_ctx):
    _, ctx, p = path_ctx
    p.moveTo(20, 100)
    p.bezierCurveTo(120, -100, 120, 300, 220, 100)
    ctx.lineWidth = 6
    ctx.strokeStyle = "black"
    ctx.stroke(p)

    assert pixel(ctx, 71, 42) == BLACK
    assert pixel(ctx, 168, 157) == BLACK
    with pytest.raises(TypeError):
        p.bezierCurveTo(120, 300, 400, 400)  # type: ignore[arg-type]


def test_quadratic_curve_to(path_ctx):
    _, ctx, p = path_ctx
    p.moveTo(20, 100)
    p.quadraticCurveTo(120, 300, 220, 100)
    ctx.lineWidth = 6
    ctx.strokeStyle = "black"
    ctx.stroke(p)

    assert pixel(ctx, 120, 199) == BLACK
    with pytest.raises(TypeError):
        p.quadraticCurveTo(120, 300)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "weight, expected",
    [
        (0, (250, 400)),
        (1, (250, 225)),
        (10, (250, 81)),
        (100, (250, 54)),
        (1000, (250, 50)),
    ],
)
def test_conic_to(path_ctx, weight, expected):
    _, ctx, _ = path_ctx
    ctx.lineWidth = 5

    path = Path2D()
    path.moveTo(100, 400)
    path.conicCurveTo(250, 50, 400, 400, weight)

    ctx.stroke(path)
    assert pixel(ctx, *expected) == BLACK
    scrub(ctx)


def test_arc_to(path_ctx):
    _, ctx, p = path_ctx
    p.moveTo(100, 100)
    p.arcTo(150, 5, 200, 100, 25)
    p.lineTo(200, 100)
    p.moveTo(100, 100)
    p.arcTo(150, 200, 200, 100, 50)
    p.lineTo(200, 100)
    ctx.lineWidth = 6
    ctx.strokeStyle = "black"
    ctx.stroke(p)

    assert pixel(ctx, 150, 137) == BLACK
    assert pixel(ctx, 150, 33) == BLACK
    with pytest.raises(TypeError):
        p.arcTo(0, 0, 20, 20)  # type: ignore[arg-type]


def test_rect(path_ctx):
    _, ctx, p = path_ctx
    p.rect(50, 50, 100, 100)
    ctx.lineWidth = 6
    ctx.strokeStyle = "black"
    ctx.stroke(p)

    assert pixel(ctx, 150, 150) == BLACK
    with pytest.raises(TypeError):
        p.rect(0, 0, 20)  # type: ignore[arg-type]


def test_round_rect(path_ctx):
    _, ctx, p = path_ctx
    dim = WIDTH / 2
    radii = [50, 25, 15, DOMPoint(20, 10)]
    p.roundRect(dim, dim, dim, dim, radii)
    p.roundRect(dim, dim, -dim, -dim, radii)
    p.roundRect(dim, dim, -dim, dim, radii)
    p.roundRect(dim, dim, dim, -dim, radii)
    ctx.fill(p)

    off = [(3, 3), (dim - 14, dim - 14), (dim - 4, 3), (7, dim - 6)]
    on = [(5, 5), (dim - 17, dim - 17), (dim - 9, 3), (9, dim - 9)]

    for x, y in on:
        assert pixel(ctx, x, y) == BLACK
        assert pixel(ctx, x, HEIGHT - y - 1) == BLACK
        assert pixel(ctx, WIDTH - x - 1, y) == BLACK
        assert pixel(ctx, WIDTH - x - 1, HEIGHT - y - 1) == BLACK

    for x, y in off:
        assert pixel(ctx, x, y) == CLEAR
        assert pixel(ctx, x, HEIGHT - y - 1) == CLEAR
        assert pixel(ctx, WIDTH - x - 1, y) == CLEAR
        assert pixel(ctx, WIDTH - x - 1, HEIGHT - y - 1) == CLEAR


def test_arc(path_ctx):
    _, ctx, p = path_ctx
    p.arc(150, 150, 75, math.pi / 8, math.pi * 1.5, True)
    ctx.fillStyle = "black"
    ctx.fill(p)

    p = Path2D()
    p.arc(150, 150, 75, math.pi / 8, math.pi * 1.5, False)
    ctx.fillStyle = "white"
    ctx.fill(p)

    assert pixel(ctx, 196, 112) == BLACK
    assert pixel(ctx, 150, 150) == WHITE
    with pytest.raises(TypeError):
        p.arc(150, 150, 75, math.pi / 8)  # type: ignore[arg-type]


def test_ellipse(path_ctx):
    _, ctx, p = path_ctx
    p.ellipse(100, 100, 100, 50, 0.25 * math.pi, 0, 1.5 * math.pi)
    ctx.lineWidth = 5
    ctx.strokeStyle = "black"
    ctx.stroke(p)

    assert pixel(ctx, 127, 175) == BLACK
    assert pixel(ctx, 130, 60) == BLACK
    assert pixel(ctx, 163, 100) == CLEAR

    p2 = Path2D()
    p2.ellipse(100, 100, 100, 50, 0.25 * math.pi, 0, 1.5 * math.pi, True)
    ctx.clearRect(0, 0, WIDTH, HEIGHT)
    ctx.stroke(p2)

    assert pixel(ctx, 127, 175) == CLEAR
    assert pixel(ctx, 130, 60) == CLEAR
    assert pixel(ctx, 163, 100) == BLACK

    p.ellipse(100, 100, 100, 50, 0.25 * math.pi, -0.5 * math.pi, 1.5 * math.pi, False)
    ctx.lineWidth = 5
    ctx.strokeStyle = "black"
    ctx.stroke(p)

    assert pixel(ctx, 127, 175) == BLACK
    assert pixel(ctx, 130, 60) == BLACK
    assert pixel(ctx, 163, 100) == BLACK

    p.ellipse(100, 100, 100, 50, 0.25 * math.pi, -0.5 * math.pi, 1.5 * math.pi, True)
    ctx.lineWidth = 5
    ctx.strokeStyle = "black"
    ctx.stroke(p)

    assert pixel(ctx, 127, 175) == BLACK
    assert pixel(ctx, 130, 60) == BLACK
    assert pixel(ctx, 163, 100) == BLACK


def test_append_other_paths(path_ctx):
    _, _, _ = path_ctx
    left = Path2D()
    right = Path2D()
    left.moveTo(20, 20)
    left.lineTo(100, 100)
    bounds_subset(left, left=20, top=20, right=100, bottom=100)

    right.moveTo(200, 20)
    right.lineTo(200, 200)
    bounds_subset(right, left=200, top=20, right=200, bottom=200)

    left.addPath(right)
    bounds_subset(left, left=20, top=20, right=200, bottom=200)


def test_append_with_matrix(path_ctx):
    _, _, _ = path_ctx
    left = Path2D()
    left.moveTo(0, 0)
    left.lineTo(10, 10)
    bounds_subset(left, left=0, top=0, right=10, bottom=10)

    right = Path2D(left)
    bounds_subset(right, left=0, top=0, right=10, bottom=10)

    matrix = DOMMatrix().scale(10, 10)
    left.addPath(right, matrix)
    bounds_subset(left, left=0, top=0, right=100, bottom=100)


def test_append_to_closed_path(path_ctx):
    _, ctx, _ = path_ctx
    ctx.lineWidth = 5
    ctx.strokeStyle = "black"

    left = Path2D()
    left.arc(100, 100, 25, 0, 2 * math.pi)
    bounds_subset(left, left=75, top=75, right=125, bottom=125)

    right = Path2D()
    right.arc(200, 100, 25, 0, 2 * math.pi)
    bounds_subset(right, left=175, top=75, right=225, bottom=125)

    left.addPath(right)
    bounds_subset(left, left=75, top=75, right=225, bottom=125)

    ctx.stroke(left)
    assert pixel(ctx, 175, 100) == BLACK
    assert pixel(ctx, 150, 100) == CLEAR

    solo = Path2D()
    solo.arc(100, 250, 25, 0, 2 * math.pi)
    solo.arc(200, 250, 25, 0, 2 * math.pi)
    ctx.stroke(solo)
    assert pixel(ctx, 175, 250) == BLACK
    assert pixel(ctx, 150, 250) == BLACK


def test_append_self(path_ctx):
    _, ctx, _ = path_ctx
    p = Path2D()
    p.ellipse(150, 150, 75, 75, 0, math.pi, math.pi * 2, True)
    p.addPath(p, DOMMatrix().scale(2, 2))
    ctx.fillStyle = "black"
    ctx.fill(p)

    assert pixel(ctx, 150, 151) == BLACK
    assert pixel(ctx, 150, 223) == BLACK
    assert pixel(ctx, 300, 301) == BLACK
    assert pixel(ctx, 300, 448) == BLACK


@pytest.fixture
def combo(path_ctx):
    _, ctx, _ = path_ctx
    a = Path2D("M 10,50 h 100 v 20 h -100 Z")
    b = Path2D("M 50,10 h 20 v100 h -20 Z")
    ctx.fillStyle = "black"
    return ctx, a, b


def test_complement(combo):
    ctx, a, b = combo
    c = a.complement(b)
    ctx.fill(c)
    assert pixel(ctx, 60, 20) == BLACK
    assert pixel(ctx, 20, 60) == CLEAR
    assert pixel(ctx, 60, 60) == CLEAR
    assert pixel(ctx, 100, 60) == CLEAR
    assert pixel(ctx, 60, 100) == BLACK


def test_difference(combo):
    ctx, a, b = combo
    c = a.difference(b)
    ctx.fill(c)
    assert pixel(ctx, 60, 20) == CLEAR
    assert pixel(ctx, 20, 60) == BLACK
    assert pixel(ctx, 60, 60) == CLEAR
    assert pixel(ctx, 100, 60) == BLACK
    assert pixel(ctx, 60, 100) == CLEAR


def test_intersect(combo):
    ctx, a, b = combo
    c = a.intersect(b)
    ctx.fill(c)
    assert pixel(ctx, 60, 20) == CLEAR
    assert pixel(ctx, 20, 60) == CLEAR
    assert pixel(ctx, 60, 60) == BLACK
    assert pixel(ctx, 100, 60) == CLEAR
    assert pixel(ctx, 60, 100) == CLEAR


def test_union(combo):
    ctx, a, b = combo
    c = a.union(b)
    ctx.fill(c)
    assert pixel(ctx, 60, 20) == BLACK
    assert pixel(ctx, 20, 60) == BLACK
    assert pixel(ctx, 60, 60) == BLACK
    assert pixel(ctx, 100, 60) == BLACK
    assert pixel(ctx, 60, 100) == BLACK


def test_xor(combo):
    ctx, a, b = combo
    c = a.xor(b)
    ctx.fill(c, "evenodd")
    assert pixel(ctx, 60, 20) == BLACK
    assert pixel(ctx, 20, 60) == BLACK
    assert pixel(ctx, 60, 60) == CLEAR
    assert pixel(ctx, 100, 60) == BLACK
    assert pixel(ctx, 60, 100) == BLACK

    ctx.fill(c, "nonzero")
    assert pixel(ctx, 60, 60) == BLACK


def test_simplify(combo):
    ctx, a, b = combo
    c = a.xor(b)
    ctx.fill(c.simplify("evenodd"))
    assert pixel(ctx, 60, 20) == BLACK
    assert pixel(ctx, 20, 60) == BLACK
    assert pixel(ctx, 60, 60) == CLEAR
    assert pixel(ctx, 100, 60) == BLACK
    assert pixel(ctx, 60, 100) == BLACK

    ctx.fill(c.simplify())
    assert pixel(ctx, 60, 60) == BLACK


def test_unwind(path_ctx):
    _, ctx, _ = path_ctx
    d = Path2D()
    d.rect(0, 0, 30, 30)
    d.rect(10, 10, 10, 10)
    ctx.fill(d.offset(50, 40))
    assert pixel(ctx, 65, 55) == BLACK
    ctx.fill(d.offset(100, 40), "evenodd")
    assert pixel(ctx, 115, 55) == CLEAR
    ctx.fill(d.simplify().offset(150, 40), "evenodd")
    assert pixel(ctx, 165, 55) == BLACK
    ctx.fill(d.unwind().offset(200, 40))
    assert pixel(ctx, 215, 55) == CLEAR


def test_interpolate(path_ctx):
    _, ctx, _ = path_ctx
    start = Path2D()
    start.moveTo(100, 100)
    start.bezierCurveTo(100, 100, 100, 200, 100, 200)
    start.bezierCurveTo(100, 200, 100, 300, 100, 300)

    finish = Path2D()
    finish.moveTo(300, 100)
    finish.bezierCurveTo(400, 100, 300, 200, 400, 200)
    finish.bezierCurveTo(300, 200, 400, 300, 300, 300)

    ctx.lineWidth = 4

    ctx.stroke(start.interpolate(finish, 0))
    assert pixel(ctx, 100, 102) == BLACK
    assert pixel(ctx, 100, 200) == BLACK
    scrub(ctx)

    ctx.stroke(start.interpolate(finish, 0.25))
    assert pixel(ctx, 151, 101) == BLACK
    assert pixel(ctx, 151, 200) == CLEAR
    assert pixel(ctx, 171, 200) == BLACK
    scrub(ctx)

    ctx.stroke(start.interpolate(finish, 0.5))
    assert pixel(ctx, 201, 101) == BLACK
    assert pixel(ctx, 201, 200) == CLEAR
    assert pixel(ctx, 243, 200) == BLACK
    scrub(ctx)

    ctx.stroke(start.interpolate(finish, 0.75))
    assert pixel(ctx, 251, 101) == BLACK
    assert pixel(ctx, 251, 200) == CLEAR
    assert pixel(ctx, 322, 200) == BLACK
    scrub(ctx)

    ctx.stroke(start.interpolate(finish, 1))
    assert pixel(ctx, 301, 101) == BLACK
    assert pixel(ctx, 301, 200) == CLEAR
    assert pixel(ctx, 395, 200) == BLACK
    scrub(ctx)

    ctx.stroke(start.interpolate(finish, 1.25))
    assert pixel(ctx, 351, 101) == BLACK
    assert pixel(ctx, 351, 200) == CLEAR
    assert pixel(ctx, 470, 200) == BLACK
    scrub(ctx)


def test_jitter(path_ctx):
    _, ctx, _ = path_ctx
    ys = range(101, 200)

    line = Path2D()
    line.moveTo(100, 100)
    line.lineTo(100, 200)

    ctx.lineWidth = 4
    ctx.stroke(line)
    all_black = [pixel(ctx, 100, y) == BLACK for y in ys]
    assert all(all_black)
    scrub(ctx)

    zag = line.jitter(10, 20)
    ctx.stroke(zag)
    not_all_black = [pixel(ctx, 100, y) == BLACK for y in ys]
    assert False in not_all_black
    assert True in not_all_black


def test_round(path_ctx):
    canvas, ctx, _ = path_ctx

    alpha = lambda: pixel(ctx, 50, 220)
    omega = lambda: pixel(ctx, 300, 30)

    top_left = lambda: pixel(ctx, 100, 30)
    top_right = lambda: pixel(ctx, 200, 30)
    bot_left = lambda: pixel(ctx, 150, 220)
    bot_right = lambda: pixel(ctx, 250, 220)

    hi_left = lambda: pixel(ctx, 100, 64)
    hi_right = lambda: pixel(ctx, 200, 64)
    lo_left = lambda: pixel(ctx, 150, 186)
    lo_right = lambda: pixel(ctx, 250, 186)

    lines = Path2D()
    lines.moveTo(50, 225)
    lines.lineTo(100, 25)
    lines.lineTo(150, 225)
    lines.lineTo(200, 25)
    lines.lineTo(250, 225)
    lines.lineTo(300, 25)

    ctx.lineWidth = 10
    ctx.stroke(lines)
    assert alpha() == BLACK
    assert omega() == BLACK

    assert top_left() == BLACK
    assert top_right() == BLACK
    assert bot_left() == BLACK
    assert bot_right() == BLACK

    assert hi_left() == CLEAR
    assert hi_right() == CLEAR
    assert lo_left() == CLEAR
    assert lo_right() == CLEAR

    rounded = lines.round(80)
    canvas.width = WIDTH
    ctx.lineWidth = 10
    ctx.stroke(rounded)
    assert alpha() == BLACK
    assert omega() == BLACK

    assert top_left() == CLEAR
    assert top_right() == CLEAR
    assert bot_left() == CLEAR
    assert bot_right() == CLEAR

    assert hi_left() == BLACK
    assert hi_right() == BLACK
    assert lo_left() == BLACK
    assert lo_right() == BLACK


def test_offset(path_ctx):
    _, _, _ = path_ctx
    orig = Path2D()
    orig.rect(10, 10, 40, 40)
    bounds_subset(orig, left=10, top=10, right=50, bottom=50)

    shifted = orig.offset(-10, -10)
    bounds_subset(shifted, left=0, top=0, right=40, bottom=40)

    shifted = shifted.offset(-40, -40)
    bounds_subset(shifted, left=-40, top=-40, right=0, bottom=0)

    bounds_subset(orig, left=10, top=10, right=50, bottom=50)


def test_transform(path_ctx):
    _, _, _ = path_ctx
    orig = Path2D()
    orig.rect(-10, -10, 20, 20)
    bounds_subset(orig, left=-10, top=-10, right=10, bottom=10)

    shifted = orig.transform(DOMMatrix().translate(10, 10))
    bounds_subset(shifted, left=0, top=0, right=20, bottom=20)

    shifted_by_hand = orig.transform(1, 0, 0, 1, 10, 10)
    assert shifted.edges == shifted_by_hand.edges

    embiggened = orig.transform(DOMMatrix().scale(2, 0.5))
    assert embiggened.bounds.left < orig.bounds.left
    assert embiggened.bounds.right > orig.bounds.right

    bounds_subset(orig, left=-10, top=-10, right=10, bottom=10)


def test_trim(path_ctx):
    _, ctx, _ = path_ctx
    left = lambda: pixel(ctx, 64, 137)
    mid = lambda: pixel(ctx, 200, 50)
    right = lambda: pixel(ctx, 336, 137)

    orig = Path2D()
    orig.arc(200, 200, 150, math.pi, 0)

    middle = orig.trim(0.25, 0.75)
    endpoints = orig.trim(0.25, 0.75, True)
    start = orig.trim(0.25)
    end = orig.trim(-0.25)
    none = orig.trim(0.75, 0.25)
    everything_and_more = orig.trim(-12345, 98765)

    ctx.lineWidth = 10
    ctx.stroke(orig)
    assert left() == BLACK
    assert mid() == BLACK
    assert right() == BLACK
    scrub(ctx)

    ctx.stroke(middle)
    assert left() == CLEAR
    assert mid() == BLACK
    assert right() == CLEAR
    scrub(ctx)

    ctx.stroke(endpoints)
    assert left() == BLACK
    assert mid() == CLEAR
    assert right() == BLACK
    scrub(ctx)

    ctx.stroke(start)
    assert left() == BLACK
    assert mid() == CLEAR
    assert right() == CLEAR
    scrub(ctx)

    ctx.stroke(end)
    assert left() == CLEAR
    assert mid() == CLEAR
    assert right() == BLACK
    scrub(ctx)

    ctx.stroke(none)
    assert left() == CLEAR
    assert mid() == CLEAR
    assert right() == CLEAR
    scrub(ctx)

    ctx.stroke(everything_and_more)
    assert left() == BLACK
    assert mid() == BLACK
    assert right() == BLACK
    scrub(ctx)


def test_validates_not_enough_arguments(path_ctx):
    _, _, p = path_ctx
    with pytest.raises(TypeError):
        p.transform()  # type: ignore[call-arg]
    with pytest.raises(TypeError):
        p.transform(0, 0, 0, 0, 0)  # type: ignore[call-arg]
    with pytest.raises(TypeError):
        p.rect(0, 0, 0)  # type: ignore[call-arg]
    with pytest.raises(TypeError):
        p.roundRect(0, 0, 0)  # type: ignore[call-arg]
    with pytest.raises(TypeError):
        p.arc(0, 0, 0, 0)  # type: ignore[call-arg]
    with pytest.raises(TypeError):
        p.arcTo(0, 0, 0, 0)  # type: ignore[call-arg]
    with pytest.raises(TypeError):
        p.ellipse(0, 0, 0, 0, 0, 0)  # type: ignore[call-arg]
    with pytest.raises(TypeError):
        p.moveTo(0)  # type: ignore[call-arg]
    with pytest.raises(TypeError):
        p.lineTo(0)  # type: ignore[call-arg]
    with pytest.raises(TypeError):
        p.bezierCurveTo(0, 0, 0, 0, 0)  # type: ignore[call-arg]
    with pytest.raises(TypeError):
        p.quadraticCurveTo(0, 0, 0)  # type: ignore[call-arg]
    with pytest.raises(TypeError):
        p.conicCurveTo(0, 0, 0, 0)  # type: ignore[call-arg]
    with pytest.raises(TypeError):
        p.complement()  # type: ignore[call-arg]
    with pytest.raises(TypeError):
        p.interpolate()  # type: ignore[call-arg]
    with pytest.raises(TypeError):
        p.offset(0)  # type: ignore[call-arg]
    with pytest.raises(TypeError):
        p.round()  # type: ignore[call-arg]
    with pytest.raises(TypeError):
        p.contains(0)  # type: ignore[call-arg]
    with pytest.raises(TypeError):
        p.addPath()  # type: ignore[call-arg]


def test_validates_value_errors(path_ctx):
    _, _, p = path_ctx
    with pytest.raises((TypeError, ValueError)):
        p.transform(0, 0, 0, math.nan, 0, 0)
    with pytest.raises((TypeError, ValueError)):
        p.complement({})  # type: ignore[arg-type]
    with pytest.raises((TypeError, ValueError)):
        p.interpolate(p, "foo")  # type: ignore[arg-type]
    with pytest.raises((TypeError, ValueError)):
        p.roundRect(0, 0, 0, 0, -10)
    with pytest.raises((TypeError, ValueError)):
        p.addPath(p, [])  # type: ignore[arg-type]


def test_validates_nan_arguments(path_ctx):
    _, _, p = path_ctx
    p.rect(0, 0, math.nan, 0)
    p.arc(0, 0, math.nan, 0, 0)
    p.arc(0, 0, math.nan, 0, 0, False)
    p.ellipse(0, 0, 0, math.nan, 0, 0, 0)
    p.moveTo(math.nan, 0)
    p.lineTo(math.nan, 0)
    p.arcTo(0, 0, 0, 0, math.nan)
    p.bezierCurveTo(0, 0, 0, 0, math.nan, 0)
    p.quadraticCurveTo(0, 0, math.nan, 0)
    p.conicCurveTo(0, 0, math.nan, 0, 1)
    p.roundRect(0, 0, 0, 0, math.nan)
    p.transform({})
