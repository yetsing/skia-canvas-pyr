from typing import TYPE_CHECKING

from ..skia_canvas_pyr import get_families, has, family, add_family, reset

if TYPE_CHECKING:
    from typing import Dict, List, overload
    from ..skia_canvas_pyr import FamilyDetails, TypefaceDetails


class FontLibrary:
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
    def use(self, font_paths: List[str], /) -> List[TypefaceDetails]: ...
    @overload
    def use(self, alias: str, font_paths: List[str], /) -> List[TypefaceDetails]: ...
    @overload
    def use(
        self, fonts: Dict[str, List[str]], /
    ) -> Dict[str, List[TypefaceDetails]]: ...

    def use(self, *args) -> List[TypefaceDetails] | Dict[str, List[TypefaceDetails]]:
        if len(args) == 1:
            first = args[0]
            if isinstance(first, list):
                return add_family(first, None)
            elif isinstance(first, dict):
                results = {}
                for alias, font_paths in first.items():
                    results[alias] = add_family(font_paths, alias)
                return results
        elif len(args) == 2:
            alias, font_paths = args
            return add_family(font_paths, alias)

        raise ValueError("Invalid arguments for use() method")

    def reset(self) -> None:
        reset()
