"""
Parsers for properties that take CSS-style strings as values
"""

import dataclasses
import math
import re
from collections.abc import Sequence
from typing import cast, Any, List, Dict, Tuple

from .sc_type import Spacing

# -- Font & Variant --------------------------------------------------------------------
#    https://developer.mozilla.org/en-US/docs/Web/CSS/font-variant
#    https://www.w3.org/TR/css-fonts-3/#font-size-prop

m = None
cache = {"font": {}, "variant": {}}

styleRE = re.compile(r"^(normal|italic|oblique)$")
smallcapsRE = re.compile(r"^(normal|small-caps)$")
stretchRE = re.compile(r"^(normal|(semi-|extra-|ultra-)?(condensed|expanded))$")
namedSizeRE = re.compile(r"(?:xx?-)?small|smaller|medium|larger|(?:xx?-)?large|normal")
numSizeRE = re.compile(r"^(\-?[\d\.]+)(px|pt|pc|in|cm|mm|%|em|ex|ch|rem|q)")
namedWeightRE = re.compile(r"^(normal|bold(er)?|lighter)$")
numWeightRE = re.compile(r"^(1000|\d{1,3})$")
parameterizedRE = re.compile(r"([\w\-]+)\((.*?)\)")

# region Some Object


@dataclasses.dataclass
class Font:
    style: str
    variant: str
    weight: float
    stretch: str
    size: float
    lineHeight: float | None
    family: List[str]
    features: Dict[str, float | List[str]]
    canonical: str


@dataclasses.dataclass
class FontVariant:
    variant: str
    features: Dict[str, float | List[str]]


@dataclasses.dataclass
class FontSpacing:
    size: float
    unit: str
    px: float


@dataclasses.dataclass
class FontTextDecoration:
    style: str
    line: str
    color: str
    thickness: Spacing | None
    inherit: str
    text: str


@dataclasses.dataclass
class Filter:
    canonical: str
    filters: Dict[str, float | Tuple[float, float, float, str]]


# endregion


def split_by(text, sep_regex):
    # split while preserving balanced (...) and quoted segments
    pat = re.compile(sep_regex)
    tokens = []
    buf = []
    depth = 0
    quote = None
    i = 0

    while i < len(text):
        ch = text[i]

        if quote:
            buf.append(ch)
            if ch == quote:
                quote = None
            i += 1
            continue

        if ch in ("'", '"'):
            quote = ch
            buf.append(ch)
            i += 1
            continue

        if ch == "(":
            depth += 1
            buf.append(ch)
            i += 1
            continue

        if ch == ")":
            depth = max(0, depth - 1)
            buf.append(ch)
            i += 1
            continue

        if depth == 0:
            matched = pat.match(text, i)
            if matched:
                token = "".join(buf).strip()
                if token:
                    tokens.append(token)
                buf = []
                i = matched.end()
                continue

        buf.append(ch)
        i += 1

    token = "".join(buf).strip()
    if token:
        tokens.append(token)
    return tokens


def unquote(s):
    return re.sub(r"^(['\"])(.*?)\1$", r"\2", s)


def isSize(s):
    return bool(namedSizeRE.search(s) or numSizeRE.search(s))


def isWeight(s):
    return bool(namedWeightRE.search(s) or numWeightRE.search(s))


def _is_finite(value):
    try:
        return math.isfinite(value)
    except Exception:
        return False


