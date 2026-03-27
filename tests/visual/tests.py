from __future__ import annotations

import base64
import math
import random
import re
import urllib.parse
from pathlib import Path

from skia_canvas_pyr import Canvas, DOMMatrix, Image

D2R = math.pi / 180.0

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"

tests = {}


class Error(Exception):
    pass


def encodeURIComponent(s: str) -> str:
    return urllib.parse.quote(s, safe="-_.!~*'()")


def register(name: str):
    def _wrap(fn):
        tests[name] = fn
        return fn

    return _wrap


def imageSrc(filename: str) -> str:
    return str(ASSETS_DIR / filename)


def frange(start, stop=None, step=1.0):
    """Float version of range."""
    if stop is None:
        stop = start
        start = 0.0
    x = float(start)
    while (step > 0 and x < stop) or (step < 0 and x > stop):
        yield x
        x += step


# region tests


@register("clearRect()")
def fn_clearRect__(ctx):
    ctx.fillRect(25, 25, 100, 100)
    ctx.clearRect(45, 45, 60, 60)
    ctx.fillRect(50, 50, 50, 50)


@register("strokeRect()")
def fn_strokeRect__(ctx):
    ctx.fillRect(25, 25, 100, 100)
    ctx.clearRect(45, 45, 60, 60)
    ctx.strokeRect(50, 50, 50, 50)


@register("fillRect()")
def fn_fillRect__(ctx):
    def render(level):
        ctx.fillStyle = getPointColour(122, 122)
        ctx.fillRect(0, 0, 240, 240)
        renderLevel(level, 81, 0)

    def renderLevel(minimumLevel, level, y):
        for x in range(math.ceil(243 / level)):
            drawBlock(x, y, level)
        for x in range(0, math.ceil(243 / level), 3):
            drawBlock(x, y + 1, level)
            drawBlock(x + 2, y + 1, level)
        for x in range(math.ceil(243 / level)):
            drawBlock(x, y + 2, level)
        y += 3
        if y >= 243 / level:
            y = 0
            level /= 3
        if level >= minimumLevel:
            renderLevel(minimumLevel, level, y)

    def drawBlock(x, y, level):
        ctx.fillStyle = getPointColour(
            x * level + (level - 1) / 2, y * level + (level - 1) / 2
        )

        ctx.fillRect(x * level, y * level, level, level)

    def getPointColour(x, y):
        x = x / 121.5 - 1
        y = -y / 121.5 + 1
        x2y2 = x * x + y * y

        if x2y2 > 1:
            return "#000"

        root = math.sqrt(1 - x2y2)
        x3d = x * 0.7071067812 + root / 2 - y / 2
        y3d = x * 0.7071067812 - root / 2 + y / 2
        z3d = 0.7071067812 * root + 0.7071067812 * y
        brightness = -x / 2 + root * 0.7071067812 + y / 2
        if brightness < 0:
            brightness = 0
        return f"rgb({round(brightness * 127.5 * (1 - y3d))},{round(brightness * 127.5 * (x3d + 1))},{round(brightness * 127.5 * (z3d + 1))})"

    render(1)


@register("lineTo()")
def fn_lineTo__(ctx):
    # Filled triangle
    ctx.beginPath()
    ctx.moveTo(25.5, 25)
    ctx.lineTo(105, 25)
    ctx.lineTo(25, 105)
    ctx.fill()

    # Stroked triangle
    ctx.beginPath()
    ctx.moveTo(125, 125)
    ctx.lineTo(125, 45)
    ctx.lineTo(45, 125)
    ctx.closePath()
    ctx.stroke()


@register("arc()")
def fn_arc__(ctx):
    ctx.beginPath()
    ctx.arc(75, 75, 50, 0, math.pi * 2, True)  # Outer circle
    ctx.moveTo(110, 75)
    ctx.arc(75, 75, 35, 0, math.pi, False)  # Mouth
    ctx.moveTo(65, 65)
    ctx.arc(60, 65, 5, 0, math.pi * 2, True)  # Left eye
    ctx.moveTo(95, 65)
    ctx.arc(90, 65, 5, 0, math.pi * 2, True)  # Right eye
    ctx.stroke()


@register("arc() 2")
def fn_arc___2(ctx):
    for i in range(4):
        for j in range(3):
            ctx.beginPath()
            x = 25 + j * 50  # x coordinate
            y = 25 + i * 50  # y coordinate
            radius = 20  # Arc radius
            startAngle = 0  # Starting point on circle
            endAngle = math.pi + (math.pi * j) / 2  # End point on circle
            anticlockwise = (i % 2) == 1  # clockwise or anticlockwise

            ctx.arc(x, y, radius, startAngle, endAngle, anticlockwise)

            if i > 1:
                ctx.fill()
            else:
                ctx.stroke()


@register("arc() 3")
def fn_arc___3(ctx):
    ctx.translate(100, 60)
    ctx.beginPath()
    ctx.moveTo(0, 100)
    ctx.lineTo(0, 0)
    ctx.arc(0, 0, 50, -math.pi * 1.2, math.pi * 0.2, False)
    ctx.lineWidth = 3
    ctx.strokeStyle = "darkgreen"
    ctx.stroke()


@register("arcTo()")
def fn_arcTo__(ctx):
    ctx.fillStyle = "#08C8EE"
    ctx.translate(-50, -50)
    ctx.moveTo(120, 100)
    ctx.lineTo(180, 100)
    ctx.arcTo(200, 100, 200, 120, 5)
    ctx.lineTo(200, 180)
    ctx.arcTo(200, 200, 180, 200, 20)
    ctx.lineTo(120, 200)
    ctx.arcTo(100, 200, 100, 180, 20)
    ctx.lineTo(100, 120)
    ctx.arcTo(100, 100, 120, 100, 20)
    ctx.fill()

    ctx.font = "bold 25px Arial"
    ctx.fillStyle = "#fff"
    ctx.fillText("skia", 125, 157)


@register("ellipse() 1")
def fn_ellipse___1(ctx):
    n = 8
    for i in range(n):
        ctx.beginPath()
        a = i * 2 * math.pi / n
        x = 100 + 50 * math.cos(a)
        y = 100 + 50 * math.sin(a)
        ctx.ellipse(x, y, 10, 15, a, 0, 2 * math.pi)
        ctx.stroke()


@register("ellipse() 2")
def fn_ellipse___2(ctx):
    n = 8
    for i in range(n):
        ctx.beginPath()
        a = i * 2 * math.pi / n
        x = 100 + 50 * math.cos(a)
        y = 100 + 50 * math.sin(a)
        ctx.ellipse(x, y, 10, 15, a, 0, a)
        ctx.stroke()


@register("ellipse() 3")
def fn_ellipse___3(ctx):
    n = 8
    for i in range(n):
        ctx.beginPath()
        a = i * 2 * math.pi / n
        x = 100 + 50 * math.cos(a)
        y = 100 + 50 * math.sin(a)
        ctx.ellipse(x, y, 10, 15, a, 0, a, True)
        ctx.stroke()


@register("ellipse() 4")
def fn_ellipse___4(ctx):
    n = 8
    for i in range(n):
        ctx.beginPath()
        a = i * 2 * math.pi / n
        x = 100 + 50 * math.cos(a)
        y = 100 + 50 * math.sin(a)
        ctx.ellipse(x, y, 10, 15, a, a, 0, True)
        ctx.stroke()


@register("ellipse() 5")
def fn_ellipse___5(ctx):
    ctx.translate(100, 50)
    ctx.beginPath()
    ctx.moveTo(-39, -33)
    ctx.ellipse(39, -23, 9, 9, 0, -math.pi / 2, 0, True)
    ctx.lineTo(49, 23)
    ctx.closePath()
    ctx.fillStyle = "#5a0e3e"
    ctx.fill()


@register("ellipse() full circle from offset angles CW")
def fn_ellipse___full_circle_from_offset_angles_CW(ctx):
    ctx.beginPath()
    ctx.ellipse(100, 100, 100, 50, 45 * D2R, -90 * D2R, 270 * D2R, False)
    ctx.lineWidth = 5
    ctx.strokeStyle = "black"
    ctx.stroke()


@register("ellipse() full circle from offset angles CCW")
def fn_ellipse___full_circle_from_offset_angles_CCW(ctx):
    ctx.beginPath()
    ctx.ellipse(100, 100, 100, 50, 45 * D2R, -90 * D2R, 270 * D2R, True)
    ctx.lineWidth = 5
    ctx.strokeStyle = "black"
    ctx.stroke()


@register("bezierCurveTo()")
def fn_bezierCurveTo__(ctx):
    ctx.beginPath()
    ctx.moveTo(75, 40)
    ctx.bezierCurveTo(75, 37, 70, 25, 50, 25)
    ctx.bezierCurveTo(20, 25, 20, 62.5, 20, 62.5)
    ctx.bezierCurveTo(20, 80, 40, 102, 75, 120)
    ctx.bezierCurveTo(110, 102, 130, 80, 130, 62.5)
    ctx.bezierCurveTo(130, 62.5, 130, 25, 100, 25)
    ctx.bezierCurveTo(85, 25, 75, 37, 75, 40)
    ctx.fill()


@register("quadraticCurveTo()")
def fn_quadraticCurveTo__(ctx):
    ctx.beginPath()
    ctx.moveTo(75, 25)
    ctx.quadraticCurveTo(25, 25, 25, 62.5)
    ctx.quadraticCurveTo(25, 100, 50, 100)
    ctx.quadraticCurveTo(50, 120, 30, 125)
    ctx.quadraticCurveTo(60, 120, 65, 100)
    ctx.quadraticCurveTo(125, 100, 125, 62.5)
    ctx.quadraticCurveTo(125, 25, 75, 25)
    ctx.stroke()


def drawPinwheel(ctx, scl=0.5, offset=0, len=100, cb=None):
    ctx.translate(100, 100)
    ctx.scale(scl, scl)
    sin = math.sin(math.pi / 6)
    cos = math.cos(math.pi / 6)
    for i in range(13):
        c = math.floor(240 / 12 * i)
        ctx.fillStyle = f"rgb({c},{c},{c})"
        ctx.fillRect(offset, offset, len, 10)
        if cb:
            cb(cos, sin, -sin, cos)
        else:
            ctx.transform(cos, sin, -sin, cos, 0, 0)


@register("transform()")
def fn_transform__(ctx):
    drawPinwheel(ctx)


@register("transform() with DOMMatrix")
def fn_transform___with_DOMMatrix(ctx):
    cb = lambda a, b, c, d: ctx.transform(DOMMatrix(a, b, c, d, 0, 0))
    drawPinwheel(ctx, scl=0.5, offset=0, len=100, cb=cb)


@register("transform() with matrix-like object")
def fn_transform___with_matrix_like_object(ctx):
    cb = lambda a, b, c, d: ctx.transform(
        {"a": a, "b": b, "c": c, "d": d, "e": 0, "f": 0}
    )
    drawPinwheel(ctx, scl=0.5, offset=0, len=100, cb=cb)


@register("rotate()")
def fn_rotate__(ctx):
    ctx.rotate(0.4)
    ctx.translate(30, 0)
    ctx.rect(0, 0, 50, 50)
    ctx.stroke()


@register("rotate() 2")
def fn_rotate___2(ctx):
    ctx.translate(75, 75)

    for i in range(1, 6):  # Loop through rings (from inside to out)
        ctx.save()
        ctx.fillStyle = f"rgb({51 * i},{255 - 51 * i},255)"

        for j in range(i * 6):  # draw individual dots
            ctx.rotate(math.pi * 2 / (i * 6))
            ctx.beginPath()
            ctx.arc(0, i * 12.5, 5, 0, math.pi * 2, True)
            ctx.fill()

        ctx.restore()


@register("translate()")
def fn_translate__(ctx):

    def drawSpirograph(ctx, R, r, O):
        x1 = R - O
        y1 = 0
        i = 1
        ctx.beginPath()
        ctx.moveTo(x1, y1)
        while True:
            if i > 20000:
                break
            x2 = (R + r) * math.cos(i * math.pi / 72) - (r + O) * math.cos(
                ((R + r) / r) * (i * math.pi / 72)
            )
            y2 = (R + r) * math.sin(i * math.pi / 72) - (r + O) * math.sin(
                ((R + r) / r) * (i * math.pi / 72)
            )
            ctx.lineTo(x2, y2)
            x1 = x2
            y1 = y2
            i += 1
            if not (x2 != R - O and y2 != 0):
                break
        ctx.stroke()

    ctx.fillRect(0, 0, 300, 300)
    for i in range(3):
        for j in range(3):
            ctx.save()
            ctx.strokeStyle = "#9CFF00"
            ctx.translate(50 + j * 100, 50 + i * 100)
            drawSpirograph(ctx, 20 * (j + 2) / (j + 1), -8 * (i + 3) / (i + 1), 10)
            ctx.restore()


