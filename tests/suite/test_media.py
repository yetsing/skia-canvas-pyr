from __future__ import annotations

import base64
from pathlib import Path
from typing import Any, cast
from urllib.parse import urlparse

import pytest

import skia_canvas_pyr.classes.imagery as imagery
from skia_canvas_pyr import (
    Canvas,
    FontLibrary,
    Image,
    ImageData,
    loadImage,
    loadImageData,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
ASSETS_DIR = REPO_ROOT / "tests" / "assets"

pytestmark = pytest.mark.skipif(
    not ASSETS_DIR.exists(),
    reason="tests/assets is missing; run tests/pretest.py first",
)

PNG_PATH = ASSETS_DIR / "pentagon.png"
SVG_PATH = ASSETS_DIR / "image" / "format.svg"
FORMAT_BASE = ASSETS_DIR / "image" / "format"
RAW_PATH = ASSETS_DIR / "image" / "format.raw"
FONTS_DIR = ASSETS_DIR / "fonts"

URI = f"http://_h_o_s_t_/{PNG_PATH.relative_to(REPO_ROOT).as_posix()}"
SVG_URI = f"http://_h_o_s_t_/{SVG_PATH.relative_to(REPO_ROOT).as_posix()}"

PNG_BUFFER = PNG_PATH.read_bytes() if PNG_PATH.exists() else b""
SVG_BUFFER = SVG_PATH.read_bytes() if SVG_PATH.exists() else b""
PNG_DATA_URI = f"data:image/png;base64,{base64.b64encode(PNG_BUFFER).decode()}"
SVG_DATA_URI = f"data:image/svg+xml;base64,{base64.b64encode(SVG_BUFFER).decode()}"

PNG_FILE_URL = PNG_PATH.resolve().as_uri()
SVG_FILE_URL = SVG_PATH.resolve().as_uri()

FRESH = {"complete": False, "width": 0, "height": 0}
LOADED = {"complete": True, "width": 125, "height": 125}
PARSED = {"complete": True, "width": 60, "height": 60}


def _matches(img: Image, complete: bool, width: int, height: int) -> None:
    assert img.complete is complete
    assert int(img.width) == width
    assert int(img.height) == height


def _as_data_uri(path: Path) -> str:
    ext = path.suffix.lstrip(".").lower().replace("jpg", "jpeg")
    mime = f"image/{ext if ext != 'svg' else 'svg+xml'}"
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode()}"


def _pixel(ctx, x: int, y: int) -> tuple[int, int, int, int]:
    data = ctx.getImageData(x, y, 1, 1).data
    return tuple(data[:4])


@pytest.fixture(autouse=True)
def fake_http(monkeypatch: pytest.MonkeyPatch):
    def _fake_fetch(url: str) -> bytes:
        prefix = "http://_h_o_s_t_/"
        if not url.startswith(prefix):
            raise RuntimeError(f"Unexpected URL in test: {url}")

        rel_path = url[len(prefix) :]
        local = REPO_ROOT / rel_path
        if local.exists():
            return local.read_bytes()
        raise RuntimeError(f'Failed to load image from "/{rel_path}" (HTTP error 404)')

    monkeypatch.setattr(imagery, "fetch_url", _fake_fetch)


@pytest.fixture
def img() -> Image:
    return Image()


