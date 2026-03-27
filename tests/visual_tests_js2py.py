#! /usr/bin/env python3
from pathlib import Path

dir = Path(__file__).resolve().parent
tests_js = dir / "visual" / "tests.js"


replace_mapping = {
    "===": "==",
    "!==": "!=",
    "// ": "# ",
    "const ": "",
    "let ": "",
    "null": "None",
    "true": "True",
    "false": "False",
    "new ": "",
    "var ": "",
    "Math.PI": "math.pi",
    "Math.round": "round",
    "Math.random": "random.random",
    "Math": "math",
    "} else {": "else:",
    "`": '"""',
    "&&": "and",
    "||": "or",
    "NaN": "float('nan')",
    "Infinity": "float('inf')",
}

snippet_mapping = {
    "do :": "while True:",
    "if (i > 20000) break": "if i > 20000: break",
    "if (brightness < 0) brightness = 0": "if (brightness < 0): brightness = 0",
    "if (color) ctx.strokeStyle = color": "if color: ctx.strokeStyle = color",
    "} while (x2 != R - O and y2 != 0)": "  if not (x2 != R - O and y2 != 0):break",
    "ctx[rectFn]": "getattr(ctx, rectFn)",
    "for (i = 0; i <= 12; i++) :": "for i in range(13):",
    "for (i = 0; i < 3; i++) :": "for i in range(3):",
    "for (j = 0; j < 3; j++) :": "for j in range(3):",
    "for (i = 0; i < 4; i++) :": "for i in range(4):",
    "for (i = 0; i < 6; i++) :": "for i in range(6):",
    "for (j = 0; j < 6; j++) :": "for j in range(6):",
    "for (i = 0; i < 7; i++) :": "for i in range(7):",
    "for (i = 0; i < n; i++) :": "for i in range(n):",
    "for (i = 0; i < 9; i++) :": "for i in range(9):",
    "for (i = 0; i < 10; i++) :": "for i in range(10):",
    "for (i = 1; i < 6; i++) :": "for i in range(1, 6):",
    "for (i = 1; i < 9; i++) :": "for i in range(1, 9):",
    "for (i = 1; i <= 9; i++) :": "for i in range(1, 10):",
    "for (i = 1; i <= 9; ++i) :": "for i in range(1, 10):",
    "for (j = 1; j < 50; j++) :": "for j in range(1, 50):",
    "for (i = 1; i < 6; i++) {": "for i in range(1, 6):",
    "for (j = 0; j < i * 6; j++) {": "for j in range(i * 6):",
    "for (x = 0; x < 243 / level; ++x) :": "for x in range(math.ceil(243 / level)):",
    "for (x = 0; x < 243 / level; x += 3) :": "for x in range(0, math.ceil(243 / level), 3):",
    "for (i = 0; i < 70; i += 3.05) :": "for i in frange(0, 70, 3.05):",
    "for (i = 0; i < lineCap.length; i++) :": "for i in range(len(lineCap)):",
    "for (i = 0; i < lineJoin.length; i++) :": "for i in range(len(lineJoin)):",
    "for (i = 0, len = data.length; i < len; i += 4) :": "for i in range(0, len(data), 4):",
    "    if ((y += 3) >= 243 / level) :": "    y += 3\n    if y >= 243 / level:",
    "  rectFn = stroke ? 'strokeRect' : 'fillRect'": "  rectFn = 'strokeRect' if stroke else 'fillRect'",
    "{ color = '#c00', offset = [0,0], blur = 5, color2 = None, stroke = False, rectCb =None } = { }": "color = '#c00', offset = (0,0), blur = 5, color2 = None, stroke = False, rectCb =None",
    "{scl = .5, offset = 0, len = 100, cb = None} = {}": "scl = .5, offset = 0, len = 100, cb = None",
    "{ color: '#000' }": "color='#000'",
    "{ offset: [2,2] }": "offset=(2,2)",
    "{ offset: [10,10] }": "offset=(10,10)",
    "{ offset: [-10,-10] }": "offset=(-10,-10)",
    "{ blur: 25, offset: [2,2], color2: 'rgba(0,0,0,0)' }": "blur=25, offset=(2,2), color2='rgba(0,0,0,0)'",
    "{ stroke: True, offset: [2,2], color: '#000', color2: 'rgba(0,0,0,0)' }": "stroke=True, offset=(2,2), color='#000', color2='rgba(0,0,0,0)'",
    """  drawShadowPattern(ctx, :
    stroke: True, offset: [2,2], color: '#000', color2: 'rgba(0,0,0,0)',
    rectCb: (x,y,w,h) => :
      ctx.rect(x,y,w,h)
      ctx.fill()
  })""": """
  def cb(x, y, w, h):
    ctx.rect(x, y, w, h)
    ctx.fill()
  drawShadowPattern(ctx, stroke=True, offset=(2,2), color='#000', color2='rgba(0,0,0,0)', rectCb=cb)""",
    """  drawShadowPattern(ctx, :
    stroke: True, offset: [2,2], color: '#000', color2: 'rgba(0,0,0,0)',
    rectCb: (x,y,w,h) => :
      ctx.rect(x,y,w,h)
      ctx.stroke()
  })""": """
  def cb(x, y, w, h):
    ctx.rect(x, y, w, h)
    ctx.stroke()
  drawShadowPattern(ctx, stroke=True, offset=(2,2), color='#000', color2='rgba(0,0,0,0)', rectCb=cb)""",
    "'rgb(' + c + ',' + c + ',' + c + ')'": 'f"rgb({c},{c},{c})"',
    "  cb = isWeb ? None : (a,b,c,d) => ctx.transform(DOMMatrix(a, b, c, d, 0, 0))": "  cb = lambda a, b, c, d: ctx.transform(DOMMatrix(a, b, c, d, 0, 0))",
    "{ scl: .5, offset: 0, len:100, cb}": "scl=.5, offset=0, len=100, cb=cb",
    "cb = isWeb ? None : (a,b,c,d) => ctx.transform({a: a, b: b, c: c, d: d, e: 0, f: 0})": "cb = lambda a, b, c, d: ctx.transform({'a': a, 'b': b, 'c': c, 'd': d, 'e': 0, 'f': 0})",
    "'rgb(' + (51 * i) + ',' + (255 - 51 * i) + ',255)'": 'f"rgb({51 * i},{255 - 51 * i},255)"',
    "'hsl(' + (360 - 60 * i) + ',' + (100 - 16.66 * j) + '%,' + (50 + (i + j) * (50 / 12)) + '%)'": 'f"hsl({360 - 60 * i},{100 - 16.66 * j}%,{50 + (i + j) * (50 / 12)}%)"',
    "'hsla(' + (360 - 60 * i) + ',' + (100 - 16.66 * j) + '%,50%,' + (1 - 0.16 * j) + ')'": 'f"hsla({360 - 60 * i},{100 - 16.66 * j}%,50%,{1 - 0.16 * j})"',
    "'rgb(' + math.floor(255 - 42.5 * i) + ',' + math.floor(255 - 42.5 * j) + ',0)'": 'f"rgb({math.floor(255 - 42.5 * i)},{math.floor(255 - 42.5 * j)},0)"',
    "'rgb(' + math.floor(255 - 42.5 * i) + ',' +\n                       math.floor(255 - 42.5 * j) + ',0)'": 'f"rgb({math.floor(255 - 42.5 * i)},{math.floor(255 - 42.5 * j)},0)"',
    "'rgb(0,' + math.floor(255 - 42.5 * i) + ',' +\n                       math.floor(255 - 42.5 * j) + ')'": 'f"rgb(0,{math.floor(255 - 42.5 * i)},{math.floor(255 - 42.5 * j)})"',
    "i++": "i += 1",
    "img.onload = function () :": "def img_onload():",
    "img1.onload = function () :": "def img1_onload():",
    "img2.onload = function () :": "def img2_onload():",
    "img.onerror = function () :": "def img_onerror():",
    "line = function (lineDash, color) :": "def line(lineDash, color=None):",
    """line((function () :
    ctx.setLineDash([8])
    a = ctx.getLineDash()
    a[0] -= 3
    a.push(20)
    return a
  })(), 'orange')""": """def inner1():
    ctx.setLineDash([8])
    a = ctx.getLineDash()
    a[0] -= 3
    a.push(20)
    return a
  line(inner1(), 'orange')
""",
    "!Canvas": "False",
    "img.onerror": "# img.onerror",
    "img1.onerror": "# img1.onerror",
    "img2.onerror": "# img2.onerror",
    "loaded1, loaded2": "loaded1, loaded2 = False, False",
    "img.crossOrigin": "# img.crossOrigin",
    'src.replace(/>$/m, """ width="${w}" height="${h}">""")': """re.sub(r'>$', f' width="{w}" height="{h}">', src, count=1, flags=re.MULTILINE)""",
    "    {width, height} = ctx.canvas": "width, height = ctx.canvas.width, ctx.canvas.height",
    "    size = 200": "size = 200",
    "if (data instanceof Uint8ClampedArray) :": "if isinstance(data, bytearray):",
    "a.push(20)": "a.append(20)",
    "{ offset: [10,10], blur: 9 }": "offset=(10,10), blur=9",
    "{scl: 1, offset: 25, len: 65}": "scl=1, offset=25, len=65",
    "{scl: 1.5, offset: 20, len: 65}": "scl=1.5, offset=20, len=65",
    "{sz = 200, sp = 50, x = sp, y = sp, scl = 0.25} = {}": "sz = 200, sp = 50, x = sp, y = sp, scl = 0.25",
    "!(": "not (",
    "data[i + 0] * 0.2": "int(data[i + 0] * 0.2)",
    "data[i + 1] * 0.2": "int(data[i + 1] * 0.2)",
    "data[i + 2] * 0.2": "int(data[i + 2] * 0.2)",
    "    ctx.setLineDash(lineDash)": "    nonlocal y\n    ctx.setLineDash(lineDash)",
    "(i == 1 ? 1 : 0.25)": "(1 if i == 1 else 0.25)",
    "not (i % 3) ? sp : (x / scl + sz + sp)": "sp if not (i % 3) else (x / scl + sz + sp)",
}