@register("scale()")
def fn_scale__(ctx):

    def drawSpirograph(ctx, R, r, O):
        x1 = R - O
        y1 = 0
        i = 1
        ctx.beginPath()
        ctx.moveTo(x1, y1)
        while True:
            if i > 20000:
                break
            x2 = (R + r) * math.cos(i * math.pi / 72) - (r + O) * math.cos(
                ((R + r) / r) * (i * math.pi / 72)
            )
            y2 = (R + r) * math.sin(i * math.pi / 72) - (r + O) * math.sin(
                ((R + r) / r) * (i * math.pi / 72)
            )
            ctx.lineTo(x2, y2)
            x1 = x2
            y1 = y2
            i += 1
            if not (x2 != R - O and y2 != 0):
                break
        ctx.stroke()

    ctx.strokeStyle = "#fc0"
    ctx.lineWidth = 1.5
    ctx.fillRect(0, 0, 300, 300)

    # Uniform scaling
    ctx.save()
    ctx.translate(50, 50)
    drawSpirograph(ctx, 22, 6, 5)  # no scaling

    ctx.translate(100, 0)
    ctx.scale(0.75, 0.75)
    drawSpirograph(ctx, 22, 6, 5)

    ctx.translate(133.333, 0)
    ctx.scale(0.75, 0.75)
    drawSpirograph(ctx, 22, 6, 5)
    ctx.restore()

    # Non-uniform scaling (y direction)
    ctx.strokeStyle = "#0cf"
    ctx.save()
    ctx.translate(50, 150)
    ctx.scale(1, 0.75)
    drawSpirograph(ctx, 22, 6, 5)

    ctx.translate(100, 0)
    ctx.scale(1, 0.75)
    drawSpirograph(ctx, 22, 6, 5)

    ctx.translate(100, 0)
    ctx.scale(1, 0.75)
    drawSpirograph(ctx, 22, 6, 5)
    ctx.restore()

    # Non-uniform scaling (x direction)
    ctx.strokeStyle = "#cf0"
    ctx.save()
    ctx.translate(50, 250)
    ctx.scale(0.75, 1)
    drawSpirograph(ctx, 22, 6, 5)

    ctx.translate(133.333, 0)
    ctx.scale(0.75, 1)
    drawSpirograph(ctx, 22, 6, 5)

    ctx.translate(177.777, 0)
    ctx.scale(0.75, 1)
    drawSpirograph(ctx, 22, 6, 5)
    ctx.restore()


@register("rect() 1")
def fn_rect___1(ctx):
    ctx.rect(5, 5, 50, 50)
    ctx.strokeStyle = "yellow"
    ctx.fill()
    ctx.stroke()


@register("rect() 2")
def fn_rect___2(ctx):
    ctx.translate(100, 50)
    ctx.rotate(math.pi * 0.25)
    ctx.beginPath()
    ctx.moveTo(0, 0)
    ctx.lineTo(0, 25)
    ctx.rect(25, 0, 25, 25)
    ctx.lineTo(75, 50)
    ctx.lineWidth = 3
    ctx.strokeStyle = "#333"
    ctx.stroke()


@register("clip()")
def fn_clip__(ctx):
    ctx.arc(50, 50, 50, 0, math.pi * 2, False)
    ctx.stroke()
    ctx.clip()
    ctx.fillStyle = "rgba(0,0,0,.5)"
    ctx.fillRect(0, 0, 100, 100)


@register("clip() 2")
def fn_clip___2(ctx):

    def drawStar(ctx, r):
        ctx.save()
        ctx.beginPath()
        ctx.moveTo(r, 0)
        for i in range(9):
            ctx.rotate(math.pi / 5)
            if (i % 2) == 0:
                ctx.lineTo((r / 0.525731) * 0.200811, 0)
            else:
                ctx.lineTo(r, 0)
        ctx.closePath()
        ctx.fill()
        ctx.restore()

    ctx.fillRect(0, 0, 150, 150)
    ctx.translate(75, 75)

    # Create a circular clipping path
    ctx.beginPath()
    ctx.arc(0, 0, 60, 0, math.pi * 2, True)
    ctx.clip()

    # draw background
    lingrad = ctx.createLinearGradient(0, -75, 0, 75)
    lingrad.addColorStop(0, "#232256")
    lingrad.addColorStop(1, "#143778")

    ctx.fillStyle = lingrad
    ctx.fillRect(-75, -75, 150, 150)

    # draw stars
    for j in range(1, 50):
        ctx.save()
        ctx.fillStyle = "#fff"
        ctx.translate(
            75 - math.floor(random.random() * 150),
            75 - math.floor(random.random() * 150),
        )
        drawStar(ctx, math.floor(random.random() * 4) + 2)
        ctx.restore()


@register("createPattern()")
def fn_createPattern__(ctx, done):
    img = Image()

    def img_onload():
        pattern = ctx.createPattern(img, "repeat")
        ctx.scale(0.1, 0.1)
        ctx.fillStyle = pattern
        ctx.fillRect(100, 100, 800, 800)
        ctx.strokeStyle = pattern
        ctx.lineWidth = 200
        ctx.strokeRect(1100, 1100, 800, 800)
        done()

    img.src = imageSrc("globe.jpg")
    img_onload()


@register("createPattern() with globalAlpha")
def fn_createPattern___with_globalAlpha(ctx, done):
    img = Image()

    def img_onload():
        pattern = ctx.createPattern(img, "repeat")
        ctx.scale(0.1, 0.1)
        ctx.globalAlpha = 0.6
        ctx.fillStyle = pattern
        ctx.fillRect(100, 100, 800, 800)
        ctx.globalAlpha = 0.2
        ctx.strokeStyle = pattern
        ctx.lineWidth = 200
        ctx.strokeRect(1100, 1100, 800, 800)
        done()

    img.src = imageSrc("globe.jpg")
    img_onload()


@register("createPattern() repeats")
def fn_createPattern___repeats(ctx, done):
    img = Image()

    def img_onload():
        ctx.scale(0.1, 0.1)
        ctx.strokeStyle = "black"
        ctx.lineWidth = 10
        ctx.fillStyle = ctx.createPattern(img, "no-repeat")
        ctx.fillRect(0, 0, 900, 900)
        ctx.strokeRect(0, 0, 900, 900)

        ctx.fillStyle = ctx.createPattern(img, "repeat-x")
        ctx.fillRect(1000, 0, 900, 900)
        ctx.strokeRect(1000, 0, 900, 900)

        ctx.fillStyle = ctx.createPattern(img, "repeat-y")
        ctx.fillRect(0, 1000, 900, 900)
        ctx.strokeRect(0, 1000, 900, 900)

        ctx.fillStyle = ctx.createPattern(img, "repeat")
        ctx.fillRect(1000, 1000, 900, 900)
        ctx.strokeRect(1000, 1000, 900, 900)
        done()

    img.src = imageSrc("globe.jpg")
    img_onload()


@register("createPattern() then setTransform and fill")
def fn_createPattern___then_setTransform_and_fill(ctx, done):
    img = Image()

    def img_onload():
        pattern = ctx.createPattern(img, "repeat")
        ctx.fillStyle = pattern
        ctx.scale(0.125, 0.125)

        ctx.fillRect(0, 0, 800, 800)

        pattern.setTransform(DOMMatrix().translate(100, 100))
        ctx.fillRect(0, 800, 800, 800)

        pattern.setTransform(DOMMatrix().rotate(45))
        ctx.fillRect(800, 0, 800, 800)

        pattern.setTransform(DOMMatrix().rotate(45).scale(4))
        ctx.fillRect(800, 800, 800, 800)
        done()

    img.src = imageSrc("quadrants.png")
    img_onload()


@register("createPattern() then setTransform and stroke")
def fn_createPattern___then_setTransform_and_stroke(ctx, done):
    img = Image()

    def img_onload():
        pattern = ctx.createPattern(img, "repeat")
        ctx.lineWidth = 150
        ctx.strokeStyle = pattern
        ctx.scale(0.125, 0.125)

        ctx.strokeRect(100, 100, 500, 500)

        pattern.setTransform(DOMMatrix().translate(100, 100))
        ctx.strokeRect(100, 900, 500, 500)

        pattern.setTransform(DOMMatrix().rotate(45))
        ctx.strokeRect(900, 100, 500, 500)

        pattern.setTransform(DOMMatrix().rotate(45).scale(4))
        ctx.strokeRect(900, 900, 500, 500)
        done()

    img.src = imageSrc("quadrants.png")
    img_onload()


@register("createPattern() then setTransform with no-repeat")
def fn_createPattern___then_setTransform_with_no_repeat(ctx, done):
    img = Image()

    def img_onload():
        pattern = ctx.createPattern(img, "no-repeat")
        ctx.fillStyle = pattern
        ctx.scale(0.125, 0.125)

        ctx.fillRect(0, 0, 800, 800)

        pattern.setTransform(DOMMatrix().translate(100, 900))
        ctx.fillRect(0, 800, 800, 800)

        pattern.setTransform(DOMMatrix().translate(800, 0).rotate(45))
        ctx.fillRect(800, 0, 800, 800)

        pattern.setTransform(DOMMatrix().translate(800, 800).rotate(45).scale(4))
        ctx.fillRect(800, 800, 800, 800)
        done()

    img.src = imageSrc("quadrants.png")
    img_onload()


@register("createLinearGradient()")
def fn_createLinearGradient__(ctx):
    lingrad = ctx.createLinearGradient(0, 0, 0, 150)
    lingrad.addColorStop(0, "#00ABEB")
    lingrad.addColorStop(0.5, "#fff")
    lingrad.addColorStop(0.5, "#26C000")
    lingrad.addColorStop(1, "#fff")

    lingrad2 = ctx.createLinearGradient(0, 50, 0, 95)
    lingrad2.addColorStop(0.5, "#000")
    lingrad2.addColorStop(1, "rgba(0,0,0,0)")

    ctx.fillStyle = lingrad
    ctx.strokeStyle = lingrad2

    ctx.fillRect(10, 10, 130, 130)
    ctx.strokeRect(50, 50, 50, 50)

    # Specifically test that setting the fillStyle to the current fillStyle works
    ctx.fillStyle = "#13b575"
    ctx.fillStyle = ctx.fillStyle  # eslint-disable-line no-self-assign
    ctx.fillRect(65, 65, 20, 20)

    lingrad3 = ctx.createLinearGradient(0, 0, 200, 0)
    lingrad3.addColorStop(0, "rgba(0,255,0,0.5)")
    lingrad3.addColorStop(0.33, "rgba(255,255,0,0.5)")
    lingrad3.addColorStop(0.66, "rgba(0,255,255,0.5)")
    lingrad3.addColorStop(1, "rgba(255,0,255,0.5)")
    ctx.fillStyle = lingrad3
    ctx.fillRect(0, 170, 200, 30)


@register("createLinearGradient() with opacity")
def fn_createLinearGradient___with_opacity(ctx):
    lingrad = ctx.createLinearGradient(0, 0, 0, 200)
    lingrad.addColorStop(0, "#00FF00")
    lingrad.addColorStop(0.33, "#FF0000")
    lingrad.addColorStop(0.66, "#0000FF")
    lingrad.addColorStop(1, "#00FFFF")
    ctx.fillStyle = lingrad
    ctx.strokeStyle = lingrad
    ctx.lineWidth = 10
    ctx.globalAlpha = 0.4
    ctx.strokeRect(5, 5, 190, 190)
    ctx.fillRect(0, 0, 50, 50)
    ctx.globalAlpha = 0.6
    ctx.strokeRect(35, 35, 130, 130)
    ctx.fillRect(50, 50, 50, 50)
    ctx.globalAlpha = 0.8
    ctx.strokeRect(65, 65, 70, 70)
    ctx.fillRect(100, 100, 50, 50)
    ctx.globalAlpha = 0.95
    ctx.fillRect(150, 150, 50, 50)


@register("createLinearGradient() and transforms")
def fn_createLinearGradient___and_transforms(ctx):
    lingrad = ctx.createLinearGradient(0, -100, 0, 100)
    lingrad.addColorStop(0, "#00FF00")
    lingrad.addColorStop(0.33, "#FF0000")
    lingrad.addColorStop(0.66, "#0000FF")
    lingrad.addColorStop(1, "#00FFFF")
    ctx.fillStyle = lingrad
    ctx.globalAlpha = 0.5
    ctx.translate(100, 100)
    ctx.beginPath()
    ctx.rect(-100, -100, 200, 200)
    ctx.rotate(math.pi / 2)
    ctx.scale(0.6, 0.6)
    ctx.fill()


@register("createRadialGradient()")
def fn_createRadialGradient__(ctx):
    # Create gradients
    radgrad = ctx.createRadialGradient(45, 45, 10, 52, 50, 30)
    radgrad.addColorStop(0, "#A7D30C")
    radgrad.addColorStop(0.9, "#019F62")
    radgrad.addColorStop(1, "rgba(1,159,98,0)")

    radgrad2 = ctx.createRadialGradient(105, 105, 20, 112, 120, 50)
    radgrad2.addColorStop(0, "#FF5F98")
    radgrad2.addColorStop(0.75, "#FF0188")
    radgrad2.addColorStop(1, "rgba(255,1,136,0)")

    radgrad3 = ctx.createRadialGradient(95, 15, 15, 102, 20, 40)
    radgrad3.addColorStop(0, "#00C9FF")
    radgrad3.addColorStop(0.8, "#00B5E2")
    radgrad3.addColorStop(1, "rgba(0,201,255,0)")

    radgrad4 = ctx.createRadialGradient(0, 150, 50, 0, 140, 90)
    radgrad4.addColorStop(0, "#F4F201")
    radgrad4.addColorStop(0.8, "#E4C700")
    radgrad4.addColorStop(1, "rgba(228,199,0,0)")

    # draw shapes
    ctx.fillStyle = radgrad4
    ctx.fillRect(0, 0, 150, 150)
    ctx.fillStyle = radgrad3
    ctx.fillRect(0, 0, 150, 150)
    ctx.fillStyle = radgrad2
    ctx.fillRect(0, 0, 150, 150)
    ctx.fillStyle = radgrad
    ctx.fillRect(0, 0, 150, 150)


@register("globalAlpha")
def fn_globalAlpha(ctx):
    ctx.globalAlpha = 0.5
    ctx.fillStyle = "rgba(0,0,0,0.5)"
    ctx.strokeRect(0, 0, 50, 50)

    ctx.globalAlpha = 0.8
    ctx.fillRect(20, 20, 20, 20)

    ctx.fillStyle = "black"
    ctx.globalAlpha = 1
    ctx.fillRect(25, 25, 10, 10)


