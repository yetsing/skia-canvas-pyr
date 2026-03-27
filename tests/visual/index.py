from __future__ import annotations

import argparse
import inspect
import json
import mimetypes
import re
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer, HTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from skia_canvas_pyr import Canvas

from tests import tests  # type: ignore

BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR.parent / "assets"
INDEX_HTML = BASE_DIR / "index.html"
TESTS_JS = BASE_DIR / "tests.js"

DEFAULTS = {
    "width": 200,
    "height": 200,
    "cc": "#FFFFFF",
    "bc": None,
    "gpu": None,
}

MIME = {
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "webp": "image/webp",
    "pdf": "application/pdf",
    "svg": "image/svg+xml",
}


PORT = 4000


def _parse_argv():
    global PORT

    parser = argparse.ArgumentParser(
        description="Visual test server for skia_canvas_pyr"
    )
    parser.add_argument("positional_port", nargs="?", default=None)
    parser.add_argument("-p", "--port", dest="port", type=int, default=None)
    parser.add_argument(
        "-g", "--gpu", dest="gpu", type=int, choices=[0, 1], default=None
    )
    parser.add_argument("-w", "--width", dest="width", type=int, default=None)
    parser.add_argument("-t", "--height", dest="height", type=int, default=None)
    parser.add_argument("-c", "--cc", dest="cc", default=None)
    parser.add_argument("-b", "--bc", dest="bc", default=None)
    args, unknown = parser.parse_known_args()

    if args.positional_port and str(args.positional_port).isdigit():
        PORT = int(args.positional_port)

    if args.port is not None:
        PORT = args.port
    if args.gpu is not None:
        DEFAULTS["gpu"] = bool(args.gpu)
    if args.width is not None:
        DEFAULTS["width"] = args.width
    if args.height is not None:
        DEFAULTS["height"] = args.height
    if args.cc is not None:
        DEFAULTS["cc"] = args.cc
    if args.bc is not None:
        DEFAULTS["bc"] = args.bc

    for arg in unknown:
        if re.match(r"^-?", arg):
            print(f"Ignoring unknown argument: {arg}")


def _as_int(value: str | None, fallback: int) -> int:
    try:
        if value is None:
            return fallback
        return int(value)
    except (TypeError, ValueError):
        return fallback


def _as_gpu(value: str | None):
    if value is None or value == "null":
        return None
    return bool(_as_int(value, 0))


def _render_opts(params: dict[str, list[str]]) -> dict:
    opts: dict[str, Any] = {
        "width": _as_int(params.get("width", [None])[0], DEFAULTS["width"]),
        "height": _as_int(params.get("height", [None])[0], DEFAULTS["height"]),
        "cc": params.get("cc", [DEFAULTS["cc"]])[0] or DEFAULTS["cc"],
        "bc": params.get("bc", [DEFAULTS["bc"]])[0],
        "gpu": _as_gpu(params.get("gpu", [None])[0]),
    }

    alpha = params.get("alpha", [None])[0]
    if (
        alpha is not None
        and isinstance(opts["cc"], str)
        and len(opts["cc"]) == 7
        and opts["cc"].startswith("#")
    ):
        try:
            a = round(255 * float(alpha))
            a = max(min(a, 255), 0)
            opts["cc"] = f"{opts['cc']}{a:02x}"
        except ValueError:
            pass

    opts["bc_default"] = params.get("bc_default", [None])[0] is not None
    return opts


def _parse_cookie(cookie_header: str | None) -> dict[str, str]:
    if not cookie_header:
        return {}
    result: dict[str, str] = {}
    for pair in cookie_header.split(";"):
        if "=" not in pair:
            continue
        key, value = pair.split("=", 1)
        result[key.strip()] = value.strip()
    return result


def _cookie_opts(cookie_header: str | None) -> dict:
    cookies = _parse_cookie(cookie_header)
    raw = cookies.get("renderOptions")
    if not raw:
        return dict(DEFAULTS)
    try:
        parsed = json.loads(raw)
        opts = dict(DEFAULTS)
        opts.update(parsed)
        return opts
    except json.JSONDecodeError:
        return dict(DEFAULTS)