prefix = """from __future__ import annotations

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
    return urllib.parse.quote(s, safe='-_.!~*\'()')


def register(name: str):
    def _wrap(fn):
        tests[name] = fn
        return fn

    return _wrap


def imageSrc(filename: str) -> str:
    return str(ASSETS_DIR / filename)


def frange(start, stop=None, step=1.0):
    \"""Float version of range.\"""
    if stop is None:
        stop = start
        start = 0.0
    x = float(start)
    while (step > 0 and x < stop) or (step < 0 and x > stop):
        yield x
        x += step

# region tests
"""
suffix = "# endregion\n"


def remove_multi_line_comments(code: str) -> str:
    result = []
    in_comment = False
    for line in code.splitlines():
        stripped_line = line.strip()
        if stripped_line.startswith("/*"):
            in_comment = not stripped_line.endswith("*/")
            continue
        if stripped_line.endswith("*/"):
            in_comment = False
            continue
        if not in_comment:
            result.append(line)
    return "\n".join(result)


def convert_test_line(line: str) -> str:
    """Convert
    tests['transform() with DOMMatrix'] = function (ctx) {
    To
    @register("transform() with DOMMatrix")
    def transform_with_DOMMatrix(ctx):

    """
    line = line.rstrip()
    left_idx = line.index("[")
    right_idx = line.index("]")
    test_msg = line[left_idx + 2 : right_idx - 1]
    entire_mapping = {
        r"fillStyle=\'hsla(...)\'": "fillStyle_hsla",
        r"fillStyle=\'hsl(...)\'": "fillStyle_hsl",
    }
    test_name = test_msg
    if test_name in entire_mapping:
        test_name = entire_mapping[test_name]
    else:
        buf = ["fn_"]  # 增加前缀，避免数字开头的函数名
        for c in test_name:
            if c.isidentifier() or c.isdigit():
                buf.append(c)
            else:
                buf.append("_")
        test_name = "".join(buf)
    paren_idx = line.rindex("(")
    line = line[paren_idx:-1] + ":"
    line = f'@register("{test_msg}")\ndef {test_name}{line}'
    return line