@register("globalAlpha 2")
def fn_globalAlpha_2(ctx):
    ctx.fillStyle = "#FD0"
    ctx.fillRect(0, 0, 75, 75)
    ctx.fillStyle = "#6C0"
    ctx.fillRect(75, 0, 75, 75)
    ctx.fillStyle = "#09F"
    ctx.fillRect(0, 75, 75, 75)
    ctx.fillStyle = "#F30"
    ctx.fillRect(75, 75, 150, 150)
    ctx.fillStyle = "#FFF"

    ctx.globalAlpha = 0.2

    for i in range(7):
        ctx.beginPath()
        ctx.arc(75, 75, 10 + 10 * i, 0, math.pi * 2, True)
        ctx.fill()


@register("fillStyle")
def fn_fillStyle(ctx):
    for i in range(6):
        for j in range(6):
            ctx.fillStyle = (
                f"rgb({math.floor(255 - 42.5 * i)},{math.floor(255 - 42.5 * j)},0)"
            )
            ctx.fillRect(j * 25, i * 25, 25, 25)


@register("strokeStyle")
def fn_strokeStyle(ctx):
    for i in range(6):
        for j in range(6):
            ctx.strokeStyle = (
                f"rgb(0,{math.floor(255 - 42.5 * i)},{math.floor(255 - 42.5 * j)})"
            )
            ctx.beginPath()
            ctx.arc(12.5 + j * 25, 12.5 + i * 25, 10, 0, math.pi * 2, True)
            ctx.stroke()


@register("fill with stroke")
def fn_fill_with_stroke(ctx):
    ctx.beginPath()
    ctx.arc(75, 75, 50, 0, math.pi * 2, True)
    ctx.fill()
    ctx.closePath()
    ctx.beginPath()
    ctx.fillStyle = "red"
    ctx.strokeStyle = "yellow"
    ctx.arc(75, 75, 30, 0, math.pi * 2, True)
    ctx.fill()
    ctx.stroke()


@register("floating point coordinates")
def fn_floating_point_coordinates(ctx):
    ctx.lineCap = "square"
    for i in frange(0, 70, 3.05):
        ctx.rect(i + 3, 10.5, 0, 130)
        ctx.moveTo(i + 77, 10.5)
        ctx.lineTo(i + 77, 140.5)
    ctx.stroke()


@register("lineWidth")
def fn_lineWidth(ctx):
    for i in range(10):
        ctx.lineWidth = 1 + i
        ctx.beginPath()
        ctx.moveTo(5 + i * 14, 5)
        ctx.lineTo(5 + i * 14, 140)
        ctx.stroke()


@register("line caps")
def fn_line_caps(ctx):
    lineCap = ["butt", "round", "square"]

    ctx.strokeStyle = "#09f"
    ctx.beginPath()
    ctx.moveTo(10, 10)
    ctx.lineTo(140, 10)
    ctx.moveTo(10, 140)
    ctx.lineTo(140, 140)
    ctx.stroke()

    ctx.strokeStyle = "black"
    for i in range(len(lineCap)):
        ctx.lineWidth = 15
        ctx.lineCap = lineCap[i]
        ctx.beginPath()
        ctx.moveTo(25 + i * 50, 10)
        ctx.lineTo(25 + i * 50, 140)
        ctx.stroke()


@register("line join")
def fn_line_join(ctx):
    lineJoin = ["round", "bevel", "miter"]
    ctx.lineWidth = 10
    for i in range(len(lineJoin)):
        ctx.lineJoin = lineJoin[i]
        ctx.beginPath()
        ctx.moveTo(-5, 5 + i * 40)
        ctx.lineTo(35, 45 + i * 40)
        ctx.lineTo(75, 5 + i * 40)
        ctx.lineTo(115, 45 + i * 40)
        ctx.lineTo(155, 5 + i * 40)
        ctx.stroke()


@register("lineCap default")
def fn_lineCap_default(ctx):
    ctx.beginPath()
    ctx.lineWidth = 10.0
    ctx.moveTo(50, 50)
    ctx.lineTo(50, 100)
    ctx.lineTo(80, 120)
    ctx.stroke()


@register("lineCap")
def fn_lineCap(ctx):
    ctx.beginPath()
    ctx.lineWidth = 10.0
    ctx.lineCap = "round"
    ctx.moveTo(50, 50)
    ctx.lineTo(50, 100)
    ctx.lineTo(80, 120)
    ctx.stroke()


@register("lineJoin")
def fn_lineJoin(ctx):
    ctx.beginPath()
    ctx.lineWidth = 10.0
    ctx.lineJoin = "round"
    ctx.moveTo(50, 50)
    ctx.lineTo(50, 100)
    ctx.lineTo(80, 120)
    ctx.stroke()


@register("states")
def fn_states(ctx):
    ctx.save()
    ctx.rect(50, 50, 100, 100)
    ctx.stroke()

    ctx.restore()
    ctx.save()
    ctx.translate(50, 50)
    ctx.scale(0.5, 0.5)
    ctx.strokeRect(51, 51, 100, 100)

    ctx.restore()
    ctx.translate(95, 95)
    ctx.fillRect(0, 0, 10, 10)


@register("states with stroke/fill/globalAlpha")
def fn_states_with_stroke_fill_globalAlpha(ctx):
    ctx.fillRect(0, 0, 150, 150)
    ctx.save()

    ctx.fillStyle = "#09F"
    ctx.fillRect(15, 15, 120, 120)

    ctx.save()
    ctx.fillStyle = "#FFF"
    ctx.globalAlpha = 0.5
    ctx.fillRect(30, 30, 90, 90)

    ctx.restore()
    ctx.fillRect(45, 45, 60, 60)

    ctx.restore()
    ctx.fillRect(60, 60, 30, 30)


@register("path through fillRect/strokeRect/clearRect")
def fn_path_through_fillRect_strokeRect_clearRect(ctx):
    # left: fillRect()
    ctx.beginPath()
    ctx.rect(0, 50, 50, 50)
    ctx.fillStyle = "#F00"
    ctx.fillRect(10, 60, 30, 30)
    ctx.fillStyle = "#0F0"
    ctx.fill()

    # center: strokeRect()
    ctx.beginPath()
    ctx.rect(50, 50, 50, 50)
    ctx.strokeStyle = "#F00"
    ctx.lineWidth = 5
    ctx.strokeRect(60, 60, 30, 30)
    ctx.fillStyle = "#0F0"
    ctx.fill()

    # right: clearRect()
    ctx.beginPath()
    ctx.rect(100, 50, 50, 50)
    ctx.fillStyle = "#0F0"
    ctx.fill()
    ctx.clearRect(110, 60, 30, 30)
    ctx.fill()


@register("invalid stroke/fill styles")
def fn_invalid_stroke_fill_styles(ctx):
    ctx.fillStyle = "red"
    ctx.strokeStyle = "yellow"
    ctx.rect(50, 50, 50, 50)
    ctx.fill()
    ctx.stroke()
    ctx.beginPath()
    ctx.fillStyle = "asdf"
    ctx.strokeStyle = "asdf"
    ctx.rect(100, 80, 15, 15)
    ctx.fill()
    ctx.stroke()


@register("fillText()")
def fn_fillText__(ctx):
    ctx.font = "30px Arial"
    ctx.rotate(0.1)
    ctx.lineTo(10, 10)
    ctx.fillText("Awesome!", 50, 100)

    te = ctx.measureText("Awesome!")

    ctx.strokeStyle = "rgba(0,0,0,0.5)"
    ctx.lineTo(50, 102)
    ctx.lineTo(50 + te.width, 102)
    ctx.stroke()


@register("fillText() transformations")
def fn_fillText___transformations(ctx):
    ctx.strokeStyle = "#666"
    ctx.font = "bold 12px Helvetica"

    ctx.strokeRect(0, 0, 200, 200)
    ctx.lineTo(0, 100)
    ctx.lineTo(200, 100)
    ctx.stroke()

    ctx.beginPath()
    ctx.lineTo(100, 0)
    ctx.lineTo(100, 200)
    ctx.stroke()

    ctx.rotate(0.2)
    ctx.fillText("foo", 150, 100)
    ctx.font = "normal 30px Arial"
    ctx.fillText("bar", 50, 100)


@register("fillText() maxWidth argument")
def fn_fillText___maxWidth_argument(ctx):
    ctx.font = "Helvetica, sans"  # invalid font assignment
    ctx.fillText("Drawing text can be fun!", 0, 20)

    for i in range(1, 6):
        ctx.fillText("Drawing text can be fun!", 0, 20 * (7 - i), i * 20)

    ctx.fillText("Drawing text can be fun!", 0, 20 * 7)


@register("maxWidth bug first usage path")
def fn_maxWidth_bug_first_usage_path(ctx, done):
    # ctx.textDrawingMode = 'path'
    ctx.fillText("Drawing text can be fun!", 0, 20, 50)
    ctx.fillText("Drawing text can be fun!", 0, 40, 50)
    ctx.fillText("Drawing text can be fun changing text bug!", 0, 60, 50)
    done()


@register("maxWidth bug first usage glyph")
def fn_maxWidth_bug_first_usage_glyph(ctx, done):
    # ctx.textDrawingMode = 'glyph'
    ctx.fillText("Drawing text can be fun!", 0, 20, 50)
    ctx.fillText("Drawing text can be fun!", 0, 40, 50)
    ctx.fillText("Drawing text can be fun changing text bug!", 0, 60, 50)
    done()


@register("fillText() maxWidth argument + textAlign center (#1253)")
def fn_fillText___maxWidth_argument___textAlign_center___1253_(ctx):
    ctx.font = "Helvetica, sans"
    ctx.textAlign = "center"
    ctx.fillText("Drawing text can be fun!", 100, 20)

    for i in range(1, 6):
        ctx.fillText("Drawing text can be fun!", 100, 20 * (7 - i), i * 20)

    ctx.fillText("Drawing text can be fun!", 100, 20 * 7)


@register("fillText() maxWidth argument + textAlign right")
def fn_fillText___maxWidth_argument___textAlign_right(ctx):
    ctx.font = "Helvetica, sans"
    ctx.textAlign = "right"
    ctx.fillText("Drawing text can be fun!", 200, 20)

    for i in range(1, 6):
        ctx.fillText("Drawing text can be fun!", 200, 20 * (7 - i), i * 20)

    ctx.fillText("Drawing text can be fun!", 200, 20 * 7)


@register("strokeText()")
def fn_strokeText__(ctx):
    ctx.strokeStyle = "#666"
    ctx.strokeRect(0, 0, 200, 200)
    ctx.lineTo(0, 100)
    ctx.lineTo(200, 100)
    ctx.stroke()

    ctx.beginPath()
    ctx.lineTo(100, 0)
    ctx.lineTo(100, 200)
    ctx.stroke()

    ctx.strokeStyle = "red"
    ctx.font = "normal 50px Arial"
    ctx.strokeText("bar", 100, 100)


@register("strokeText() maxWidth argument")
def fn_strokeText___maxWidth_argument(ctx):
    ctx.font = "Helvetica, sans"
    ctx.strokeText("Drawing text can be fun!", 0, 20)

    for i in range(1, 6):
        ctx.strokeText("Drawing text can be fun!", 0, 20 * (7 - i), i * 20)

    ctx.strokeText("Drawing text can be fun!", 0, 20 * 7)


@register("textAlign right")
def fn_textAlign_right(ctx):
    ctx.strokeStyle = "#666"
    ctx.strokeRect(0, 0, 200, 200)
    ctx.lineTo(0, 100)
    ctx.lineTo(200, 100)
    ctx.stroke()

    ctx.beginPath()
    ctx.lineTo(100, 0)
    ctx.lineTo(100, 200)
    ctx.stroke()

    ctx.font = "normal 20px Arial"
    ctx.textAlign = "right"
    ctx.fillText("right", 100, 100)


@register("textAlign left")
def fn_textAlign_left(ctx):
    ctx.strokeStyle = "#666"
    ctx.strokeRect(0, 0, 200, 200)
    ctx.lineTo(0, 100)
    ctx.lineTo(200, 100)
    ctx.stroke()

    ctx.beginPath()
    ctx.lineTo(100, 0)
    ctx.lineTo(100, 200)
    ctx.stroke()

    ctx.font = "normal 20px Arial"
    ctx.textAlign = "left"
    ctx.fillText("left", 100, 100)


@register("textAlign center")
def fn_textAlign_center(ctx):
    ctx.strokeStyle = "#666"
    ctx.strokeRect(0, 0, 200, 200)
    ctx.lineTo(0, 100)
    ctx.lineTo(200, 100)
    ctx.stroke()

    ctx.beginPath()
    ctx.lineTo(100, 0)
    ctx.lineTo(100, 200)
    ctx.stroke()

    ctx.font = "normal 20px Arial"
    ctx.textAlign = "center"
    ctx.fillText("center", 100, 100)


@register("textBaseline alphabetic")
def fn_textBaseline_alphabetic(ctx):
    ctx.strokeStyle = "#666"
    ctx.strokeRect(0, 0, 200, 200)
    ctx.lineTo(0, 100)
    ctx.lineTo(200, 100)
    ctx.stroke()

    ctx.font = "normal 20px Arial"
    ctx.textBaseline = "alphabetic"
    ctx.textAlign = "center"
    ctx.fillText("alphabetic", 100, 100)


@register("textBaseline top")
def fn_textBaseline_top(ctx):
    ctx.strokeStyle = "#666"
    ctx.strokeRect(0, 0, 200, 200)
    ctx.lineTo(0, 100)
    ctx.lineTo(200, 100)
    ctx.stroke()

    ctx.font = "normal 20px Arial"
    ctx.textBaseline = "top"
    ctx.textAlign = "center"
    ctx.fillText("top", 100, 100)


@register("textBaseline hanging")
def fn_textBaseline_hanging(ctx):
    ctx.strokeStyle = "#666"
    ctx.strokeRect(0, 0, 200, 200)
    ctx.lineTo(0, 100)
    ctx.lineTo(200, 100)
    ctx.stroke()

    ctx.font = "normal 20px Arial"
    ctx.textBaseline = "hanging"
    ctx.textAlign = "center"
    ctx.fillText("hanging", 100, 100)


