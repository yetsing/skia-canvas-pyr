# canvas_pyr

[![image](https://img.shields.io/pypi/v/skia-canvas-pyr.svg)](https://pypi.python.org/pypi/skia-canvas-pyr)
[![image](https://img.shields.io/pypi/l/skia-canvas-pyr.svg)](https://pypi.python.org/pypi/skia-canvas-pyr)
[![image](https://img.shields.io/pypi/pyversions/skia-canvas-pyr.svg)](https://pypi.python.org/pypi/skia-canvas-pyr)
[![Actions status](https://github.com/yetsing/skia-canvas-pyr/actions/workflows/CI.yml/badge.svg)](https://github.com/yetsing/skia-canvas-pyr/actions)

A Python canvas library powered by Skia, with bindings implemented in Rust.

Support Python3.10+.

文档参考 [skia-canvas](http://skia-canvas.org/api) ，除了一些 JS 特性， API 基本一致。

## Installation

```shell
pip install skia-canvas-pyr
```

## Example Usage

### Generating image files

```python
import math
from skia_canvas_pyr import Canvas

canvas = Canvas(400, 400)
ctx = canvas.getContext("2d")
width = canvas.width
height = canvas.height

sweep = ctx.createConicGradient(math.pi * 1.2, width/2, height/2)
sweep.addColorStop(0, "red")
sweep.addColorStop(0.25, "orange")
sweep.addColorStop(0.5, "yellow")
sweep.addColorStop(0.75, "green")
sweep.addColorStop(1, "red")
ctx.strokeStyle = sweep
ctx.lineWidth = 100
ctx.strokeRect(100,100, 200,200)

# ...or save the file synchronously from the main thread
canvas.toFileSync("rainbox.png", {"density": 2})
```

### Multi-page sequences

```python
import math
from skia_canvas_pyr import Canvas

canvas = Canvas(400, 400)
ctx = canvas.getContext("2d")
width, height = canvas.width, canvas.height

for color in ['orange', 'yellow', 'green', 'skyblue', 'purple']:
  ctx = canvas.newPage()
  ctx.fillStyle = color
  ctx.fillRect(0,0, width, height)
  ctx.fillStyle = 'white'
  ctx.arc(width/2, height/2, 40, 0, 2 * math.pi)
  ctx.fill()

# save to a multi-page PDF file
canvas.toFileSync("all-pages.pdf")

# save to files named `page-01.png`, `page-02.png`, etc.
canvas.toFileSync("page-{2}.png")
```

### Rendering to a window

```python
import math
from skia_canvas_pyr import Window, WindowEvent, App

win = Window(300, 300)
win.title = "Canvas Window"

@win.on(WindowEvent.draw)
def draw(e):
  ctx = e.target.canvas.getContext("2d")
  ctx.lineWidth = 25 + 25 * math.cos(e.frame / 10)
  ctx.beginPath()
  ctx.arc(150, 150, 50, 0, 2 * math.pi)
  ctx.stroke()

  ctx.beginPath()
  ctx.arc(150, 150, 10, 0, 2 * math.pi)
  ctx.stroke()
  ctx.fill()

App.run()
```

## 来源与致谢

本项目的核心源自 [samizdatco/skia-canvas](https://github.com/samizdatco/skia-canvas)，在此基础上，使用 [PyO3](https://pyo3.rs/) 使其能够作为 Python 扩展模块使用。