def get_leading_spaces(line: str) -> str:
    return line[: len(line) - len(line.lstrip())]


def main():
    output = dir / "output.py"
    code = tests_js.read_text(encoding="utf-8")
    idx = code.index("tests[")
    test_code = code[idx:]
    test_code = remove_multi_line_comments(test_code)
    for old, new in replace_mapping.items():
        test_code = test_code.replace(old, new)

    tests_sign_count = 0
    buf = [prefix]
    for line in test_code.splitlines():
        if line.strip().startswith("function"):
            line = line.replace("function", "def", 1)
            line = line[:-1] + ":"
        elif line.startswith("tests["):
            line = convert_test_line(line)
            tests_sign_count += 1
        elif line.rstrip().endswith("{"):
            line = line.rstrip()[:-1] + ":"
        elif line.strip() in {"}", "};", "//", "x"}:
            continue
        elif line.strip().startswith("#") and line.strip().endswith("}"):
            line = line.rstrip()[:-1]
        elif line.strip() == "else":
            line = line.rstrip() + ":"
        elif line.strip().startswith("if") and (line.strip().endswith(")")):
            line = line.rstrip() + ":"
        elif line.strip().endswith(";"):
            line = line.rstrip()[:-1]
        elif line.rstrip().endswith("(),"):
            line = line.rstrip()[:-1]
        buf.append(line)
    buf.append(suffix)
    test_code = "\n".join(buf)

    for old, new in snippet_mapping.items():
        test_code = test_code.replace(old, new)

    output.write_text(test_code, encoding="utf-8")
    print(f"Extracted {tests_sign_count} tests to {output}")


if __name__ == "__main__":
    main()