@register("textBaseline middle")
def fn_textBaseline_middle(ctx):
    ctx.strokeStyle = "#666"
    ctx.strokeRect(0, 0, 200, 200)
    ctx.lineTo(0, 100)
    ctx.lineTo(200, 100)
    ctx.stroke()

    ctx.font = "normal 20px Arial"
    ctx.textBaseline = "middle"
    ctx.textAlign = "center"
    ctx.fillText("middle", 100, 100)


@register("textBaseline ideographic")
def fn_textBaseline_ideographic(ctx):
    ctx.strokeStyle = "#666"
    ctx.strokeRect(0, 0, 200, 200)
    ctx.lineTo(0, 100)
    ctx.lineTo(200, 100)
    ctx.stroke()

    ctx.font = "normal 20px Arial"
    ctx.textBaseline = "ideographic"
    ctx.textAlign = "center"
    ctx.fillText("ideographic", 100, 100)


@register("textBaseline bottom")
def fn_textBaseline_bottom(ctx):
    ctx.strokeStyle = "#666"
    ctx.strokeRect(0, 0, 200, 200)
    ctx.lineTo(0, 100)
    ctx.lineTo(200, 100)
    ctx.stroke()

    ctx.font = "normal 20px Arial"
    ctx.textBaseline = "bottom"
    ctx.textAlign = "center"
    ctx.fillText("bottom", 100, 100)


@register("font size px")
def fn_font_size_px(ctx):
    ctx.strokeStyle = "#666"
    ctx.strokeRect(0, 0, 200, 200)
    ctx.lineTo(0, 100)
    ctx.lineTo(200, 100)
    ctx.stroke()

    ctx.font = "normal 14px Arial"
    ctx.textAlign = "center"
    ctx.fillText("normal 14px Arial", 100, 100)


@register("font size pt")
def fn_font_size_pt(ctx):
    ctx.strokeStyle = "#666"
    ctx.strokeRect(0, 0, 200, 200)
    ctx.lineTo(0, 100)
    ctx.lineTo(200, 100)
    ctx.stroke()

    ctx.font = "normal 14pt Arial"
    ctx.textAlign = "center"
    ctx.fillText("normal 14pt Arial", 100, 100)


@register("font size mm")
def fn_font_size_mm(ctx):
    ctx.strokeStyle = "#666"
    ctx.strokeRect(0, 0, 200, 200)
    ctx.lineTo(0, 100)
    ctx.lineTo(200, 100)
    ctx.stroke()

    ctx.font = "normal 3mm Arial"
    ctx.textAlign = "center"
    ctx.fillText("normal 3mm Arial", 100, 100)


@register("font size cm")
def fn_font_size_cm(ctx):
    ctx.strokeStyle = "#666"
    ctx.strokeRect(0, 0, 200, 200)
    ctx.lineTo(0, 100)
    ctx.lineTo(200, 100)
    ctx.stroke()

    ctx.font = "normal 0.6cm Arial"
    ctx.textAlign = "center"
    ctx.fillText("normal 0.6cm Arial", 100, 100)


@register("font weight bold")
def fn_font_weight_bold(ctx):
    ctx.strokeStyle = "#666"
    ctx.strokeRect(0, 0, 200, 200)
    ctx.lineTo(0, 100)
    ctx.lineTo(200, 100)
    ctx.stroke()

    ctx.font = "bold 14px Arial"
    ctx.textAlign = "center"
    ctx.fillText("bold 14px Arial", 100, 100)


@register("font weight lighter")
def fn_font_weight_lighter(ctx):
    ctx.strokeStyle = "#666"
    ctx.strokeRect(0, 0, 200, 200)
    ctx.lineTo(0, 100)
    ctx.lineTo(200, 100)
    ctx.stroke()

    ctx.font = "lighter 14px Arial"
    ctx.textAlign = "center"
    ctx.fillText("lighter 14px Arial", 100, 100)


@register("font weight lighter italic")
def fn_font_weight_lighter_italic(ctx):
    ctx.strokeStyle = "#666"
    ctx.strokeRect(0, 0, 200, 200)
    ctx.lineTo(0, 100)
    ctx.lineTo(200, 100)
    ctx.stroke()

    ctx.font = "lighter italic 14px Arial"
    ctx.textAlign = "center"
    ctx.fillText("lighter italic 14px Arial", 100, 100)


@register("font weight 200")
def fn_font_weight_200(ctx):
    ctx.strokeStyle = "#666"
    ctx.strokeRect(0, 0, 200, 200)
    ctx.lineTo(0, 100)
    ctx.lineTo(200, 100)
    ctx.stroke()

    ctx.font = "200 14px Arial"
    ctx.textAlign = "center"
    ctx.fillText("200 14px Arial", 100, 100)


@register("font weight 800")
def fn_font_weight_800(ctx):
    ctx.strokeStyle = "#666"
    ctx.strokeRect(0, 0, 200, 200)
    ctx.lineTo(0, 100)
    ctx.lineTo(200, 100)
    ctx.stroke()

    ctx.font = "800 14px Arial"
    ctx.textAlign = "center"
    ctx.fillText("800 14px Arial", 100, 100)


@register("font family serif")
def fn_font_family_serif(ctx):
    ctx.strokeStyle = "#666"
    ctx.strokeRect(0, 0, 200, 200)
    ctx.lineTo(0, 100)
    ctx.lineTo(200, 100)
    ctx.stroke()

    ctx.font = "14px serif"
    ctx.textAlign = "center"
    ctx.fillText("14px serif", 100, 100)


@register("font family sans-serif")
def fn_font_family_sans_serif(ctx):
    ctx.strokeStyle = "#666"
    ctx.strokeRect(0, 0, 200, 200)
    ctx.lineTo(0, 100)
    ctx.lineTo(200, 100)
    ctx.stroke()

    ctx.font = "14px sans-serif"
    ctx.textAlign = "center"
    ctx.fillText("14px sans-serif", 100, 100)


@register("font family Impact")
def fn_font_family_Impact(ctx):
    ctx.strokeStyle = "#666"
    ctx.strokeRect(0, 0, 200, 200)
    ctx.lineTo(0, 100)
    ctx.lineTo(200, 100)
    ctx.stroke()

    ctx.font = "18px Impact"
    ctx.textAlign = "center"
    ctx.fillText("18px Impact", 100, 100)


@register("font family invalid")
def fn_font_family_invalid(ctx):
    ctx.strokeStyle = "#666"
    ctx.strokeRect(0, 0, 200, 200)
    ctx.lineTo(0, 100)
    ctx.lineTo(200, 100)
    ctx.stroke()

    ctx.font = "14px Foo, Invalid, Impact, sans-serif"
    ctx.textAlign = "center"
    ctx.fillText("14px Invalid, Impact", 100, 100)


@register("font style variant weight size family")
def fn_font_style_variant_weight_size_family(ctx):
    ctx.strokeStyle = "#666"
    ctx.strokeRect(0, 0, 200, 200)
    ctx.lineTo(0, 100)
    ctx.lineTo(200, 100)
    ctx.stroke()

    ctx.font = "normal normal normal 16px Impact"
    ctx.textAlign = "center"
    ctx.fillText("normal normal normal 16px", 100, 100)


@register("generic font family monospace")
def fn_generic_font_family_monospace(ctx):
    ctx.strokeStyle = "#666"
    ctx.strokeRect(0, 0, 200, 200)
    ctx.lineTo(0, 100)
    ctx.lineTo(200, 100)
    ctx.stroke()

    ctx.font = '22px monospace, "Times New Roman", "Times", serif'
    ctx.textAlign = "center"
    ctx.fillText("monospace iWlx", 100, 100)


@register("generic font family fallback serif")
def fn_generic_font_family_fallback_serif(ctx):
    ctx.strokeStyle = "#666"
    ctx.strokeRect(0, 0, 200, 200)
    ctx.lineTo(0, 100)
    ctx.lineTo(200, 100)
    ctx.stroke()

    ctx.font = "24px None_suchFont, serif, Arial, monospace"
    ctx.textAlign = "center"
    ctx.fillText("serif fallback", 100, 100)


@register("generic font family fallback sans-serif")
def fn_generic_font_family_fallback_sans_serif(ctx):
    ctx.strokeStyle = "#666"
    ctx.strokeRect(0, 0, 200, 200)
    ctx.lineTo(0, 100)
    ctx.lineTo(200, 100)
    ctx.stroke()

    ctx.font = '24px None_suchFont, sans-serif, "Times New Roman", "Times", monospace'
    ctx.textAlign = "center"
    ctx.fillText("sans-serif fallback", 100, 100)


@register("generic font family fallback system-ui")
def fn_generic_font_family_fallback_system_ui(ctx):
    ctx.strokeStyle = "#666"
    ctx.strokeRect(0, 0, 200, 200)
    ctx.lineTo(0, 100)
    ctx.lineTo(200, 100)
    ctx.stroke()

    ctx.font = '24px None_suchFont, system-ui, "Times New Roman", "Times", serif'
    ctx.textAlign = "center"
    ctx.fillText("system-ui fallback", 100, 100)