def parseFont(text) -> Font | None:
    if text not in cache["font"]:
        try:
            if not isinstance(text, str):
                raise ValueError("Font specification must be a string")
            if not text:
                raise ValueError("Font specification cannot be an empty string")

            font = {
                "style": "normal",
                "variant": "normal",
                "weight": "normal",
                "stretch": "normal",
            }
            value = re.sub(r"\s*/\*s", "/", text)
            tokens = value.split()

            while tokens:
                token = tokens.pop(0)
                match_case = None
                if styleRE.match(token):
                    match_case = "style"
                elif smallcapsRE.match(token):
                    match_case = "variant"
                elif stretchRE.match(token):
                    match_case = "stretch"
                elif isWeight(token):
                    match_case = "weight"
                elif isSize(token):
                    match_case = "size"

                if match_case in ("style", "variant", "stretch", "weight"):
                    font[match_case] = token
                    continue

                if match_case == "size":
                    # size is the pivot point between the style fields and the family name stack,
                    # so start processing what's been collected
                    parts = split_by(token, r"/")
                    emSize = parts[0] if parts else token
                    leading = parts[1] if len(parts) > 1 else None
                    size = parseSize(emSize)
                    lineHeight = (
                        parseSize(re.sub(r"(\d)$", r"\1em", leading), size)
                        if leading
                        else None
                    )
                    weight = parseWeight(font["weight"])
                    family = [
                        unquote(p) for p in split_by(" ".join(tokens), r"\s*,\s*")
                    ]
                    features = (
                        {"on": ["smcp", "onum"]}
                        if font["variant"] == "small-caps"
                        else {}
                    )
                    style = font["style"]
                    stretch = font["stretch"]
                    variant = font["variant"]

                    # make sure all the numeric fields have legitimate values
                    invalid = ""
                    if not _is_finite(size):
                        invalid = f'font size "{emSize}"'
                    elif lineHeight is not None and not _is_finite(lineHeight):
                        invalid = f'line height "{leading}"'
                    elif not _is_finite(weight):
                        invalid = f'font weight "{font["weight"]}"'
                    elif len(family) == 0:
                        invalid = f'font family "{", ".join(tokens)}"'

                    if not invalid:
                        # include a re-stringified version of the decoded/absified values
                        canonical_parts = [
                            style,
                            variant if variant != style else None,
                            str(weight) if weight not in (variant, style) else None,
                            (
                                stretch
                                if stretch not in (variant, style, weight)
                                else None
                            ),
                            f"{size}px{'/' + str(lineHeight) + 'px' if _is_finite(lineHeight) else ''}",
                            ", ".join(
                                [
                                    f'"{nm}"' if re.search(r"\s", nm) else nm
                                    for nm in family
                                ]
                            ),
                        ]
                        result = {
                            **font,
                            "size": size,
                            "lineHeight": lineHeight,
                            "weight": weight,
                            "family": family,
                            "features": features,
                            "canonical": " ".join([p for p in canonical_parts if p]),
                        }
                        font_obj = Font(**result)
                        cache["font"][text] = font_obj
                        return font_obj

                    raise ValueError(f"Invalid {invalid}")

                raise ValueError(f'Unrecognized font attribute "{token}"')

            raise ValueError("Could not find a font size value")
        except Exception:
            cache["font"][text] = None

    return cache["font"].get(text)


def parseSize(text, emSize=16.0):
    global m
    m = numSizeRE.search(str(text))
    if m:
        size = float(m.group(1))
        unit = m.group(2)
        unit_num = math.nan
        match unit:
            case "px":
                unit_num = 1
            case "pt":
                unit_num = 1 / 0.75
            case "%":
                unit_num = emSize / 100
            case "pc":
                unit_num = 16
            case "in":
                unit_num = 96
            case "cm":
                unit_num = 96.0 / 2.54
            case "mm":
                unit_num = 96.0 / 25.4
            case "q":
                unit_num = 96 / 25.4 / 4
            case _:
                if re.search(r"r?em", unit):
                    unit_num = emSize
        return size * unit_num

    m = namedSizeRE.search(str(text))
    if m:
        return emSize * (sizeMap.get(m.group(0), 1.0))

    return math.nan


def parseFlexibleSize(text):
    global m
    m = numSizeRE.search(str(text))
    if m:
        size = float(m.group(1))
        unit = m.group(2)
        unit_num = math.nan
        match unit:
            case "px":
                unit_num = 1
            case "pt":
                unit_num = 1 / 0.75
            case "pc":
                unit_num = 16
            case "in":
                unit_num = 96
            case "cm":
                unit_num = 96.0 / 2.54
            case "mm":
                unit_num = 96.0 / 25.4
            case "q":
                unit_num = 96 / 25.4 / 4
        px = size * unit_num
        return FontSpacing(size=size, unit=unit, px=px)
    return None


def parseStretch(text):
    global m
    m = stretchRE.search(str(text))
    return m.group(0) if m else None


def parseWeight(text):
    global m
    m = numWeightRE.search(str(text))
    if m:
        val = int(m.group(0))
        return val or math.nan

    m = namedWeightRE.search(str(text))
    if m:
        return weightMap[m.group(0)]

    return math.nan


def parseVariant(text) -> FontVariant | None:
    if text not in cache["variant"]:
        variants = []
        features: Dict[str, Any] = {"on": [], "off": []}

        for token in text.split():
            if token == "normal":
                return FontVariant(variant="normal", features={"on": [], "off": []})
            if token in featureMap:
                for feat in featureMap[token]:
                    if feat and feat[0] == "-":
                        cast(list[str], features["off"]).append(feat[1:])
                    else:
                        cast(list[str], features["on"]).append(feat)
                variants.append(token)
                continue

            pm = parameterizedRE.search(token)
            if pm:
                name = pm.group(1)
                if name not in alternatesMap:
                    raise ValueError(f'Invalid font variant "{token}"')

                subPattern = alternatesMap[name]
                parsed = int(pm.group(2), 10)
                subValue = max(0, min(99, parsed))
                expanded = subPattern.replace("##", f"{subValue:02d}").replace(
                    "#", str(min(9, subValue))
                )
                parts = expanded.split(" ")
                feat = parts[0]
                val = parts[1] if len(parts) > 1 else None
                if val is None:
                    cast(list[str], features["on"]).append(feat)
                else:
                    features[feat] = int(val, 10)
                variants.append(f"{name}({subValue})")
                continue

            raise ValueError(f'Invalid font variant "{token}"')

        cache["variant"][text] = FontVariant(
            variant=" ".join(variants), features=features
        )

    return cache["variant"].get(text)


