"""
Parsers for properties that take CSS-style strings as values
"""

import math
import re
from collections.abc import Sequence
from typing import cast

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


def parseFont(text):
    if cache["font"].get(text, None) is None and text not in cache["font"]:
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
            tokens = split_by(value, r"\s+")

            while tokens:
                token = tokens.pop(0)
                match = (
                    "style"
                    if styleRE.match(token)
                    else (
                        "variant"
                        if smallcapsRE.match(token)
                        else (
                            "stretch"
                            if stretchRE.match(token)
                            else (
                                "weight"
                                if isWeight(token)
                                else "size" if isSize(token) else None
                            )
                        )
                    )
                )

                if match in ("style", "variant", "stretch", "weight"):
                    font[match] = token
                    continue

                if match == "size":
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
                    invalid = (
                        f'font size "{emSize}"'
                        if not _is_finite(size)
                        else (
                            f'line height "{leading}"'
                            if (lineHeight is not None and not _is_finite(lineHeight))
                            else (
                                f'font weight "{font["weight"]}"'
                                if not _is_finite(weight)
                                else (
                                    f'font family "{", ".join(tokens)}"'
                                    if len(family) == 0
                                    else False
                                )
                            )
                        )
                    )

                    if not invalid:
                        # include a re-stringified version of the decoded/absified values
                        canonical_parts = [
                            style,
                            variant if variant != style else None,
                            weight if weight not in (variant, style) else None,
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
                        cache["font"][text] = result
                        return result

                    raise ValueError(f"Invalid {invalid}")

                raise ValueError(f'Unrecognized font attribute "{token}"')

            raise ValueError("Could not find a font size value")
        except Exception:
            # console.warn(Object.assign(e, {name:"Warning"}))
            cache["font"][text] = None

    return cache["font"].get(text)


def parseSize(text, emSize=16.0):
    global m
    m = numSizeRE.search(str(text))
    if m:
        size = float(m.group(1))
        unit = m.group(2)
        return size * (
            1
            if unit == "px"
            else (
                1 / 0.75
                if unit == "pt"
                else (
                    emSize / 100
                    if unit == "%"
                    else (
                        16
                        if unit == "pc"
                        else (
                            96
                            if unit == "in"
                            else (
                                96.0 / 2.54
                                if unit == "cm"
                                else (
                                    96.0 / 25.4
                                    if unit == "mm"
                                    else (
                                        96 / 25.4 / 4
                                        if unit == "q"
                                        else (
                                            emSize
                                            if re.search(r"r?em", unit)
                                            else math.nan
                                        )
                                    )
                                )
                            )
                        )
                    )
                )
            )
        )

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
        px = size * (
            1
            if unit == "px"
            else (
                1 / 0.75
                if unit == "pt"
                else (
                    16
                    if unit == "pc"
                    else (
                        96
                        if unit == "in"
                        else (
                            96.0 / 2.54
                            if unit == "cm"
                            else (
                                96.0 / 25.4
                                if unit == "mm"
                                else 96 / 25.4 / 4 if unit == "q" else math.nan
                            )
                        )
                    )
                )
            )
        )
        return {"size": size, "unit": unit, "px": px}
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
        return val if val != 0 else math.nan

    m = namedWeightRE.search(str(text))
    if m:
        return weightMap[m.group(0)]

    return math.nan


def parseVariant(text):
    if cache["variant"].get(text, None) is None and text not in cache["variant"]:
        variants = []
        features: dict[str, object] = {"on": [], "off": []}

        for token in split_by(str(text), r"\s+"):
            if token == "normal":
                return {"variants": [token], "features": {"on": [], "off": []}}
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

        cache["variant"][text] = {"variant": " ".join(variants), "features": features}

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

    return {
        "style": style,
        "line": line,
        "color": color,
        "thickness": thickness,
        "inherit": inherit,
        "str": text,
    }


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

    return (
        [radii[0], radii[0], radii[0], radii[0]]
        if len(radii) == 1
        else (
            [radii[0], radii[1], radii[0], radii[1]]
            if len(radii) == 2
            else (
                [radii[0], radii[1], radii[2], radii[1]]
                if len(radii) == 3
                else (
                    [radii[0], radii[1], radii[2], radii[3]]
                    if len(radii) == 4
                    else [
                        {"x": 0, "y": 0},
                        {"x": 0, "y": 0},
                        {"x": 0, "y": 0},
                        {"x": 0, "y": 0},
                    ]
                )
            )
        )
    )


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
                filters[kind] = [*dims, color]
                canonical.append(
                    f"{kind}({' '.join(lengths)} {color.replace(' ', '')})"
                )
            continue

        m = plainFilterRE.search(spec)
        if m:
            kind, arg = m.group(1), m.group(2)
            val = (
                parseSize(arg)
                if kind == "blur"
                else parseAngle(arg) if kind == "hue-rotate" else parsePercentage(arg)
            )
            if _is_finite(val):
                filters[kind] = val
                canonical.append(f"{kind}({arg.strip()})")

    s = str(text).strip()
    return (
        {"canonical": "none", "filters": filters}
        if s == "none"
        else (
            {"canonical": " ".join(canonical), "filters": filters}
            if canonical
            else None
        )
    )


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
        return (
            amt
            if unit == "deg"
            else (
                360 * amt / (2 * math.pi)
                if unit == "rad"
                else (
                    360 * amt / 400
                    if unit == "grad"
                    else 360 * amt if unit == "turn" else math.nan
                )
            )
        )
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
