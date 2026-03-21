from __future__ import annotations

import base64
import math
from pathlib import Path

import pytest

from skia_canvas_pyr import Canvas, Image

BLACK = (0, 0, 0, 255)
WHITE = (255, 255, 255, 255)
CLEAR = (0, 0, 0, 0)

MAGIC = {
    "jpg": bytes([0xFF, 0xD8, 0xFF]),
    "png": bytes([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A]),
    "webp": bytes([0x52, 0x49, 0x46, 0x46]),
    "pdf": bytes([0x25, 0x50, 0x44, 0x46, 0x2D]),
    "svg": b"<?xml version",
}

MIME = {
    "png": "image/png",
    "jpg": "image/jpeg",
    "webp": "image/webp",
    "pdf": "application/pdf",
    "svg": "image/svg+xml",
}

WIDTH = 512
HEIGHT = 512


def pixel(ctx, x: int, y: int) -> tuple[int, int, int, int]:
    data = ctx.getImageData(x, y, 1, 1).data
    return tuple(data[:4])


def tmp_files(tmp_path: Path) -> list[Path]:
    return sorted(path for path in tmp_path.iterdir() if path.is_file())


def header(path: Path, size: int) -> bytes:
    return path.read_bytes()[:size]


def draw_sample(ctx) -> None:
    ctx.fillStyle = "red"
    ctx.arc(100, 100, 25, 0, math.pi / 2)
    ctx.fill()


@pytest.fixture
def canvas_ctx():
    canvas = Canvas(WIDTH, HEIGHT)
    ctx = canvas.getContext("2d")
    return canvas, ctx


class TestCanvasState:
    def test_width_and_height(self, canvas_ctx):
        canvas, ctx = canvas_ctx

        assert canvas.width == WIDTH
        assert canvas.height == HEIGHT

        ctx.fillStyle = "white"
        ctx.fillRect(0, 0, WIDTH, HEIGHT)
        assert ctx.fillStyle == "#ffffff"
        assert pixel(ctx, 0, 0) == WHITE

        canvas.width = 123
        canvas.height = 456
        assert canvas.width == 123
        assert canvas.height == 456
        assert ctx.fillStyle == "#000000"
        assert pixel(ctx, 0, 0) == CLEAR

    def test_initial_dimensions(self):
        c = Canvas(0, 0)
        assert c.width == 0
        assert c.height == 0

        c = Canvas(-99, 123)
        assert c.width == 300
        assert c.height == 123

        c = Canvas(123, -456)
        assert c.width == 123
        assert c.height == 150

        with pytest.raises(TypeError):
            Canvas()  # type: ignore[call-arg]

        with pytest.raises(TypeError):
            Canvas(456)  # type: ignore[call-arg]

        with pytest.raises(TypeError):
            Canvas(None, 789)  # type: ignore[arg-type]

        with pytest.raises(TypeError):
            Canvas("garbage", math.nan)  # type: ignore[arg-type]

    def test_new_page_dimensions(self, canvas_ctx):
        canvas, _ = canvas_ctx

        assert canvas.width == WIDTH
        assert canvas.height == HEIGHT
        assert len(canvas.pages) == 1
        assert canvas.getContext("2d") is not None
        assert len(canvas.pages) == 1

        canvas.newPage()
        assert len(canvas.pages) == 2

        c = Canvas(123, 456)
        assert c.width == 123
        assert c.height == 456
        assert len(c.pages) == 0

        page = c.newPage().canvas
        assert page is not None
        assert len(c.pages) == 1
        assert c.getContext("2d") is not None
        assert len(c.pages) == 1
        assert page.width == 123
        assert page.height == 456

        with pytest.raises(ValueError, match="not enough values to unpack"):
            c.newPage(987)

        page = c.newPage(math.nan, math.nan).canvas
        assert page is not None
        assert page.width == 300
        assert page.height == 150