def _run_test(canvas: Canvas, name: str, opts: dict, fmt: str) -> bytes:
    if name not in tests:
        raise KeyError(f"Unknown test: {name}")

    if opts.get("gpu") is not None:
        try:
            canvas.gpu = bool(opts["gpu"])
        except Exception:
            pass

    ctx = canvas.getContext("2d")
    initial_fill = ctx.fillStyle
    ctx.fillStyle = opts["cc"]
    ctx.fillRect(0, 0, canvas.width, canvas.height)
    ctx.fillStyle = initial_fill
    ctx.imageSmoothingEnabled = True

    fn = tests[name]
    param_count = len(inspect.signature(fn).parameters)
    if param_count >= 2:
        fn(ctx, lambda *_args, **_kwargs: None)
    else:
        fn(ctx)

    return canvas.toBufferSync(fmt)


class VisualHandler(BaseHTTPRequestHandler):
    server_version = "SkiaCanvasVisual/1.0"
    log_request_code = 400

    def _send_bytes(
        self,
        body: bytes,
        content_type: str,
        status: int = HTTPStatus.OK,
        extra_headers: dict[str, str] | None = None,
    ) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        if extra_headers:
            for key, value in extra_headers.items():
                self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)

    def _send_text(
        self,
        text: str,
        content_type: str,
        status: int = HTTPStatus.OK,
        extra_headers: dict[str, str] | None = None,
    ) -> None:
        self._send_bytes(text.encode("utf-8"), content_type, status, extra_headers)

    def _send_json(self, payload: dict, status: int = HTTPStatus.OK) -> None:
        self._send_text(json.dumps(payload), "application/json; charset=utf-8", status)

    def _serve_static(self, path: Path) -> None:
        if not path.exists() or not path.is_file():
            self._send_text(
                "Not Found", "text/plain; charset=utf-8", HTTPStatus.NOT_FOUND
            )
            return

        content_type, _ = mimetypes.guess_type(path.name)
        self._send_bytes(path.read_bytes(), content_type or "application/octet-stream")

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        req_path = parsed.path
        params = parse_qs(parsed.query)

        if req_path == "/":
            if not params:
                cookie_value = json.dumps(DEFAULTS, separators=(",", ":"))
            else:
                cookie_value = json.dumps(_render_opts(params), separators=(",", ":"))

            body = INDEX_HTML.read_bytes()
            self._send_bytes(
                body,
                "text/html; charset=utf-8",
                extra_headers={"Set-Cookie": f"renderOptions={cookie_value}; Path=/"},
            )
            return

        if req_path == "/tests.js":
            self._serve_static(TESTS_JS)
            return

        if req_path == "/tests.py":
            self._serve_static(BASE_DIR / "tests.py")
            return

        if (
            req_path.startswith("/")
            and req_path.count("/") == 1
            and req_path[1:] in MIME
        ):
            fmt = req_path[1:]
            name = params.get("name", [None])[0]
            if not name:
                self._send_json(
                    {"error": "Missing query parameter: name"}, HTTPStatus.BAD_REQUEST
                )
                return

            opts = _cookie_opts(self.headers.get("Cookie"))
            canvas = Canvas(opts["width"], opts["height"])
            try:
                data = _run_test(canvas, name, opts, fmt)
            except KeyError as err:
                print(f"KeyError: {err}")
                self._send_json({"error": str(err)}, HTTPStatus.BAD_REQUEST)
                return
            except Exception as err:
                import traceback

                traceback.print_exc()
                self._send_json({"error": str(err)}, HTTPStatus.INTERNAL_SERVER_ERROR)
                return

            self._send_bytes(data, MIME[fmt])
            return

        # static assets passthrough for index.html references
        rel = req_path.lstrip("/")
        asset = ASSETS_DIR / rel
        if asset.exists() and asset.is_file():
            self._serve_static(asset)
            return

        self._send_text("Not Found", "text/plain; charset=utf-8", HTTPStatus.NOT_FOUND)

    def log_request(self, code="-", size="-"):
        """Log an accepted request.

        This is called by send_response().

        """
        if isinstance(code, HTTPStatus):
            code = code.value
        is_output = not (isinstance(code, int) and code <= self.log_request_code)
        if not is_output:
            return
        self.log_message('"%s" %s %s', self.requestline, str(code), str(size))


def main() -> None:
    _parse_argv()
    server = HTTPServer(("127.0.0.1", PORT), VisualHandler)
    print(f"=> http://localhost:{PORT}/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