def parseTextDecoration(text):
    style = "solid"
    line = "none"
    color = "currentColor"
    inherit = "auto"
    thickness = None

    text = (text if isinstance(text, str) else "").strip()
    text = re.sub(r"\s+", " ", text, count=1)

    for token in text.split(" "):
        if re.search(r"solid|double|dotted|dashed|wavy", token):
            style = token
        elif re.search(r"none|initial|revert(-layer)?|unset", token):
            line = "none"
        elif re.search(r"underline|overline|line-through", token):
            line = token
        elif (val := parseFlexibleSize(token)) is not None:
            thickness = val
        elif re.search(r"auto|from-font", token):
            inherit = token
        elif token:
            color = token

    return FontTextDecoration(
        style=style,
        line=line,
        color=color,
        thickness=thickness,
        inherit=inherit,
        text=text,
    )


# -- Window Types -----------------------------------------------------------------------

cursorTypes = [
    "default",
    "none",
    "context-menu",
    "help",
    "pointer",
    "progress",
    "wait",
    "cell",
    "crosshair",
    "text",
    "vertical-text",
    "alias",
    "copy",
    "move",
    "no-drop",
    "not-allowed",
    "grab",
    "grabbing",
    "e-resize",
    "n-resize",
    "ne-resize",
    "nw-resize",
    "s-resize",
    "se-resize",
    "sw-resize",
    "w-resize",
    "ew-resize",
    "ns-resize",
    "nesw-resize",
    "nwse-resize",
    "col-resize",
    "row-resize",
    "all-scroll",
    "zoom-in",
    "zoom-out",
]


def parseCursor(text):
    return text in cursorTypes


def parseFit(mode):
    return mode in [
        "none",
        "contain-x",
        "contain-y",
        "contain",
        "cover",
        "fill",
        "scale-down",
        "resize",
    ]


# -- Corner Rounding
#    https://github.com/fserb/canvas2D/blob/master/spec/roundrect.md


class RangeError(ValueError):
    pass


def parseCornerRadii(r):
    if isinstance(r, Sequence) and not isinstance(r, (str, bytes, bytearray, dict)):
        vals = list(r)
    else:
        vals = [r]

    vals = vals[:4]
    radii = []
    for n in vals:
        if isinstance(n, dict) and "x" in n and "y" in n:
            radii.append(n)
        elif hasattr(n, "x") and hasattr(n, "y"):
            radii.append({"x": getattr(n, "x"), "y": getattr(n, "y")})
        else:
            radii.append({"x": n, "y": n})

    if any(not _is_finite(pt["x"]) or not _is_finite(pt["y"]) for pt in radii):
        return None  # silently abort
    if any(pt["x"] < 0 or pt["y"] < 0 for pt in radii):
        raise RangeError("Corner radius cannot be negative")

    match len(radii):
        case 1:
            return [radii[0], radii[0], radii[0], radii[0]]
        case 2:
            return [radii[0], radii[1], radii[0], radii[1]]
        case 3:
            return [radii[0], radii[1], radii[2], radii[1]]
        case 4:
            return [radii[0], radii[1], radii[2], radii[3]]
        case _:
            return [
                {"x": 0, "y": 0},
                {"x": 0, "y": 0},
                {"x": 0, "y": 0},
                {"x": 0, "y": 0},
            ]


# -- Image Filters -----------------------------------------------------------------------
#    https://developer.mozilla.org/en-US/docs/Web/CSS/filter

plainFilterRE = re.compile(
    r"(blur|hue-rotate|brightness|contrast|grayscale|invert|opacity|saturate|sepia)\((.*?)\)"
)
shadowFilterRE = re.compile(r"drop-shadow\((.*)\)")
percentValueRE = re.compile(r"^(\+|-)?\d+%$")
angleValueRE = re.compile(r"([\d\.]+)(deg|g?rad|turn)")


