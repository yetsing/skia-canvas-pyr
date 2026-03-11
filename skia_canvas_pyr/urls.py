import re
import base64
from urllib import parse, request
from urllib.parse import ParseResult
from pathlib import Path
from typing import Any


def fetch_url(url: str) -> bytes:
    with request.urlopen(url) as response:
        return response.read()


def decode_data_url(data_url: str) -> bytes:
    """
    Decode a data: URL and return the raw bytes.

    Raises:
      TypeError: if data_url is not a str
      ValueError: if data_url is not a valid data URL or decoding fails
    """
    if not isinstance(data_url, str):
        raise TypeError(f"Expected a data URL string (got {type(data_url).__name__})")

    s = data_url.lstrip()
    if not s.lower().startswith("data:"):
        raise ValueError(f'Expected a data URL string (got: "{data_url}")')

    # split header and content at first comma
    comma = s.find(",")
    if comma == -1:
        raise ValueError(f'Expected a valid data URL string (got: "{data_url}")')

    header = s[5:comma]  # part after "data:" up to the comma
    content = s[comma + 1 :]

    # header: <mediatype>(;param)*  e.g. "image/svg+xml;charset=utf-8;base64"
    if header == "":
        # permissive: no mediatype/params
        parts = []
        mediatype = ""
        params = []
    else:
        parts = header.split(";")
        mediatype = parts[0]
        params = parts[1:]

    # determine if base64 encoding is specified
    is_base64 = any(p.lower() == "base64" for p in params)

    try:
        if is_base64:
            # base64 content
            # strip whitespace/newlines which are sometimes present
            b = base64.b64decode(content.strip(), validate=True)
            return b
        else:
            # percent-decoded bytes (e.g. for non-base64 data URLs such as SVG)
            # urllib.parse.unquote_to_bytes handles percent-encoding to bytes
            return parse.unquote_to_bytes(content)
    except Exception as exc:
        raise ValueError(f"Failed to decode data URL: {exc}") from exc


def expand_url(src: Any) -> str:
    """
    Convert a URL-like object to a string or file path:
      - If src is a pathlib.Path -> return its string path
      - If src is a ParseResult (from urllib.parse.urlparse()):
          * file: -> return local filesystem path
          * http:, https:, data: -> return the full URL string
          * otherwise -> raise ValueError
      - If src is a string -> return it unchanged

    Note: This mirrors the JS behavior that specially handles URL objects.
    """
    # pathlib.Path => file system path string
    if isinstance(src, Path):
        return str(src)

    # urllib.parse.ParseResult => inspect scheme
    if isinstance(src, ParseResult):
        scheme = (src.scheme or "").lower()
        if scheme == "file":
            # Convert percent-encoded path to local filesystem path
            # url2pathname handles Windows <-> URL path conversions
            return request.url2pathname(parse.unquote(src.path))
        if scheme in ("http", "https", "data"):
            return src.geturl()
        raise ValueError(f"Unsupported protocol: {scheme or '<empty>'}")

    return src


if __name__ == "__main__":
    # small usage examples / smoke tests

    # decode base64 data URL
    b64 = "data:text/plain;base64,SGVsbG8sIHdvcmxkIQ=="
    print(decode_data_url(b64))  # b'Hello, world!'

    # decode percent-encoded (e.g. SVG often not base64)
    svg = "data:image/svg+xml;charset=utf-8,%3Csvg%20xmlns='http://www.w3.org/2000/svg'%3E%3C/svg%3E"
    print(decode_data_url(svg))  # bytes of the SVG

    # expand_url examples
    from urllib.parse import urlparse

    print(expand_url("https://example.com/foo"))  # same string
    pr = urlparse("file:///tmp/test.txt")
    print(expand_url(pr))  # '/tmp/test.txt' (on POSIX)
    print(expand_url(Path("/tmp/abc.txt")))  # '/tmp/abc.txt'