class TestCanvasExport:
    def test_export_file_formats_errors(self, canvas_ctx, tmp_path: Path):
        canvas, _ = canvas_ctx

        with pytest.raises(ValueError, match="Unsupported file format"):
            canvas.toFileSync(str(tmp_path / "output.gif"))

        with pytest.raises(ValueError, match="Unsupported file format"):
            canvas.toFileSync(str(tmp_path / "output.targa"))

        with pytest.raises(ValueError, match="Cannot determine image format"):
            canvas.toFileSync(str(tmp_path / "output"))

        with pytest.raises(ValueError, match="Cannot determine image format"):
            canvas.toFileSync(str(tmp_path))

        canvas.toFileSync(str(tmp_path / "output"), {"format": "png"})
        assert (tmp_path / "output").exists()

    @pytest.mark.parametrize(
        ("targets", "expected_ext"),
        [
            (
                [
                    "output1.jpg",
                    "output2.jpeg",
                    ("output3", {"format": "jpg"}),
                    ("output4.png", {"format": "jpeg"}),
                ],
                "jpg",
            ),
            (
                [
                    "output1.png",
                    "output2.PNG",
                    ("output3", {"format": "png"}),
                    ("output4.svg", {"format": "png"}),
                ],
                "png",
            ),
            (
                [
                    "output1.webp",
                    "output2.WEBP",
                    ("output3", {"format": "webp"}),
                    ("output4.svg", {"format": "webp"}),
                ],
                "webp",
            ),
            (
                [
                    "output1.pdf",
                    "output2.PDF",
                    ("output3", {"format": "pdf"}),
                    ("output4.jpg", {"format": "pdf"}),
                ],
                "pdf",
            ),
        ],
    )
    def test_export_binary_formats(
        self, canvas_ctx, tmp_path: Path, targets, expected_ext: str
    ):
        canvas, ctx = canvas_ctx
        draw_sample(ctx)

        for target in targets:
            if isinstance(target, tuple):
                filename, options = target
                canvas.toFileSync(str(tmp_path / filename), options)
            else:
                canvas.toFileSync(str(tmp_path / target))

        magic = MAGIC[expected_ext]
        for path in tmp_files(tmp_path):
            assert header(path, len(magic)) == magic

    def test_export_svgs(self, canvas_ctx, tmp_path: Path):
        canvas, ctx = canvas_ctx
        draw_sample(ctx)

        canvas.toFileSync(str(tmp_path / "output1.svg"))
        canvas.toFileSync(str(tmp_path / "output2.SVG"))
        canvas.toFileSync(str(tmp_path / "output3"), {"format": "svg"})
        canvas.toFileSync(str(tmp_path / "output4.jpeg"), {"format": "svg"})

        for path in tmp_files(tmp_path):
            assert path.read_text(encoding="utf-8").startswith("<?xml version")

    def test_raw_pixel_buffers(self, canvas_ctx):
        canvas, ctx = canvas_ctx
        canvas.width = 4
        canvas.height = 4
        ctx.fillStyle = "#f00"
        ctx.fillRect(0, 0, 1, 1)
        ctx.fillStyle = "#0f0"
        ctx.fillRect(1, 0, 1, 1)
        ctx.fillStyle = "#00f"
        ctx.fillRect(0, 1, 1, 1)
        ctx.fillStyle = "#fff"
        ctx.fillRect(1, 1, 1, 1)

        rgba = list(ctx.getImageData(0, 0, 2, 2).data)
        # fmt: off
        assert rgba == [
            255, 0,   0,   255,
            0,   255, 0,   255,
            0,   0,   255, 255,
            255, 255, 255, 255,
        ]
        # fmt: on

        bgra = list(ctx.getImageData(0, 0, 2, 2, {"color_type": "bgra"}).data)
        # fmt: off
        assert bgra == [
            0,   0,   255, 255,
            0,   255, 0,   255,
            255, 0,   0,   255,
            255, 255, 255, 255,
        ]
        # fmt: on

    def test_image_sequences(self, canvas_ctx, tmp_path: Path):
        canvas, ctx = canvas_ctx
        colors = ["orange", "yellow", "green", "skyblue", "purple"]

        for i, color in enumerate(colors):
            dim = 512 + 100 * i
            ctx = canvas.newPage(dim, dim) if i else canvas.newPage()
            ctx.fillStyle = color
            ctx.arc(100, 100, 25, 0, math.pi + math.pi / len(colors) * (i + 1))
            ctx.fill()
            assert ctx.canvas.width == dim
            assert ctx.canvas.height == dim

        canvas.toFileSync(str(tmp_path / "output-{2}.png"))

        files = tmp_files(tmp_path)
        assert len(files) == len(colors) + 1

        for i, path in enumerate(files):
            img = Image(path.read_bytes())
            assert img.complete is True
            dim = 512 if i < 2 else 512 + 100 * (i - 1)
            assert img.width == dim
            assert img.height == dim

    def test_multi_page_pdf(self, canvas_ctx, tmp_path: Path):
        canvas, _ = canvas_ctx
        colors = ["orange", "yellow", "green", "skyblue", "purple"]

        for i, color in enumerate(colors):
            ctx = canvas.newPage()
            ctx.fillStyle = color
            ctx.fillRect(0, 0, canvas.width, canvas.height)
            ctx.fillStyle = "white"
            ctx.textAlign = "center"
            ctx.fillText(str(i + 1), canvas.width / 2, canvas.height / 2)

        path = tmp_path / "multipage.pdf"
        canvas.toFileSync(str(path))
        assert header(path, len(MAGIC["pdf"])) == MAGIC["pdf"]

    def test_image_buffers(self, canvas_ctx, tmp_path: Path):
        canvas, ctx = canvas_ctx
        draw_sample(ctx)

        for ext in ["png", "jpg", "pdf", "svg"]:
            path = tmp_path / f"output.{ext}"
            buf = canvas.toBufferSync(ext)
            assert isinstance(buf, bytes)
            path.write_bytes(buf)
            assert header(path, len(MAGIC[ext])) == MAGIC[ext]

            by_mime = tmp_path / f"bymime.{ext}"
            buf = canvas.toBufferSync(MIME[ext])
            assert isinstance(buf, bytes)
            by_mime.write_bytes(buf)
            assert header(by_mime, len(MAGIC[ext])) == MAGIC[ext]

    def test_data_urls(self, canvas_ctx):
        canvas, ctx = canvas_ctx
        draw_sample(ctx)

        for ext, mime in MIME.items():
            magic = MAGIC[ext]
            ext_url = canvas.toURLSync(ext)
            mime_url = canvas.toURLSync(mime)
            std_url = canvas.toDataURL(mime, 0.92)
            header_prefix = f"data:{mime};base64,"
            data = base64.b64decode(ext_url[len(header_prefix) :])

            assert ext_url == mime_url
            assert ext_url == std_url
            assert ext_url.startswith(header_prefix)
            assert data[: len(magic)] == magic

    def test_sensible_error_messages(self, canvas_ctx, tmp_path: Path):
        canvas, ctx = canvas_ctx
        ctx.fillStyle = "lightskyblue"
        ctx.fillRect(0, 0, canvas.width, canvas.height)

        with pytest.raises(RuntimeError):
            canvas.toFileSync(
                str(tmp_path / "deep" / "path" / "that" / "doesn" / "not" / "exist.pdf")
            )

        canvas.width = 0
        canvas.height = 128
        assert canvas.width == 0
        assert canvas.height == 128
        with pytest.raises(RuntimeError, match="non-zero"):
            canvas.toFileSync(str(tmp_path / "zeroed.png"))

    def test_can_export_without_existing_context(self):
        canvas = Canvas(200, 200)
        assert canvas.toURLSync("png").startswith("data:image/png;base64,")
