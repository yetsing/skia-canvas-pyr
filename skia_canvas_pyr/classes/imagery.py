import pathlib
import re

from typing import Tuple, overload, TypedDict

from ..skia_canvas_pyr import Image as ImageRs
from ..urls import fetch_url, decode_data_url, expand_url


def loadImage(src) -> "Image":
    data, img_src = _fetch_data(src)
    return Image(data, img_src)


class Image:
    __slots__ = ("__image",)

    def __init__(self, data: bytes | str, src: str = "") -> None:
        self.__image = ImageRs()

        data = expand_url(data)
        self.__image.set_src(src or "<bytes>")

        if isinstance(data, bytes):
            if not self.__image.set_data(data):
                raise ValueError("Failed to decode image data")
        elif isinstance(data, str):
            b = decode_data_url(data)
            if not self.__image.set_data(b):
                raise ValueError("Failed to decode image data")
            if not src:
                self.__image.set_src(data)
        else:
            raise TypeError(f"Unsupported data type: {type(data).__name__}")

    @property
    def complete(self) -> bool:
        return self.__image.get_complete()

    @property
    def height(self) -> float:
        return self.__image.get_height()

    @property
    def width(self) -> float:
        return self.__image.get_width()

    @property
    def src(self) -> str:
        return self.__image.get_src()

    @src.setter
    def set_src(self, src: str) -> None:
        src = expand_url(src)
        if isinstance(src, str):
            self.__image.set_src(src)
        else:
            self.__image.set_src("")

        data, img_src = _fetch_data(src)
        self.__image.set_src(img_src)
        if not self.__image.set_data(data):
            raise ValueError("Failed to decode image data")

    def __repr__(self) -> str:
        return f"Image(width={self.width}, height={self.height}, complete={self.complete} src='{self.src[:128]}')"

    __str__ = __repr__

    def core(self) -> ImageRs:
        return self.__image


class ColorOption(TypedDict):
    color_type: str
    color_space: str


class ImageData:
    __slots__ = (
        "__color_space",
        "__color_type",
        "__width",
        "__height",
        "__bytes_per_pixel",
        "__data",
    )

    @overload
    def __init__(self, width: int, height: int, /) -> None: ...
    @overload
    def __init__(self, width: int, height: int, option: ColorOption, /) -> None: ...
    @overload
    def __init__(self, buffer: bytes, width: int, /) -> None: ...
    @overload
    def __init__(self, buffer: bytes, width: int, height: int, /) -> None: ...
    @overload
    def __init__(
        self, buffer: bytes, width: int, height: int, option: ColorOption, /
    ) -> None: ...
    @overload
    def __init__(self, image: Image, option: ColorOption, /) -> None: ...
    @overload
    def __init__(self, image_data: "ImageData", /) -> None: ...

    def __init__(self, *args) -> None:
        if isinstance(args[0], ImageData):
            # copy constructor
            other = args[0]
            color_space = other.__color_space
            color_type = other.__color_type
            width = other.__width
            height = other.__height
            bytes_per_pixel = other.__bytes_per_pixel
            data = other.__data[:]
        elif isinstance(args[0], Image):
            # from Image
            image = args[0]
            option = args[1] if len(args) > 1 else {}
            color_space = option.get("colorSpace", "srgb")
            color_type = option.get("colorType", "rgba")
            width = int(image.width)
            height = int(image.height)
            bytes_per_pixel = _pixel_size(color_type)
            data = image.core().pixels(color_type, None)
            data = (
                bytearray(data)
                if data is not None
                else bytearray(width * height * bytes_per_pixel)
            )
        elif isinstance(args[0], bytes):
            data = bytearray(args[0])
            width = int(args[1])
            height = int(args[2]) if len(args) > 2 else 0
            option = args[3] if len(args) > 3 else {}
            color_space = option.get("colorSpace", "srgb")
            color_type = option.get("colorType", "rgba")
            bytes_per_pixel = _pixel_size(color_type)
            if height == 0:
                height = len(data) // (width * bytes_per_pixel)
            if len(data) != width * height * bytes_per_pixel:
                raise ValueError(
                    "Buffer size does not match width, height and color type"
                )
        else:
            width = int(args[0])
            height = int(args[1])
            option = args[2] if len(args) > 2 else {}
            color_space = option.get("colorSpace", "srgb")
            color_type = option.get("colorType", "rgba")
            bytes_per_pixel = _pixel_size(color_type)
            data = bytearray(width * height * bytes_per_pixel)

        if color_space not in ["srgb"]:
            raise ValueError(f"Unsupported color space: {color_space}")
        if width < 0 or height < 0:
            raise ValueError("Width and height must be non-negative")

        self.__color_space: str = color_space
        self.__color_type: str = color_type
        self.__width: int = width
        self.__height: int = height
        self.__bytes_per_pixel: int = bytes_per_pixel
        self.__data: bytearray = data

    @property
    def colorSpace(self) -> str:
        return self.__color_space

    @property
    def colorType(self) -> str:
        return self.__color_type

    @property
    def width(self) -> int:
        return self.__width

    @property
    def height(self) -> int:
        return self.__height

    @property
    def bytesPerPixel(self) -> int:
        return self.__bytes_per_pixel

    @property
    def data(self) -> bytearray:
        return self.__data

    def __repr__(self) -> str:
        return f"ImageData(width={self.width}, height={self.height}, colorType='{self.colorType}', colorSpace='{self.colorSpace}', bytesPerPixel={self.bytesPerPixel}, data=bytearray({len(self.data)} bytes))"

    __str__ = __repr__


def _pixel_size(color_type: str) -> int:
    if color_type in ["Alpha8", "Gray8", "R8UNorm"]:
        return 1
    elif color_type in ["A16Float", "A16UNorm", "ARGB4444", "R8G8UNorm", "RGB565"]:
        return 2
    elif color_type in [
        "rgb",
        "rgba",
        "bgra",
        "BGR101010x",
        "BGRA1010102",
        "BGRA8888",
        "R16G16Float",
        "R16G16UNorm",
        "RGB101010x",
        "RGB888x",
        "RGBA1010102",
        "RGBA8888",
        "RGBA8888",
        "SRGBA8888",
    ]:
        return 4
    elif color_type in ["R16G16B16A16UNorm", "RGBAF16", "RGBAF16Norm"]:
        return 8
    elif color_type == "RGBAF32":
        return 16

    raise ValueError(f"Unsupported color type: {color_type}")


def _fetch_data(src) -> Tuple[bytes, str]:
    src = expand_url(src)
    if isinstance(src, bytes):
        return src, "<bytes>"
    elif isinstance(src, str):
        if src.startswith("data:"):
            data = decode_data_url(src)
            return data, src
        elif re.match(r"^https?://", src):
            data = fetch_url(src)
            return data, src
        else:
            data = pathlib.Path(src).read_bytes()
            return data, src
    raise TypeError(f"Unsupported src type: {type(src).__name__}")