class TestImage:
    def test_bitmap_from_buffer(self, img: Image):
        img = Image(PNG_BUFFER)
        _matches(img, **LOADED)
        assert img.src == "<bytes>"

        fake_src = "arbitrary*src*string"
        img = Image(PNG_BUFFER, fake_src)
        assert img.src == fake_src

        img = Image()
        img.src = PNG_BUFFER
        _matches(img, **LOADED)

    def test_bitmap_from_data_uri(self, img: Image):
        img.src = PNG_DATA_URI
        _matches(img, **LOADED)

        img = Image(PNG_DATA_URI)
        _matches(img, **LOADED)
        assert img.src == PNG_DATA_URI

        fake_src = "arbitrary*src*string"
        img = Image(PNG_DATA_URI, fake_src)
        assert img.src == fake_src

    def test_bitmap_from_local_file(self, img: Image):
        _matches(img, **FRESH)

        img.src = str(PNG_PATH)
        _matches(img, **LOADED)
        assert img.src == str(PNG_PATH)

        with pytest.raises(ValueError, match="Expected a data URL"):
            Image(str(PNG_PATH))

    def test_bitmap_from_file_url(self, img: Image):
        _matches(img, **FRESH)
        img.src = urlparse(PNG_FILE_URL)
        _matches(img, **LOADED)
        assert img.src == str(PNG_PATH.resolve())

        with pytest.raises(ValueError, match="Expected a data URL"):
            Image(urlparse(PNG_FILE_URL))  # type: ignore

    def test_bitmap_from_http_url(self, img: Image):
        _matches(img, **FRESH)
        img.src = URI
        _matches(img, **LOADED)

        with pytest.raises(ValueError, match="Expected a data URL"):
            Image(URI)

    def test_load_image_call(self):
        loaded = loadImage(URI)
        _matches(loaded, **LOADED)

        loaded = loadImage(PNG_BUFFER)
        _matches(loaded, **LOADED)

        loaded = loadImage(PNG_DATA_URI)
        _matches(loaded, **LOADED)

        loaded = loadImage(str(PNG_PATH))
        _matches(loaded, **LOADED)

        loaded = loadImage(str(SVG_PATH))
        _matches(loaded, **PARSED)

        loaded = loadImage(urlparse(URI))
        _matches(loaded, **LOADED)

        loaded = loadImage(URI)
        _matches(loaded, **LOADED)

        loaded = loadImage(urlparse(PNG_DATA_URI))
        _matches(loaded, **LOADED)

        loaded = loadImage(urlparse(PNG_PATH.resolve().as_uri()))
        _matches(loaded, **LOADED)

        loaded = loadImage(urlparse(SVG_PATH.resolve().as_uri()))
        _matches(loaded, **PARSED)

        with pytest.raises(RuntimeError, match="HTTP error 404"):
            loadImage("http://_h_o_s_t_/nonesuch")

    def test_svg_from_buffer(self, img: Image):
        _matches(img, **FRESH)
        img = Image(SVG_BUFFER)
        _matches(img, **PARSED)

        img = Image()
        img.src = SVG_BUFFER
        _matches(img, **PARSED)

    def test_svg_from_data_uri(self, img: Image):
        _matches(img, **FRESH)
        img.src = SVG_DATA_URI
        _matches(img, **PARSED)

    def test_svg_from_local_file(self, img: Image):
        _matches(img, **FRESH)
        img.src = SVG_PATH
        _matches(img, **PARSED)

    def test_svg_from_file_url(self, img: Image):
        _matches(img, **FRESH)
        img.src = cast(Any, urlparse(SVG_PATH.resolve().as_uri()))
        _matches(img, **PARSED)

    def test_svg_from_http_url(self, img: Image):
        _matches(img, **FRESH)
        img.src = SVG_URI
        _matches(img, **PARSED)

    def test_complete_flag(self, img: Image):
        _matches(img, **FRESH)
        img.src = str(PNG_PATH)
        assert img.complete

    def test_reload_existing_image(self, img: Image):
        _matches(img, **FRESH)

        img.src = URI
        _matches(img, complete=True, width=125, height=125)

        img.src = f"http://_h_o_s_t_/{(ASSETS_DIR / 'image' / 'format.png').relative_to(REPO_ROOT).as_posix()}"
        _matches(img, complete=True, width=60, height=60)

    def test_http_error_raises_on_src_assignment(self, img: Image):
        with pytest.raises(RuntimeError, match="HTTP error 404"):
            img.src = "http://_h_o_s_t_/nonesuch"

    @pytest.mark.parametrize("ext", ["png", "jpg", "gif", "bmp", "ico", "webp", "svg"])
    def test_can_decode_format(self, ext: str):
        path = Path(f"{FORMAT_BASE}.{ext}")

        local = loadImage(str(path))
        _matches(local, complete=True, width=60, height=60)

        data = loadImage(_as_data_uri(path))
        _matches(data, complete=True, width=60, height=60)

        from_buffer = Image(path.read_bytes())
        _matches(from_buffer, complete=True, width=60, height=60)


class TestImageData:
    def test_can_init_from_buffer(self):
        buffer = RAW_PATH.read_bytes()
        img_data = ImageData(buffer, 60, 60)
        assert img_data.width == 60
        assert img_data.height == 60
        assert img_data.colorType == "rgba"

        with pytest.raises(ValueError, match="Buffer size"):
            ImageData(buffer, 60, 59)

    def test_load_image_data_call(self):
        img_data = loadImageData(str(RAW_PATH), 60, 60)
        assert img_data.width == 60
        assert img_data.height == 60
        assert img_data.colorType == "rgba"

    def test_canvas_content(self):
        canvas = Canvas(60, 60)
        ctx = canvas.getContext("2d")

        rgba = ctx.getImageData(0, 0, 60, 60)
        assert rgba.width == 60
        assert rgba.height == 60
        assert rgba.colorType == "rgba"

        bgra = ctx.getImageData(0, 0, 60, 60, {"color_type": "bgra"})
        assert bgra.width == 60
        assert bgra.height == 60
        assert bgra.colorType == "bgra"


