import dataclasses
from pathlib import Path
from typing import Dict, List, overload, Sequence

from ..skia_canvas_pyr import (
    get_families,
    has,
    family,
    add_family,
    reset,
    FamilyDetails,
    TypefaceDetails,
)


def _convert_path_list(font_paths: List[str | Path]) -> List[str]:
    res = []
    for p in font_paths:
        if isinstance(p, Path):
            res.append(str(p))
        elif isinstance(p, str):
            res.append(p)
        else:
            raise TypeError(f"Invalid font path type: {type(p).__name__}")
    return res


class _FontLibrary:
    def __init__(self) -> None:
        pass

    @property
    def families(self) -> List[str]:
        return get_families()

    def has(self, family_name: str) -> bool:
        return has(family_name)

    def family(self, family_name: str) -> FamilyDetails | None:
        return family(family_name)

    @overload
    def use(self, font_path: str | Path, /) -> List[TypefaceDetails]: ...
    @overload
    def use(self, font_paths: Sequence[str | Path], /) -> List[TypefaceDetails]: ...
    @overload
    def use(
        self, alias: str, font_paths: Sequence[str | Path], /
    ) -> List[TypefaceDetails]: ...
    @overload
    def use(
        self, fonts: Dict[str, Sequence[str | Path]], /
    ) -> Dict[str, List[TypefaceDetails]]: ...

    def use(self, *args) -> List[TypefaceDetails] | Dict[str, List[TypefaceDetails]]:
        if len(args) == 1:
            first = args[0]
            if isinstance(first, list):
                return add_family(_convert_path_list(first), None)
            elif isinstance(first, dict):
                results = {}
                for alias, font_paths in first.items():
                    results[alias] = add_family(_convert_path_list(font_paths), alias)
                return results
            elif isinstance(first, (str, Path)):
                return add_family([str(first)], None)
        elif len(args) == 2:
            alias, font_paths = args
            return add_family(_convert_path_list(font_paths), alias)

        raise ValueError("Invalid arguments for use() method")

    def reset(self) -> None:
        reset()


@dataclasses.dataclass(frozen=True)
class TextMetrics:
    """
    The dimensions of a piece of text in the canvas, as created by the CanvasRenderingContext2D.measureText() method.

    [MDN Reference](https://developer.mozilla.org/docs/Web/API/TextMetrics)

    Attributes:
        actualBoundingBoxAscent: [MDN Reference](https://developer.mozilla.org/docs/Web/API/TextMetrics/actualBoundingBoxAscent)
        actualBoundingBoxDescent: [MDN Reference](https://developer.mozilla.org/docs/Web/API/TextMetrics/actualBoundingBoxDescent)
        actualBoundingBoxLeft: [MDN Reference](https://developer.mozilla.org/docs/Web/API/TextMetrics/actualBoundingBoxLeft)
        actualBoundingBoxRight: [MDN Reference](https://developer.mozilla.org/docs/Web/API/TextMetrics/actualBoundingBoxRight)
        alphabeticBaseline: [MDN Reference](https://developer.mozilla.org/docs/Web/API/TextMetrics/alphabeticBaseline)
        emHeightAscent: [MDN Reference](https://developer.mozilla.org/docs/Web/API/TextMetrics/emHeightAscent)
        emHeightDescent: [MDN Reference](https://developer.mozilla.org/docs/Web/API/TextMetrics/emHeightDescent)
        fontBoundingBoxAscent: [MDN Reference](https://developer.mozilla.org/docs/Web/API/TextMetrics/fontBoundingBoxAscent)
        fontBoundingBoxDescent: [MDN Reference](https://developer.mozilla.org/docs/Web/API/TextMetrics/fontBoundingBoxDescent)
        hangingBaseline: [MDN Reference](https://developer.mozilla.org/docs/Web/API/TextMetrics/hangingBaseline)
        ideographicBaseline: [MDN Reference](https://developer.mozilla.org/docs/Web/API/TextMetrics/ideographicBaseline)
        width: [MDN Reference](https://developer.mozilla.org/docs/Web/API/TextMetrics/width)
        lines: Individual metrics for each line (only applicable when context's textWrap is set to `true` )
    """

    actualBoundingBoxAscent: float
    actualBoundingBoxDescent: float
    actualBoundingBoxLeft: float
    actualBoundingBoxRight: float
    alphabeticBaseline: float
    emHeightAscent: float
    emHeightDescent: float
    fontBoundingBoxAscent: float
    fontBoundingBoxDescent: float
    hangingBaseline: float
    ideographicBaseline: float
    width: float

    lines: list[dict] | None = None


FontLibrary = _FontLibrary()