# From https://developer.mozilla.org/en-US/docs/Web/API/CanvasRenderingContext2D/globalCompositeOperation
gco = [
    "source-over",
    "source-in",
    "source-out",
    "source-atop",
    "destination-over",
    "destination-in",
    "destination-out",
    "destination-atop",
    "lighter",
    "copy",
    "xor",
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

# gco.forEach(op => :
#   tests['path globalCompositeOperator ' + op] = function (ctx, done) :
#     ctx.save()
#     ctx.beginPath()
#     ctx.fillStyle = "rgba(255,0,0,1)"
#     ctx.arc(50, 100, 50, math.pi*2, 0, False)
#     ctx.fill()

#     ctx.globalCompositeOperation = op

#     ctx.beginPath()
#     ctx.fillStyle = "rgba(0,0,255,1)"
#     ctx.arc(110, 100, 50, math.pi*2, 0, False)
#     ctx.fill()

#     ctx.beginPath()
#     ctx.fillStyle = "rgba(0,255,0,1)"
#     ctx.arc(80, 50, 50, math.pi*2, 0, False)
#     ctx.fill()


#     done()
# })
def path_globalCompositeOperator(ctx, done, op):
    ctx.save()
    ctx.beginPath()
    ctx.fillStyle = "rgba(255,0,0,1)"
    ctx.arc(50, 100, 50, math.pi * 2, 0, False)
    ctx.fill()

    ctx.globalCompositeOperation = op

    ctx.beginPath()
    ctx.fillStyle = "rgba(0,0,255,1)"
    ctx.arc(110, 100, 50, math.pi * 2, 0, False)
    ctx.fill()

    ctx.beginPath()
    ctx.fillStyle = "rgba(0,255,0,1)"
    ctx.arc(80, 50, 50, math.pi * 2, 0, False)
    ctx.fill()

    done()


# gco.forEach(op => :
#   tests['image globalCompositeOperator ' + op] = function (ctx, done) :
#     img1 = Image()
#     img2 = Image()
#     def img1_onload():
#       def img2_onload():
#         ctx.globalAlpha = 0.7
#         ctx.drawImage(img1, 0, 0)
#         ctx.globalCompositeOperation = op
#         ctx.drawImage(img2, 0, 0)
#         done()
#       img2.src = imageSrc('blend-fg.png')
#     img1.src = imageSrc('blend-bg.png')
# })
def image_globalCompositeOperator(ctx, done, op):
    img1 = Image()
    img2 = Image()

    def img1_onload():
        def img2_onload():
            ctx.globalAlpha = 0.7
            ctx.drawImage(img1, 0, 0)
            ctx.globalCompositeOperation = op
            ctx.drawImage(img2, 0, 0)
            done()

        img2.src = imageSrc("blend-fg.png")
        img2_onload()

    img1.src = imageSrc("blend-bg.png")
    img1_onload()


# gco.forEach(op => :
#   tests['9 args, transform, globalCompositeOperator ' + op] = function (ctx, done) :
#     img1 = Image()
#     img2 = Image()
#     def img1_onload():
#       def img2_onload():
#         ctx.globalAlpha = 0.7
#         ctx.drawImage(img1, 0, 0)
#         ctx.globalCompositeOperation = op
#         ctx.translate(92, 12)
#         ctx.rotate(math.pi/4)
#         ctx.scale(0.8, .8)
#         ctx.drawImage(img2, 0, 0, 125, 125, 10, 10, 125, 125)
#         done()
#       img2.src = imageSrc('blend-fg.png')
#     img1.src = imageSrc('blend-bg.png')
# })
def _9_args_transform_globalCompositeOperator(ctx, done, op):
    img1 = Image()
    img2 = Image()

    def img1_onload():
        def img2_onload():
            ctx.globalAlpha = 0.7
            ctx.drawImage(img1, 0, 0)
            ctx.globalCompositeOperation = op
            ctx.translate(92, 12)
            ctx.rotate(math.pi / 4)
            ctx.scale(0.8, 0.8)
            ctx.drawImage(img2, 0, 0, 125, 125, 10, 10, 125, 125)
            done()

        img2.src = imageSrc("blend-fg.png")
        img2_onload()

    img1.src = imageSrc("blend-bg.png")
    img1_onload()


for op in gco:
    register(f"path globalCompositeOperator {op}")(
        lambda ctx, done, op=op: path_globalCompositeOperator(ctx, done, op)
    )
    register(f"image globalCompositeOperator {op}")(
        lambda ctx, done, op=op: image_globalCompositeOperator(ctx, done, op)
    )
    register(f"9 args, transform, globalCompositeOperator {op}")(
        lambda ctx, done, op=op: _9_args_transform_globalCompositeOperator(
            ctx, done, op
        )
    )


@register("drawImage with negative source rect origin")
def fn_drawImage_with_negative_source_rect_origin(ctx, done):
    img1 = Image()
    img2 = Image()

    def img1_onload():
        def img2_onload():
            ctx.drawImage(img1, 0, 0, 200, 200)
            ctx.drawImage(img2, -8, -8, 18, 18, 0, 0, 200, 200)
            ctx.restore()
            done()

        img2.src = imageSrc("checkers.png")
        img2_onload()

    img1.src = imageSrc("pentagon.png")
    img1_onload()


@register("composite with text")
def fn_composite_with_text(ctx, done):
    img = Image()

    def img_onload():
        ctx.drawImage(img, 0, 0)
        ctx.globalCompositeOperation = "destination-in"
        ctx.save()
        ctx.fillStyle = "red"
        ctx.font = "900 80px Arial"
        ctx.fillText("XXXX", 10, 100)

        ctx.restore()
        done()

    img.src = imageSrc("blend-bg.png")
    img_onload()


@register("composite with path")
def fn_composite_with_path(ctx, done):
    img = Image()

    def img_onload():
        ctx.drawImage(img, 0, 0)
        ctx.globalCompositeOperation = "destination-in"
        ctx.save()
        ctx.fillStyle = "red"
        ctx.beginPath()
        ctx.arc(50, 50, 30, 0, 2 * math.pi)
        ctx.fill()

        ctx.restore()
        done()

    img.src = imageSrc("blend-bg.png")
    img_onload()


@register("drawImage 9 arguments big numbers")
def fn_drawImage_9_arguments_big_numbers(ctx, done):
    img = Image()
    ctx.imageSmoothingEnabled = False

    def img_onload():
        # we use big numbers because is over the max canvas allowed
        ctx.drawImage(img, -90000, -90000, 90080, 90080, -180000, -18000, 180160, 18016)
        ctx.drawImage(
            img, -90000, -90000, 90040, 90040, -179930, -179930, 180060, 180060
        )
        ctx.drawImage(img, -90000, -90000, 90080, 90080, -18000, -180000, 18016, 180160)
        ctx.drawImage(img, 475, 380, 90000, 90000, 20, 20, 180000, 720000)
        done(None)

    # def img_onerror():
    # done(Error('Failed to load image'))
    img.src = imageSrc("globe.jpg")
    img_onload()


@register("known bug #416")
def fn_known_bug__416(ctx, done):
    img1 = Image()
    img2 = Image()

    def img1_onload():
        def img2_onload():
            ctx.drawImage(img1, 0, 0)
            ctx.globalCompositeOperation = "destination-in"
            ctx.save()
            ctx.translate(img2.width / 2, img1.height / 2)
            ctx.rotate(math.pi / 4)
            ctx.scale(0.5, 0.5)
            ctx.translate(-img2.width / 2, -img1.height / 2)
            ctx.drawImage(img2, 0, 0)
            ctx.restore()
            done()

        img2.src = imageSrc("blend-fg.png")
        img2_onload()

    img1.src = imageSrc("blend-bg.png")
    img1_onload()


def drawShadowPattern(
    ctx, color="#c00", offset=(0, 0), blur=5, color2=None, stroke=False, rectCb=None
):

    rectFn = "strokeRect" if stroke else "fillRect"

    getattr(ctx, rectFn)(150, 10, 20, 20)

    ctx.lineTo(20, 5)
    ctx.lineTo(100, 5)
    ctx.stroke()

    ctx.shadowColor = color
    ctx.shadowBlur = blur
    ctx.shadowOffsetX = offset[0]
    ctx.shadowOffsetY = offset[1]
    if rectCb:
        rectCb(20, 20, 100, 100)
    else:
        getattr(ctx, rectFn)(20, 20, 100, 100)

    ctx.beginPath()
    ctx.lineTo(20, 150)
    ctx.lineTo(100, 150)
    ctx.stroke()

    if color2:
        ctx.shadowColor = color2
    else:
        ctx.shadowBlur = 0

    ctx.beginPath()
    ctx.lineTo(20, 180)
    ctx.lineTo(100, 180)
    ctx.stroke()

    getattr(ctx, rectFn)(150, 150, 20, 20)


@register("shadowBlur")
def fn_shadowBlur(ctx):
    drawShadowPattern(ctx, color="#000")


@register("shadowColor")
def fn_shadowColor(ctx):
    drawShadowPattern(ctx)


@register("shadowOffset{X,Y}")
def fn_shadowOffset_X_Y_(ctx):
    drawShadowPattern(ctx, offset=(2, 2))


@register("shadowOffset{X,Y} large")
def fn_shadowOffset_X_Y__large(ctx):
    drawShadowPattern(ctx, offset=(10, 10))


@register("shadowOffset{X,Y} negative")
def fn_shadowOffset_X_Y__negative(ctx):
    drawShadowPattern(ctx, offset=(-10, -10))


@register("shadowBlur values")
def fn_shadowBlur_values(ctx):
    drawShadowPattern(ctx, blur=25, offset=(2, 2), color2="rgba(0,0,0,0)")


@register("shadow strokeRect()")
def fn_shadow_strokeRect__(ctx):
    drawShadowPattern(
        ctx, stroke=True, offset=(2, 2), color="#000", color2="rgba(0,0,0,0)"
    )


@register("shadow fill()")
def fn_shadow_fill__(ctx):

    def cb(x, y, w, h):
        ctx.rect(x, y, w, h)
        ctx.fill()

    drawShadowPattern(
        ctx, stroke=True, offset=(2, 2), color="#000", color2="rgba(0,0,0,0)", rectCb=cb
    )


@register("shadow stroke()")
def fn_shadow_stroke__(ctx):

    def cb(x, y, w, h):
        ctx.rect(x, y, w, h)
        ctx.stroke()

    drawShadowPattern(
        ctx, stroke=True, offset=(2, 2), color="#000", color2="rgba(0,0,0,0)", rectCb=cb
    )


@register("shadow translate, scale & rotate")
def fn_shadow_translate__scale___rotate(ctx):
    ctx.translate(50, 0)
    ctx.scale(0.8, 0.8)
    ctx.rotate(math.pi / 8)
    drawShadowPattern(ctx, offset=(10, 10))


@register("shadow scale & skew")
def fn_shadow_scale___skew(ctx):
    ctx.translate(-20, 0)
    # ctx.rotate(-(math.pi / 16))
    ctx.scale(0.85, 0.85)
    ctx.transform(1, 0.2, 0.3, 1, 0, 0)
    drawShadowPattern(ctx, offset=(10, 10), blur=9)


@register("shadowBlur rotate")
def fn_shadowBlur_rotate(ctx):
    ctx.shadowColor = "#c00"
    ctx.shadowBlur = 5
    ctx.shadowOffsetX = 10
    ctx.shadowOffsetY = 10
    drawPinwheel(ctx, scl=1, offset=25, len=65)


@register("shadowBlur rotate & scale")
def fn_shadowBlur_rotate___scale(ctx):
    ctx.shadowColor = "#c00"
    ctx.shadowBlur = 5
    ctx.shadowOffsetX = 10
    ctx.shadowOffsetY = 10
    drawPinwheel(ctx, scl=1.5, offset=20, len=65)


def drawScaledBoxes(ctx, sz=200, sp=50, x=None, y=None, scl=0.25):
    x = sp if x is None else x
    y = sp if y is None else y
    ctx.fillStyle = "black"
    ctx.shadowColor = "#c00"
    for i in range(1, 10):
        ctx.scale(scl, scl)
        ctx.fillRect(x, y, sz, sz)

        scl += 1 if i == 1 else 0.25
        sz /= scl
        sp /= scl
        x = sp if not (i % 3) else (x / scl + sz + sp)
        y /= scl
        if not (i % 3):
            y += sz + sp


@register("shadowBlur varying scale")
def fn_shadowBlur_varying_scale(ctx):
    ctx.shadowBlur = 6
    ctx.shadowOffsetX = 5
    ctx.shadowOffsetY = 5
    drawScaledBoxes(ctx)


@register("shadowBlur skew & varying scale")
def fn_shadowBlur_skew___varying_scale(ctx):
    ctx.shadowBlur = 6
    ctx.shadowOffsetX = -5
    ctx.shadowOffsetY = -8
    # ctx.translate(-20, 0)
    ctx.scale(0.85, 0.85)
    ctx.transform(1, 0.2, 0.3, 1, 0, 0)
    drawScaledBoxes(ctx)


@register("drop-shadow filter with scale")
def fn_drop_shadow_filter_with_scale(ctx):
    ctx.filter = "drop-shadow(5px 5px 6px #c00)"
    drawScaledBoxes(ctx)


@register("shadow globalAlpha")
def fn_shadow_globalAlpha(ctx):
    ctx.lineTo(0, 0)
    ctx.lineTo(50, 0)
    ctx.lineTo(50, 150)
    ctx.stroke()

    ctx.lineWidth = 5
    ctx.globalAlpha = 0.3
    ctx.shadowColor = "#00c"
    ctx.shadowBlur = 2
    ctx.shadowOffsetX = 8
    ctx.shadowOffsetY = 8

    ctx.lineTo(0, 150)
    ctx.stroke()


@register("shadow fillText()")
def fn_shadow_fillText__(ctx):
    ctx.shadowColor = "#00c"
    ctx.shadowBlur = 2
    ctx.shadowOffsetX = 8
    ctx.shadowOffsetY = 8
    ctx.textAlign = "center"
    ctx.font = "35px Arial"
    ctx.fillText("Shadow", 100, 100)


@register("shadow strokeText()")
def fn_shadow_strokeText__(ctx):
    ctx.shadowColor = "#00c"
    ctx.shadowBlur = 2
    ctx.shadowOffsetX = 8
    ctx.shadowOffsetY = 8
    ctx.textAlign = "center"
    ctx.font = "35px Arial"
    ctx.lineWidth = 2
    ctx.strokeText("Shadow", 100, 100)


@register("shadow gradient fill")
def fn_shadow_gradient_fill(ctx):
    ctx.shadowColor = "#c00"
    ctx.shadowBlur = 2
    ctx.shadowOffsetX = 8
    ctx.shadowOffsetY = 8

    grad = ctx.createLinearGradient(20, 20, 120, 120)
    grad.addColorStop(0, "yellow")
    grad.addColorStop(0.25, "red")
    grad.addColorStop(0.25, "rgba(0,0,0,0)")
    grad.addColorStop(0.75, "rgba(0,0,0,0)")
    grad.addColorStop(0.75, "blue")
    grad.addColorStop(1, "limegreen")

    ctx.fillStyle = grad
    ctx.translate(100, 0)
    ctx.rotate(math.pi / 4)
    ctx.fillRect(20, 20, 100, 100)


@register("shadow low opacity fill")
def fn_shadow_low_opacity_fill(ctx):
    ctx.shadowColor = "#c00"
    ctx.shadowBlur = 2
    ctx.shadowOffsetX = 8
    ctx.shadowOffsetY = 8

    ctx.fillStyle = "rgba(0,0,0, .2)"
    ctx.fillRect(20, 20, 100, 100)


@register("shadow low opacity drawImage")
def fn_shadow_low_opacity_drawImage(ctx, done):
    img = Image()

    def img_onload():

        ctx.shadowColor = "#000"
        ctx.shadowBlur = 4
        ctx.shadowOffsetX = 12
        ctx.shadowOffsetY = 12
        ctx.globalAlpha = 0.4

        ctx.drawImage(img, 0, 0)
        done(None)

    # img.onerror = done
    img.src = imageSrc("blend-fg.png")
    img_onload()


@register("shadow transform text")
def fn_shadow_transform_text(ctx):
    ctx.shadowColor = "#c0c"
    ctx.shadowBlur = 4
    ctx.shadowOffsetX = 6
    ctx.shadowOffsetY = 10
    ctx.textAlign = "center"
    ctx.font = "35px Arial"
    ctx.scale(2, 2)
    ctx.strokeText("Sha", 33, 40)
    ctx.rotate(math.pi / 2)
    ctx.fillText("dow", 50, -72)


@register("shadow image")
def fn_shadow_image(ctx, done):
    img = Image()

    def img_onload():
        ctx.shadowColor = "#f3ac22"
        ctx.shadowBlur = 2
        ctx.shadowOffsetX = 8
        ctx.shadowOffsetY = 8
        ctx.drawImage(img, 0, 0)
        done(None)

    # img.onerror = done
    img.src = imageSrc("star.png")
    img_onload()


@register("shadow image with crop")
def fn_shadow_image_with_crop(ctx, done):
    img = Image()

    def img_onload():
        ctx.shadowColor = "#000"
        ctx.shadowBlur = 12
        ctx.shadowOffsetX = 10
        ctx.shadowOffsetY = 10

        # cropped
        ctx.drawImage(img, 100, 100, 150, 150, 25, 25, 150, 150)
        done(None)

    # def img_onerror():
    #   done(Error('Failed to load image'))
    img.src = imageSrc("globe.jpg")
    img_onload()


@register("shadow image with crop and zoom")
def fn_shadow_image_with_crop_and_zoom(ctx, done):
    img = Image()

    def img_onload():
        ctx.shadowColor = "#000"
        ctx.shadowBlur = 12
        ctx.shadowOffsetX = 10
        ctx.shadowOffsetY = 10

        # cropped
        ctx.drawImage(img, 100, 220, 40, 40, 25, 25, 150, 150)
        done(None)

    # def img_onerror():
    #   done(Error('Failed to load image'))
    img.src = imageSrc("globe.jpg")
    img_onload()


@register("drawImage canvas over canvas")
def fn_drawImage_canvas_over_canvas(ctx):
    # Drawing canvas to itself
    ctx.fillStyle = "white"
    ctx.fillRect(0, 0, 200, 200)
    ctx.fillStyle = "black"
    ctx.fillRect(5, 5, 10, 10)
    ctx.drawImage(ctx.canvas, 20, 20)


@register("scaled shadow image")
def fn_scaled_shadow_image(ctx, done):
    img = Image()

    def img_onload():
        ctx.shadowColor = "#f3ac22"
        ctx.shadowBlur = 2
        ctx.shadowOffsetX = 8
        ctx.shadowOffsetY = 8
        ctx.drawImage(img, 10, 10, 80, 80)
        done(None)

    # img.onerror = done
    img.src = imageSrc("star.png")
    img_onload()


@register("smoothing disabled image")
def fn_smoothing_disabled_image(ctx, done):
    img = Image()

    def img_onload():
        ctx.imageSmoothingEnabled = False
        ctx.imageSmoothingQuality = "high"
        # cropped
        ctx.drawImage(img, 0, 0, 10, 10, 0, 0, 200, 200)
        done(None)

    # def img_onerror():
    #   done(Error('Failed to load image'))
    img.src = imageSrc("globe.jpg")
    img_onload()


@register("createPattern() with globalAlpha and smoothing off scaling down")
def fn_createPattern___with_globalAlpha_and_smoothing_off_scaling_down(ctx, done):
    img = Image()

    def img_onload():
        ctx.imageSmoothingEnabled = False
        ctx.imageSmoothingQuality = "high"
        pattern = ctx.createPattern(img, "repeat")
        ctx.scale(0.1, 0.1)
        ctx.globalAlpha = 0.95
        ctx.fillStyle = pattern
        ctx.fillRect(100, 100, 800, 800)
        ctx.globalAlpha = 1
        ctx.strokeStyle = pattern
        ctx.lineWidth = 800
        ctx.strokeRect(1400, 1100, 1, 800)
        done()

    img.src = imageSrc("globe.jpg")
    img_onload()


@register("createPattern() with globalAlpha and smoothing off scaling up")
def fn_createPattern___with_globalAlpha_and_smoothing_off_scaling_up(ctx, done):
    img = Image()

    def img_onload():
        ctx.imageSmoothingEnabled = False
        ctx.imageSmoothingQuality = "high"
        pattern = ctx.createPattern(img, "repeat")
        ctx.scale(20, 20)
        ctx.globalAlpha = 0.95
        ctx.fillStyle = pattern
        ctx.fillRect(1, 1, 8, 3)
        ctx.globalAlpha = 1
        ctx.strokeStyle = pattern
        ctx.lineWidth = 2
        ctx.strokeRect(2, 6, 6, 1)
        done()

    img.src = imageSrc("globe.jpg")
    img_onload()


@register("smoothing and gradients (gradients are not influenced by patternQuality)")
def fn_smoothing_and_gradients__gradients_are_not_influenced_by_patternQuality_(ctx):
    grad1 = ctx.createLinearGradient(0, 0, 10, 10)
    grad1.addColorStop(0, "yellow")
    grad1.addColorStop(0.25, "red")
    grad1.addColorStop(0.75, "blue")
    grad1.addColorStop(1, "limegreen")
    ctx.imageSmoothingEnabled = False
    ctx.globalAlpha = 0.9
    # linear grad box
    ctx.fillStyle = grad1
    ctx.moveTo(0, 0)
    ctx.lineTo(200, 0)
    ctx.lineTo(200, 200)
    ctx.lineTo(0, 200)
    ctx.lineTo(0, 0)
    ctx.scale(20, 20)
    ctx.fill()


@register("shadow integration")
def fn_shadow_integration(ctx):
    ctx.shadowBlur = 5
    ctx.shadowOffsetX = 10
    ctx.shadowOffsetY = 10
    ctx.shadowColor = "#eee"
    ctx.lineWidth = 3

    grad1 = ctx.createLinearGradient(105, 0, 200, 100)
    grad1.addColorStop(0, "yellow")
    grad1.addColorStop(0.25, "red")
    grad1.addColorStop(0.75, "blue")
    grad1.addColorStop(1, "limegreen")

    grad2 = ctx.createRadialGradient(50, 50, 10, 50, 50, 50)
    grad2.addColorStop(0, "yellow")
    grad2.addColorStop(0.25, "red")
    grad2.addColorStop(0.75, "blue")
    grad2.addColorStop(1, "limegreen")

    # linear grad box
    ctx.fillStyle = grad1
    ctx.fillRect(105, 0, 100, 100)

    # skyblue box
    ctx.fillStyle = "skyblue"
    ctx.fillRect(105, 101, 100, 100)

    # radial grad oval
    ctx.beginPath()
    ctx.arc(50, 50, 50, 0, math.pi * 2, False)
    ctx.fillStyle = grad2
    ctx.fill()

    # gold oval
    ctx.beginPath()
    ctx.arc(50, 151, 50, 0, math.pi * 2, False)
    ctx.fillStyle = "gold"
    ctx.fill()


@register("shadow vs blur filter")
def fn_shadow_vs_blur_filter(ctx):
    ctx.rotate(0.33)
    ctx.scale(3, 3)
    ctx.shadowBlur = 20
    ctx.shadowOffsetX = 10
    ctx.shadowOffsetY = 10
    ctx.shadowColor = "#333"

    ctx.filter = "blur(5px)"
    ctx.fillStyle = "orange"
    ctx.fillRect(20, 0, 33, 33)


@register("blur + shadow in filter")
def fn_blur___shadow_in_filter(ctx):
    ctx.rotate(0.33)
    ctx.scale(3, 3)
    ctx.filter = "drop-shadow(10px 10px 20px #333) blur(5px)"
    ctx.fillStyle = "orange"
    ctx.fillRect(20, 0, 33, 33)


@register("shadow in filter")
def fn_shadow_in_filter(ctx):
    ctx.rotate(0.33)
    ctx.scale(3, 3)
    ctx.filter = "drop-shadow(10px 10px 20px #333)"
    ctx.fillStyle = "orange"
    ctx.fillRect(20, 0, 33, 33)


@register("filter chains")
def fn_filter_chains(ctx):
    ctx.filter = "blur(5px) invert(56%) sepia(63%) saturate(4837%) hue-rotate(163deg) brightness(96%) contrast(101%)"
    ctx.fillRect(40, 40, 120, 120)


@register("font state")
def fn_font_state(ctx):
    ctx.save()
    ctx.font = "20px Impact"
    ctx.fillText("Bam!", 50, 80)

    ctx.save()
    ctx.font = "10px Arial"
    ctx.fillText("Boom!", 50, 100)

    ctx.restore()
    ctx.fillText("Bam again!", 50, 120)

    ctx.restore()
    ctx.fillText("Boom again!", 50, 140)


# Images


@register("drawImage(img) PNG")
def fn_drawImage_img__PNG(ctx, done):
    img = Image()

    def img_onload():
        ctx.drawImage(img, 0, 0)
        done(None)

    # img.onerror = done
    img.src = imageSrc("state.png")
    img_onload()


@register("drawImage(img) JPEG")
def fn_drawImage_img__JPEG(ctx, done):
    img = Image()

    def img_onload():
        ctx.drawImage(img, 0, 0, 100, 100)
        done(None)

    # img.onerror = done
    img.src = imageSrc("globe.jpg")
    img_onload()


@register("drawImage(img) CMYK JPEG")
def fn_drawImage_img__CMYK_JPEG(ctx, done):
    # This also provides coverage for CMYK JPEGs
    img = Image()

    def img_onload():
        ctx.drawImage(img, 0, 0, 100, 100)
        done(None)

    # img.onerror = done
    img.src = imageSrc("pentagon-cmyk.jpg")
    img_onload()


@register("drawImage(img) grayscale JPEG")
def fn_drawImage_img__grayscale_JPEG(ctx, done):
    img = Image()

    def img_onload():
        ctx.drawImage(img, 0, 0, 100, 100)
        done(None)

    # img.onerror = done
    img.src = imageSrc("pentagon-grayscale.jpg")
    img_onload()


@register("drawImage(img) WEBP")
def fn_drawImage_img__WEBP(ctx, done):
    img = Image()

    def img_onload():
        ctx.drawImage(img, 0, 0, 200, 200)
        done(None)

    # img.onerror = done
    img.src = imageSrc("rose.webp")
    img_onload()


@register("drawImage() SVG")
def fn_drawImage___SVG(ctx, done):
    img = Image()

    def img_onload():
        ctx.drawImage(img, 0, 0)
        done(None)

    # img.onerror = done
    img.src = imageSrc("tree.svg")
    img_onload()


@register("drawImage() SVG gradients/alpha")
def fn_drawImage___SVG_gradients_alpha(ctx, done):
    img = Image()

    def img_onload():
        ctx.drawImage(img, 0, 0, ctx.canvas.width, ctx.canvas.height)
        done(None)

    # img.onerror = done
    img.src = imageSrc("grapes.svg")
    img_onload()


@register("drawImage() SVG from URL w/ patterns/effects")
def fn_drawImage___SVG_from_URL_w__patterns_effects(ctx, done):
    img = Image()

    def img_onload():
        ctx.drawImage(img, 0, 0, ctx.canvas.width, ctx.canvas.height)
        done(None)

    # img.onerror = done
    # img.crossOrigin = "anonymous"
    img.src = "https://skia-canvas.org/test/rg1024_metal_effect.svg"
    img_onload()


# drawImage() variations


@register("drawImage(img,x,y)")
def fn_drawImage_img_x_y_(ctx, done):
    img = Image()

    def img_onload():
        ctx.drawImage(img, 25, 25)
        done(None)

    # img.onerror = done
    img.src = imageSrc("state.png")
    img_onload()


@register("drawImage(img,x,y,w,h) scale down")
def fn_drawImage_img_x_y_w_h__scale_down(ctx, done):
    img = Image()

    def img_onload():
        ctx.drawImage(img, 25, 25, 10, 10)
        done(None)

    # img.onerror = done
    img.src = imageSrc("state.png")
    img_onload()


@register("drawImage(img,x,y,w,h) scale down in a scaled up context")
def fn_drawImage_img_x_y_w_h__scale_down_in_a_scaled_up_context(ctx, done):
    img = Image()

    def img_onload():
        ctx.scale(20, 20)
        ctx.drawImage(img, -2.25, 0, 15, 10)
        done(None)

    # img.onerror = done
    img.src = imageSrc("globe.jpg")
    img_onload()


@register("drawImage(img,x,y,w,h) scale up")
def fn_drawImage_img_x_y_w_h__scale_up(ctx, done):
    img = Image()

    def img_onload():
        ctx.drawImage(img, -45, 0, 300, 200)
        done(None)

    # img.onerror = done
    img.src = imageSrc("globe.jpg")
    img_onload()


@register("drawImage(img,x,y,w,h) scale vertical")
def fn_drawImage_img_x_y_w_h__scale_vertical(ctx, done):
    img = Image()

    def img_onload():
        ctx.drawImage(img, 0, 0, img.width, 200)
        done(None)

    # img.onerror = done
    img.src = imageSrc("state.png")
    img_onload()


@register("drawImage(img,sx,sy,sw,sh,x,y,w,h)")
def fn_drawImage_img_sx_sy_sw_sh_x_y_w_h_(ctx, done):
    img = Image()

    def img_onload():
        ctx.drawImage(img, 13, 13, 45, 45, 25, 25, img.width / 2, img.height / 2)
        done(None)

    # img.onerror = done
    img.src = imageSrc("state.png")
    img_onload()


@register("drawCanvas(img,sx,sy,sw,sh,x,y,w,h)")
def fn_drawCanvas_img_sx_sy_sw_sh_x_y_w_h_(ctx, done):
    if False:
        return tests["drawImage(img,sx,sy,sw,sh,x,y,w,h)"](ctx, done)
    img = Image()

    def img_onload():
        srcCanvas = Canvas(200, 200)
        srcCtx = srcCanvas.getContext("2d")
        srcCtx.drawImage(img, 0, 0)
        ctx.drawCanvas(
            srcCtx.canvas, 13, 13, 45, 45, 25, 25, img.width / 2, img.height / 2
        )
        done(None)

    # img.onerror = (e) => { console.log(e); done(e); }
    img.src = imageSrc("state.png")
    img_onload()


@register("drawImage(img,0,0) globalAlpha")
def fn_drawImage_img_0_0__globalAlpha(ctx, done):
    img = Image()
    ctx.fillRect(50, 50, 30, 30)
    ctx.globalAlpha = 0.5

    def img_onload():
        ctx.drawImage(img, 0, 0)
        done(None)

    # img.onerror = done
    img.src = imageSrc("state.png")
    img_onload()


@register("drawImage(img,0,0) clip")
def fn_drawImage_img_0_0__clip(ctx, done):
    ctx.arc(50, 50, 50, 0, math.pi * 2, False)
    ctx.stroke()
    ctx.clip()
    img = Image()
    ctx.fillRect(50, 50, 30, 30)
    ctx.globalAlpha = 0.5

    def img_onload():
        ctx.drawImage(img, 0, 0)
        done(None)

    # img.onerror = done
    img.src = imageSrc("state.png")
    img_onload()


# SVG sizing, scaling and transform

SVG_IMG = """
<svg id='svg1' viewBox='0 0 100 100' xmlns='http://www.w3.org/2000/svg'>
  <circle r="32" cx="35" cy="65" fill="#F00" opacity="0.5"/>
  <circle r="32" cx="65" cy="65" fill="#0F0" opacity="0.5"/>
  <circle r="32" cx="50" cy="35" fill="#00F" opacity="0.5"/>
</svg>"""

SVG_TXT = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <path d="M0,50l50,-50l50,50l-50,50l-50-50" stroke="#000" fill="none"/>
  <path d="M2,50l48,-48l48,48l-48,48l-48-48" fill="#a23"/>
  <text x="50" y="64" font-family="serif" font-size="48" fill="#FFF" text-anchor="middle"><![CDATA[§]]></text>
</svg>"""


def addSvgSize(src, w, h):
    return re.sub(
        r">$", f' width="{w}" height="{h}">', src, count=1, flags=re.MULTILINE
    )


@register("drawImage() SVG with offset")
def fn_drawImage___SVG_with_offset(ctx, done):
    img = Image()

    def img_onload():
        ctx.drawImage(img, 25, 25)
        done(None)

    # img.onerror = done
    img.src = imageSrc("tree.svg")
    img_onload()


@register("drawImage() SVG natural size with scaling from drawImage")
def fn_drawImage___SVG_natural_size_with_scaling_from_drawImage(ctx, done):
    img = Image()

    def img_onload():
        ctx.drawImage(img, -350, -350, 1000, 1000)
        done(None)

    # img.onerror = done
    img.src = imageSrc("tree.svg")
    img_onload()


@register("drawImage() SVG natural size with scaling from ctx")
def fn_drawImage___SVG_natural_size_with_scaling_from_ctx(ctx, done):
    img = Image()

    def img_onload():
        ctx.scale(10, 10)
        ctx.drawImage(img, -35, -35)
        done(None)

    # img.onerror = (e) => { console.log(e); done(e); }
    img.src = imageSrc("tree.svg")
    img_onload()


@register("SVG no natural size drawImage(img,0,0)")
def fn_SVG_no_natural_size_drawImage_img_0_0_(ctx, done):
    img = Image()

    def img_onload():
        ctx.drawImage(img, 0, 0)
        done(None)

    # img.onerror = done
    img.src = f"""data:image/svg+xml;utf8,{encodeURIComponent(SVG_IMG)}"""
    img_onload()


@register("drawImage() SVG from string")
def fn_drawImage___SVG_from_string(ctx, done):
    img = Image()
    width, height = ctx.canvas.width, ctx.canvas.height

    def img_onload():
        ctx.drawImage(img, 0, 0, width, height)
        done(None)

    # img.onerror = done
    img.src = f"""data:image/svg+xml;utf8,{encodeURIComponent(SVG_IMG)}"""
    img_onload()


@register("drawImage() SVG from base64")
def fn_drawImage___SVG_from_base64(ctx, done):
    img = Image()
    size = 200

    def img_onload():
        ctx.drawImage(img, 0, 0, size, size)
        done(None)

    # img.onerror = done
    img.src = (
        f"""data:image/svg+xml;base64,{base64.b64encode(SVG_IMG.encode()).decode()}"""
    )
    img_onload()


@register("drawImage() SVG from remote URL")
def fn_drawImage___SVG_from_remote_URL(ctx, done):
    img = Image()
    size = 200

    def img_onload():
        ctx.drawImage(img, 0, 0, size, size)
        done(None)

    # img.onerror = done
    # img.crossOrigin = "anonymous"
    img.src = "https://skia-canvas.org/test/alphachannel.svg"
    img_onload()


@register("drawImage() SVG with font")
def fn_drawImage___SVG_with_font(ctx, done):
    # if (FontLibrary) :
    #   FontLibrary.use(imageSrc("Monoton-Regular.woff2"))
    #   console.log(FontLibrary.has("Monoton"))
    #
    img = Image()
    size = 200

    def img_onload():
        ctx.drawImage(img, 0, 0, size, size)
        done(None)

    # img.onerror = done
    img.src = f"""data:image/svg+xml;utf8,{encodeURIComponent(SVG_TXT)}"""
    img_onload()


@register("SVG no natural size drawImage(img,sx,sy,sw,sh,x,y,w,h)")
def fn_SVG_no_natural_size_drawImage_img_sx_sy_sw_sh_x_y_w_h_(ctx, done):
    img = Image()

    def img_onload():
        ctx.drawImage(
            img,
            0,
            0,
            img.width / 2,
            img.height / 2,
            0,
            0,
            img.width / 2,
            img.height / 2,
        )
        done(None)

    # img.onerror = done
    img.src = f"""data:image/svg+xml;utf8,{encodeURIComponent(SVG_TXT)}"""
    img_onload()


@register("SVG with natural size drawImage(img,sx,sy,sw,sh,x,y,w,h)")
def fn_SVG_with_natural_size_drawImage_img_sx_sy_sw_sh_x_y_w_h_(ctx, done):
    img = Image()

    def img_onload():
        ctx.drawImage(
            img,
            0,
            0,
            img.width / 2,
            img.height / 2,
            0,
            0,
            img.width / 2,
            img.height / 2,
        )
        done(None)

    # img.onerror = done
    img.src = f"""data:image/svg+xml;utf8,{encodeURIComponent(addSvgSize(SVG_TXT, 200, 200))}"""
    img_onload()


@register("SVG with natural size drawImage(img,sx,sy,sw,sh,x,y,w,h) with scaling")
def fn_SVG_with_natural_size_drawImage_img_sx_sy_sw_sh_x_y_w_h__with_scaling(ctx, done):
    img = Image()

    def img_onload():
        ctx.drawImage(img, 0, 0, img.width / 2, img.height / 2, 0, 0, 190, 190)
        done(None)

    # img.onerror = done
    img.src = (
        f"""data:image/svg+xml;utf8,{encodeURIComponent(addSvgSize(SVG_TXT, 50, 50))}"""
    )
    img_onload()


@register("createPattern() from SVG with natural size")
def fn_createPattern___from_SVG_with_natural_size(ctx, done):
    img = Image()

    def img_onload():
        pattern = ctx.createPattern(img, "repeat")
        ctx.scale(0.1, 0.1)
        ctx.fillStyle = pattern
        ctx.fillRect(100, 100, 800, 800)
        ctx.strokeStyle = pattern
        ctx.lineWidth = 200
        ctx.strokeRect(1100, 1100, 800, 800)
        done()

    img.src = f"""data:image/svg+xml;utf8,{encodeURIComponent(addSvgSize(SVG_IMG, 200, 200))}"""
    img_onload()


@register("createPattern() from SVG no natural size")
def fn_createPattern___from_SVG_no_natural_size(ctx, done):
    img = Image()

    def img_onload():
        pattern = ctx.createPattern(img, "repeat")
        ctx.scale(0.1, 0.1)
        ctx.fillStyle = pattern
        ctx.fillRect(100, 100, 800, 800)
        ctx.strokeStyle = pattern
        ctx.lineWidth = 200
        ctx.strokeRect(1100, 1100, 800, 800)
        done()

    img.src = f"""data:image/svg+xml;utf8,{encodeURIComponent(SVG_IMG)}"""
    img_onload()


@register("SVG shadow & filters")
def fn_SVG_shadow___filters(ctx, done):
    img = Image()
    size = 200

    def img_onload():
        ctx.drawImage(img, 0, 0, size, size)
        done(None)

    ctx.shadowBlur = 5
    ctx.shadowOffsetX = 5
    ctx.shadowOffsetY = 7
    ctx.shadowColor = "black"

    ctx.filter = "blur(1px) hue-rotate(90deg) saturate(4893%)"

    # img.onerror = done
    img.src = imageSrc("grapes.svg")
    img_onload()


@register("SVG globalCompositeOperator SVG under")
def fn_SVG_globalCompositeOperator_SVG_under(ctx, done):
    img1 = Image()
    img2 = Image()

    def img1_onload():
        def img2_onload():
            ctx.globalAlpha = 0.7
            ctx.drawImage(img1, 0, 0, ctx.canvas.width, ctx.canvas.height)
            ctx.globalCompositeOperation = "difference"
            ctx.translate(100, 100)
            ctx.rotate(0.25 * math.pi)
            ctx.translate(-50, -75)
            ctx.scale(0.8, 0.8)
            ctx.drawImage(img2, 50, 50)
            done()

        img2.src = imageSrc("blend-fg.png")
        img2_onload()

    img1.src = imageSrc("grapes.svg")
    img1_onload()


@register("SVG globalCompositeOperator SCG over")
def fn_SVG_globalCompositeOperator_SCG_over(ctx, done):
    img1 = Image()
    img2 = Image()

    def img1_onload():
        def img2_onload():
            ctx.globalAlpha = 0.7
            ctx.translate(100, 100)
            ctx.rotate(0.25 * math.pi)
            ctx.translate(-50, -75)
            ctx.scale(0.8, 0.8)
            ctx.drawImage(img1, 50, 50)
            ctx.globalCompositeOperation = "difference"
            ctx.resetTransform()
            ctx.drawImage(img2, 0, 0, ctx.canvas.width, ctx.canvas.height)
            done()

        img2.src = imageSrc("grapes.svg")
        img2_onload()

    img1.src = imageSrc("blend-fg.png")
    img1_onload()


@register("SVG globalCompositeOperator xor")
def fn_SVG_globalCompositeOperator_xor(ctx, done):
    img1 = Image()
    img2 = Image()

    def img1_onload():
        def img2_onload():
            ctx.globalAlpha = 0.7
            ctx.drawImage(img1, 0, 0, ctx.canvas.width, ctx.canvas.height)
            ctx.globalCompositeOperation = "xor"
            ctx.drawImage(img2, 50, 50)
            done()

        img2.src = imageSrc("blend-fg.png")
        img2_onload()

    img1.src = imageSrc("grapes.svg")
    img1_onload()


@register("SVG globalAlpha + clip")
def fn_SVG_globalAlpha___clip(ctx, done):
    ctx.arc(100, 100, 75, 0, math.pi * 2, False)
    ctx.stroke()
    ctx.clip()
    img = Image()
    ctx.fillRect(50, 50, 30, 30)
    ctx.globalAlpha = 0.5

    def img_onload():
        ctx.drawImage(img, 0, 0, ctx.canvas.width, ctx.canvas.height)
        done(None)

    # img.onerror = done
    img.src = imageSrc("grapes.svg")
    img_onload()


# ImageData


@register("putImageData()")
def fn_putImageData__(ctx):
    for i in range(6):
        for j in range(6):
            ctx.fillStyle = (
                f"rgb({math.floor(255 - 42.5 * i)},{math.floor(255 - 42.5 * j)},0)"
            )
            ctx.fillRect(j * 25, i * 25, 25, 25)
    data = ctx.getImageData(0, 0, 50, 50)
    ctx.putImageData(data, 10, 10)


@register("putImageData() 1")
def fn_putImageData___1(ctx):
    for i in range(6):
        for j in range(6):
            ctx.fillStyle = (
                f"rgb({math.floor(255 - 42.5 * i)},{math.floor(255 - 42.5 * j)},0)"
            )
            ctx.fillRect(j * 25, i * 25, 25, 25)
    data = ctx.getImageData(0, 0, 50, 50)
    ctx.putImageData(data, -10, -10)


@register("putImageData() 2")
def fn_putImageData___2(ctx):
    for i in range(6):
        for j in range(6):
            ctx.fillStyle = (
                f"rgb({math.floor(255 - 42.5 * i)},{math.floor(255 - 42.5 * j)},0)"
            )
            ctx.fillRect(j * 25, i * 25, 25, 25)
    data = ctx.getImageData(25, 25, 50, 50)
    ctx.putImageData(data, 10, 10)


@register("putImageData() 3")
def fn_putImageData___3(ctx):
    for i in range(6):
        for j in range(6):
            ctx.fillStyle = (
                f"rgb({math.floor(255 - 42.5 * i)},{math.floor(255 - 42.5 * j)},0)"
            )
            ctx.fillRect(j * 25, i * 25, 25, 25)
    data = ctx.getImageData(10, 25, 10, 50)
    ctx.putImageData(data, 50, 10)


@register("putImageData() 4")
def fn_putImageData___4(ctx):
    for i in range(6):
        for j in range(6):
            ctx.fillStyle = (
                f"rgb({math.floor(255 - 42.5 * i)},{math.floor(255 - 42.5 * j)},0)"
            )
            ctx.fillRect(j * 25, i * 25, 25, 25)
    ctx.strokeRect(30, 30, 30, 30)
    data = ctx.getImageData(0, 0, 50, 50)
    ctx.putImageData(data, 30, 30, 10, 10, 30, 30)


@register("putImageData() 5")
def fn_putImageData___5(ctx):
    for i in range(6):
        for j in range(6):
            ctx.fillStyle = (
                f"rgb({math.floor(255 - 42.5 * i)},{math.floor(255 - 42.5 * j)},0)"
            )
            ctx.fillRect(j * 25, i * 25, 25, 25)
    ctx.strokeRect(60, 60, 50, 30)
    data = ctx.getImageData(0, 0, 50, 50)
    ctx.putImageData(data, 60, 60, 0, 0, 50, 30)


@register("putImageData() 6")
def fn_putImageData___6(ctx):
    for i in range(6):
        for j in range(6):
            ctx.fillStyle = (
                f"rgb({math.floor(255 - 42.5 * i)},{math.floor(255 - 42.5 * j)},0)"
            )
            ctx.fillRect(j * 25, i * 25, 25, 25)
    ctx.strokeRect(60, 60, 50, 30)
    data = ctx.getImageData(0, 0, 50, 50)
    ctx.putImageData(data, 60, 60, 10, 0, 35, 30)


@register("putImageData() 7")
def fn_putImageData___7(ctx):
    for i in range(6):
        for j in range(6):
            ctx.fillStyle = (
                f"rgb({math.floor(255 - 42.5 * i)},{math.floor(255 - 42.5 * j)},0)"
            )
            ctx.fillRect(j * 25, i * 25, 25, 25)
    ctx.strokeRect(60, 60, 50, 30)
    ctx.translate(20, 20)
    data = ctx.getImageData(75, 35, 50, 50)
    ctx.putImageData(data, 60, 60, 10, 20, 35, -10)


@register("putImageData() 8")
def fn_putImageData___8(ctx):
    for i in range(6):
        for j in range(6):
            ctx.fillStyle = (
                f"rgb({math.floor(255 - 42.5 * i)},{math.floor(255 - 42.5 * j)},0)"
            )
            ctx.fillRect(j * 25, i * 25, 25, 25)
    ctx.translate(20, 20)
    data = ctx.getImageData(0, 0, 50, 50)
    ctx.putImageData(data, -10, -10, 0, 20, 35, 30)


@register("putImageData() 9")
def fn_putImageData___9(ctx):
    for i in range(6):
        for j in range(6):
            ctx.fillStyle = (
                f"rgb({math.floor(255 - 42.5 * i)},{math.floor(255 - 42.5 * j)},0)"
            )
            ctx.fillRect(j * 25, i * 25, 25, 25)
    ctx.translate(20, 20)
    data = ctx.getImageData(0, 0, 50, 50)
    ctx.putImageData(data, -10, -10, 0, 20, 500, 500)


@register("putImageData() 10")
def fn_putImageData___10(ctx):
    ctx.fillStyle = "rgba(255,0,0,1)"
    ctx.fillRect(0, 0, 50, 100)
    ctx.fillStyle = "rgba(0,255,0,1)"
    ctx.fillRect(50, 0, 50, 100)
    ctx.fillStyle = "rgba(0,0,255,1)"
    ctx.fillRect(100, 0, 50, 100)

    data = ctx.getImageData(0, 0, 120, 20)
    ctx.putImageData(data, 20, 120)


@register("putImageData() alpha")
def fn_putImageData___alpha(ctx):
    ctx.fillStyle = "rgba(255,0,0,0.5)"
    ctx.fillRect(0, 0, 50, 100)
    ctx.fillStyle = "rgba(0,255,0,0.5)"
    ctx.fillRect(50, 0, 50, 100)
    ctx.fillStyle = "rgba(0,0,255,0.5)"
    ctx.fillRect(100, 0, 50, 100)

    data = ctx.getImageData(0, 0, 120, 20)
    ctx.putImageData(data, 20, 120)


@register("putImageData() alpha 2")
def fn_putImageData___alpha_2(ctx):
    ctx.fillStyle = "rgba(255,0,0,0.2)"
    ctx.fillRect(0, 0, 50, 100)
    ctx.fillStyle = "rgba(0,255,0,0.5)"
    ctx.fillRect(50, 0, 50, 100)
    ctx.fillStyle = "rgba(0,0,255,0.75)"
    ctx.fillRect(100, 0, 50, 100)

    data = ctx.getImageData(0, 0, 120, 20)
    ctx.putImageData(data, 20, 120)


@register("putImageData() globalAlpha")
def fn_putImageData___globalAlpha(ctx):
    ctx.globalAlpha = 0.5
    ctx.fillStyle = "#f00"
    ctx.fillRect(0, 0, 50, 100)
    ctx.fillStyle = "#0f0"
    ctx.fillRect(50, 0, 50, 100)
    ctx.fillStyle = "#00f"
    ctx.fillRect(100, 0, 50, 100)

    data = ctx.getImageData(0, 0, 120, 20)
    ctx.putImageData(data, 20, 120)


@register("putImageData() png data")
def fn_putImageData___png_data(ctx, done):
    img = Image()
    ctx.fillRect(50, 50, 30, 30)

    def img_onload():
        ctx.drawImage(img, 0, 0, 200, 200)
        imageData = ctx.getImageData(0, 0, 50, 50)
        data = imageData.data
        if isinstance(data, bytearray):
            for i in range(0, len(data), 4):
                data[i + 3] = 80
        ctx.putImageData(imageData, 50, 50)
        done(None)

    # img.onerror = done

    img.src = imageSrc("state.png")
    img_onload()


@register("putImageData() png data 2")
def fn_putImageData___png_data_2(ctx, done):
    img = Image()
    ctx.fillRect(50, 50, 30, 30)

    def img_onload():
        ctx.drawImage(img, 0, 0, 200, 200)
        imageData = ctx.getImageData(0, 0, 50, 50)
        data = imageData.data
        if isinstance(data, bytearray):
            for i in range(0, len(data), 4):
                data[i + 3] = 80
        ctx.putImageData(imageData, 50, 50, 10, 10, 20, 20)
        done(None)

    # img.onerror = done

    img.src = imageSrc("state.png")
    img_onload()


@register("putImageData() png data 3")
def fn_putImageData___png_data_3(ctx, done):
    img = Image()
    ctx.fillRect(50, 50, 30, 30)

    def img_onload():
        ctx.drawImage(img, 0, 0, 200, 200)
        imageData = ctx.getImageData(0, 0, 50, 50)
        data = imageData.data
        if isinstance(data, bytearray):
            for i in range(0, len(data), 4):
                data[i + 0] = int(data[i + 0] * 0.2)
                data[i + 1] = int(data[i + 1] * 0.2)
                data[i + 2] = int(data[i + 2] * 0.2)
        ctx.putImageData(imageData, 50, 50)
        done(None)

    # img.onerror = done
    img.src = imageSrc("state.png")
    img_onload()


@register("setLineDash")
def fn_setLineDash(ctx):
    ctx.setLineDash([10, 5, 25, 15])
    ctx.lineWidth = 14

    y = 5

    def line(lineDash, color=None):
        nonlocal y
        ctx.setLineDash(lineDash)
        if color:
            ctx.strokeStyle = color
        ctx.beginPath()
        ctx.moveTo(0, y)
        ctx.lineTo(200, y)
        ctx.stroke()
        y += ctx.lineWidth + 4

    line([15, 30], "blue")
    line([], "black")
    line([5, 10, 15, 20, 25, 30, 35, 40, 45, 50], "purple")
    line([8], "green")
    line([3, 3, -30], "red")
    line([4, float("inf"), 4])
    line([10, 10, float("nan")])

    def inner1():
        ctx.setLineDash([8])
        a = ctx.getLineDash()
        a[0] -= 3
        a.append(20)
        return a

    line(inner1(), "orange")

    line([0, 0], "purple")  # should be full
    line([0, 0, 3, 0], "orange")  # should be full
    line([0, 3, 0, 0], "green")  # should be empty


# tests['lineDashOffset'] = function (ctx) :
#   ctx.setLineDash([10, 5, 25, 15])
#   ctx.lineWidth = 4

#   y = 5
#   line = function (lineDashOffset, color) :
#     ctx.lineDashOffset = lineDashOffset
#     if color: ctx.strokeStyle = color
#     ctx.beginPath()
#     ctx.moveTo(0, y)
#     ctx.lineTo(200, y)
#     ctx.stroke()
#     y += ctx.lineWidth + 4
#

#   line(-10, 'black')
#   line(0)
#   line(10)
#   line(20)
#   line(30)
#   line(40, 'blue')
#   line(float('nan'))
#   line(50, 'green')
#   line(float('inf'))
#   line(60, 'orange')
#   line(-float('inf'))
#   line(70, 'purple')
#   line(void 0)
#   line(80, 'black')
#   line(ctx.lineDashOffset + 10)

#   for i in range(10):
#     line(90 + i / 5, 'red')
#
#


@register("fillStyle='hsl(...)'")
def fillStyle_hsl(ctx):
    for i in range(6):
        for j in range(6):
            ctx.fillStyle = (
                f"hsl({360 - 60 * i},{100 - 16.66 * j}%,{50 + (i + j) * (50 / 12)}%)"
            )
            ctx.fillRect(j * 25, i * 25, 25, 25)


@register("fillStyle='hsla(...)'")
def fillStyle_hsla(ctx):
    for i in range(6):
        for j in range(6):
            ctx.fillStyle = (
                f"hsla({360 - 60 * i},{100 - 16.66 * j}%,50%,{1 - 0.16 * j})"
            )
            ctx.fillRect(j * 25, i * 25, 25, 25)


# tests['textBaseline and scale'] = function (ctx) :
#   ctx.strokeStyle = '#666'
#   ctx.strokeRect(0, 0, 200, 200)
#   ctx.lineTo(0, 50)
#   ctx.lineTo(200, 50)
#   ctx.stroke()
#   ctx.beginPath()
#   ctx.lineTo(0, 150)
#   ctx.lineTo(200, 150)
#   ctx.stroke()

#   ctx.font = 'normal 20px Arial'
#   ctx.textBaseline = 'bottom'
#   ctx.textAlign = 'center'
#   ctx.fillText('bottom', 100, 50)

#   ctx.scale(0.1, 0.1)
#   ctx.font = 'normal 200px Arial'
#   ctx.textBaseline = 'bottom'
#   ctx.textAlign = 'center'
#   ctx.fillText('bottom', 1000, 1500)
#

# tests['rotated baseline'] = function (ctx) :
#   ctx.font = '12px Arial'
#   ctx.fillStyle = 'black'
#   ctx.textAlign = 'center'
#   ctx.textBaseline = 'bottom'
#   ctx.translate(100, 100)

#   for (i = 0; i < 16; i += 1) :
#     ctx.fillText('Hello world!', -50, -50)
#     ctx.rotate(-math.pi / 8)
#
#

# tests['rotated and scaled baseline'] = function (ctx) :
#   ctx.font = '120px Arial'
#   ctx.fillStyle = 'black'
#   ctx.textAlign = 'center'
#   ctx.textBaseline = 'bottom'
#   ctx.translate(100, 100)
#   ctx.scale(0.1, 0.2)

#   for (i = 0; i < 16; i += 1) :
#     ctx.fillText('Hello world!', -50 / 0.1, -50 / 0.2)
#     ctx.rotate(-math.pi / 8)
#
#

# tests['rotated and skewed baseline'] = function (ctx) :
#   ctx.font = '12px Arial'
#   ctx.fillStyle = 'black'
#   ctx.textAlign = 'center'
#   ctx.textBaseline = 'bottom'
#   ctx.translate(100, 100)
#   ctx.transform(1, 1, 0, 1, 1, 1)

#   for (i = 0; i < 16; i += 1) :
#     ctx.fillText('Hello world!', -50, -50)
#     ctx.rotate(-math.pi / 8)
#
#

# tests['rotated, scaled and skewed baseline'] = function (ctx) :
#   # Known issue: we don't have a way to decompose the cairo matrix into the
#   # skew and rotation separately.
#   ctx.font = '120px Arial'
#   ctx.fillStyle = 'black'
#   ctx.textAlign = 'center'
#   ctx.textBaseline = 'bottom'
#   ctx.translate(100, 100)
#   ctx.scale(0.1, 0.2)
#   ctx.transform(1, 1, 0, 1, 1, 1)

#   for (i = 0; i < 16; i += 1) :
#     ctx.fillText('Hello world!', -50 / 0.1, -50 / 0.2)
#     ctx.rotate(-math.pi / 8)
#
#

# tests['measureText()'] = function (ctx) :
#   # Note: As of Sep 2017, Chrome is the only browser with advanced TextMetrics,
#   # and they're behind a flag, and a few of them are missing and others are
#   # wrong.
#   function drawWithBBox (text, x, y) :
#     ctx.fillText(text, x, y)
#     ctx.strokeStyle = 'red'
#     ctx.beginPath(); ctx.moveTo(0, y + 0.5); ctx.lineTo(200, y + 0.5); ctx.stroke()
#     metrics = ctx.measureText(text)
#     ctx.strokeStyle = 'blue'
#     ctx.strokeRect(
#       x - metrics.actualBoundingBoxLeft + 0.5,
#       y - metrics.actualBoundingBoxAscent + 0.5,
#       metrics.width,
#       metrics.actualBoundingBoxAscent + metrics.actualBoundingBoxDescent
#     )
#

#   ctx.font = '20px Arial'
#   ctx.textBaseline = 'alphabetic'
#   drawWithBBox('Alphabet alphabetic', 20, 50)

#   drawWithBBox('weruoasnm', 50, 175) # no ascenders/descenders

#   drawWithBBox(',', 100, 125) # tiny height

#   ctx.textBaseline = 'bottom'
#   drawWithBBox('Alphabet bottom', 20, 90)

#   ctx.textBaseline = 'alphabetic'
#   ctx.rotate(math.pi / 8)
#   drawWithBBox('Alphabet', 50, 100)
#


@register("image sampling (#1084)")
def fn_image_sampling___1084_(ctx, done):
    loaded1, loaded2 = False, False
    img1 = Image()
    img2 = Image()

    def img1_onload():
        nonlocal loaded1, loaded2
        loaded1 = True
        ctx.drawImage(img1, -170 - 100, -203, 352, 352)
        if loaded2:
            done()

    # img1.onerror = done

    def img2_onload():
        nonlocal loaded1, loaded2
        loaded2 = True
        ctx.drawImage(img2, 182 - 100, -203, 352, 352)
        if loaded1:
            done()

    # img2.onerror = done

    img1.src = imageSrc("halved-1.jpeg")
    img2.src = imageSrc("halved-2.jpeg")
    img1_onload()
    img2_onload()


@register("drawImage reflection bug")
def fn_drawImage_reflection_bug(ctx, done):
    img1 = Image()

    def img1_onload():
        ctx.drawImage(img1, 60, 30, 150, 150, 0, 0, 200, 200)
        done()

    img1.src = imageSrc("pentagon.png")
    img1_onload()


@register("drawImage reflection bug with skewing")
def fn_drawImage_reflection_bug_with_skewing(ctx, done):
    img1 = Image()

    def img1_onload():
        ctx.transform(1.2, 1, 1.8, 1.3, 0, 0)
        ctx.drawImage(img1, 60, 30, 150, 150, 0, 0, 200, 200)
        ctx.setTransform(1.2, 1.8, 0.3, 0.8, 0, 0)
        ctx.drawImage(img1, 30, 60, 150, 150, -5, -5, 200, 200)
        done()

    img1.src = imageSrc("pentagon.png")
    img1_onload()


@register("transformed drawimage")
def fn_transformed_drawimage(ctx):
    ctx.fillStyle = "white"
    ctx.fillRect(0, 0, 200, 200)
    ctx.fillStyle = "#999"
    ctx.fillRect(5, 5, 50, 50)
    ctx.transform(1.2, 1, 1.8, 1.3, 0, 0)
    ctx.drawImage(ctx.canvas, 0, 0)


# endregion