class TestFontLibrary:
    @pytest.fixture(autouse=True)
    def _setup(self):
        canvas = Canvas(512, 512)
        ctx = canvas.getContext("2d")
        yield ctx
        FontLibrary.reset()

    def _find_font(self, rel: str) -> str:
        return str(FONTS_DIR / rel)

    def test_can_list_families(self):
        fams = FontLibrary.families
        sorted_fams = sorted(fams)
        unique_fams = sorted(set(fams), key=fams.index)

        assert ("Arial" in fams) or ("DejaVu Sans" in fams)
        assert fams == sorted_fams
        assert fams == unique_fams

    def test_can_check_for_family(self):
        assert FontLibrary.has("Arial") or FontLibrary.has("DejaVu Sans")
        assert not FontLibrary.has("_n_o_n_e_s_u_c_h_")

    def test_can_describe_family(self):
        fam = (
            "Arial"
            if FontLibrary.has("Arial")
            else "DejaVu Sans" if FontLibrary.has("DejaVu Sans") else None
        )
        if fam is None:
            pytest.skip("No baseline family available")

        info = FontLibrary.family(fam)
        assert info is not None
        assert isinstance(info.family, str)
        assert isinstance(info.weights[0], (int, float))
        assert isinstance(info.widths[0], str)
        assert isinstance(info.styles[0], str)

    def test_can_register_fonts(self):
        ttf = self._find_font("AmstelvarAlpha-VF.ttf")
        name = "AmstelvarAlpha"
        alias = "PseudonymousBosch"

        FontLibrary.use(ttf)
        assert FontLibrary.has(name)
        family_info = FontLibrary.family(name)
        assert 400 in (family_info.weights if family_info is not None else [])

        FontLibrary.use(alias, [ttf])
        assert FontLibrary.has(alias)
        alias_info = FontLibrary.family(alias)
        assert 400 in (alias_info.weights if alias_info is not None else [])

        FontLibrary.reset()
        assert not FontLibrary.has(name)
        assert not FontLibrary.has(alias)

    @pytest.mark.parametrize("ext", ["woff", "woff2"])
    def test_can_render_woff_fonts(self, ext: str, _setup):
        ctx = _setup
        woff = self._find_font(f"Monoton-Regular.{ext}")
        name = "Monoton"
        FontLibrary.use(woff)
        assert FontLibrary.has(name)

        ctx.font = "256px Monoton"
        ctx.fillText("G", 128, 256)

        assert _pixel(ctx, 300, 172) == (0, 0, 0, 0)

    def test_can_handle_use_signatures(self):
        amstel = self._find_font("AmstelvarAlpha-VF.ttf")
        monoton = [
            self._find_font("Monoton-Regular.woff"),
            self._find_font("Monoton-Regular.woff2"),
        ]
        montserrat = [
            self._find_font("montserrat-latin/montserrat-v30-latin-200.woff2"),
            self._find_font("montserrat-latin/montserrat-v30-latin-700italic.woff2"),
            self._find_font("montserrat-latin/montserrat-v30-latin-200italic.woff2"),
            self._find_font("montserrat-latin/montserrat-v30-latin-italic.woff2"),
            self._find_font("montserrat-latin/montserrat-v30-latin-700.woff2"),
            self._find_font("montserrat-latin/montserrat-v30-latin-regular.woff2"),
        ]

        assert len(FontLibrary.use([amstel, *monoton])) == 3
        assert len(FontLibrary.use("Montmartre", montserrat)) == 6

        single = FontLibrary.use(
            {"Monaton": [monoton[0]], "Montserrat": [montserrat[0]]}
        )
        assert len(single.get("Monaton", [])) == 1
        assert len(single.get("Montserrat", [])) == 1

        multiple = FontLibrary.use(
            {
                "Monaton": [monoton[1]],
                "Montserrat": montserrat[1:-1],
            }
        )
        assert len(multiple.get("Monaton", [])) == 1
        assert len(multiple.get("Montserrat", [])) == 4