def parseFilter(text):
    global m
    filters = {}
    canonical = []

    for spec in split_by(str(text), r"\s+") or []:
        m = shadowFilterRE.search(spec)
        if m:
            kind = "drop-shadow"
            args = m.group(1).strip().split()
            lengths = args[:3]
            color = " ".join(args[3:])
            dims = [parseSize(s) for s in lengths]
            dims = [d for d in dims if _is_finite(d)]
            if len(dims) == 3 and bool(color):
                filters[kind] = (*dims, color)
                canonical.append(
                    f"{kind}({' '.join(lengths)} {color.replace(' ', '')})"
                )
            continue

        m = plainFilterRE.search(spec)
        if m:
            kind, arg = m.group(1), m.group(2)
            match kind:
                case "blur":
                    val = parseSize(arg)
                case "hue-rotate":
                    val = parseAngle(arg)
                case _:
                    val = parsePercentage(arg)
            if _is_finite(val):
                filters[kind] = val
                canonical.append(f"{kind}({arg.strip()})")

    if text.strip() == "none":
        return Filter(canonical="none", filters=filters)
    elif canonical:
        return Filter(canonical=" ".join(canonical), filters=filters)
    else:
        return


def parsePercentage(text):
    s = str(text).strip()
    if percentValueRE.match(s):
        return int(s[:-1], 10) / 100
    try:
        return float(s)
    except ValueError:
        return math.nan


def parseAngle(text):
    global m
    m = angleValueRE.search(str(text).strip())
    if m:
        amt = float(m.group(1))
        unit = m.group(2)
        match unit:
            case "deg":
                return amt
            case "rad":
                return 360 * amt / (2 * math.pi)
            case "grad":
                return 360 * amt / 400
            case "turn":
                return 360 * amt
    return math.nan


#
# Font attribute keywords & corresponding values
#

weightMap = {
    "lighter": 300,
    "normal": 400,
    "bold": 700,
    "bolder": 800,
}

sizeMap = {
    "xx-small": 3 / 5,
    "x-small": 3 / 4,
    "small": 8 / 9,
    "smaller": 8 / 9,
    "large": 6 / 5,
    "larger": 6 / 5,
    "x-large": 3 / 2,
    "xx-large": 2 / 1,
    "normal": 1.2,  # special case for lineHeight
}

featureMap = {
    "normal": [],
    # font-variant-ligatures
    "common-ligatures": ["liga", "clig"],
    "no-common-ligatures": ["-liga", "-clig"],
    "discretionary-ligatures": ["dlig"],
    "no-discretionary-ligatures": ["-dlig"],
    "historical-ligatures": ["hlig"],
    "no-historical-ligatures": ["-hlig"],
    "contextual": ["calt"],
    "no-contextual": ["-calt"],
    # font-variant-position
    "super": ["sups"],
    "sub": ["subs"],
    # font-variant-caps
    "small-caps": ["smcp"],
    "all-small-caps": ["c2sc", "smcp"],
    "petite-caps": ["pcap"],
    "all-petite-caps": ["c2pc", "pcap"],
    "unicase": ["unic"],
    "titling-caps": ["titl"],
    # font-variant-numeric
    "lining-nums": ["lnum"],
    "oldstyle-nums": ["onum"],
    "proportional-nums": ["pnum"],
    "tabular-nums": ["tnum"],
    "diagonal-fractions": ["frac"],
    "stacked-fractions": ["afrc"],
    "ordinal": ["ordn"],
    "slashed-zero": ["zero"],
    # font-variant-east-asian
    "jis78": ["jp78"],
    "jis83": ["jp83"],
    "jis90": ["jp90"],
    "jis04": ["jp04"],
    "simplified": ["smpl"],
    "traditional": ["trad"],
    "full-width": ["fwid"],
    "proportional-width": ["pwid"],
    "ruby": ["ruby"],
    # font-variant-alternates (non-parameterized)
    "historical-forms": ["hist"],
}

alternatesMap = {
    "stylistic": "salt #",
    "styleset": "ss##",
    "character-variant": "cv##",
    "swash": "swsh #",
    "ornaments": "ornm #",
    "annotation": "nalt #",
}


# used by context
font = parseFont
variant = parseVariant
size = parseSize
spacing = parseFlexibleSize
stretch = parseStretch
decoration = parseTextDecoration
filter = parseFilter

# path & context
radii = parseCornerRadii

# gui
cursor = parseCursor
fit = parseFit

__all__ = [
    "parseFont",
    "parseVariant",
    "parseSize",
    "parseFlexibleSize",
    "parseStretch",
    "parseTextDecoration",
    "parseFilter",
    "parseCornerRadii",
    "parseCursor",
    "parseFit",
    "font",
    "variant",
    "size",
    "spacing",
    "stretch",
    "decoration",
    "filter",
    "radii",
    "cursor",
    "fit",
    "RangeError",
]
