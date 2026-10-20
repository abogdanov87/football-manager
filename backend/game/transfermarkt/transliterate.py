"""Latin football names → Russian (simplified BGN-style, deterministic)."""

from __future__ import annotations

import re
import unicodedata

# Multi-char sequences first (order matters).
_DIGRAPHS: tuple[tuple[str, str], ...] = (
    ("sch", "ш"),
    ("sh", "ш"),
    ("ch", "ч"),
    ("kh", "х"),
    ("zh", "ж"),
    ("ts", "ц"),
    ("ya", "я"),
    ("yu", "ю"),
    ("yo", "ё"),
    ("ye", "е"),
    ("iy", "ий"),
    ("ii", "ий"),
    ("ey", "ей"),
    ("ay", "ей"),
    ("ow", "оу"),
    ("ou", "у"),
    ("ee", "и"),
    ("oo", "у"),
)

_CHAR_MAP: dict[str, str] = {
    "a": "а",
    "b": "б",
    "c": "к",
    "d": "д",
    "e": "е",
    "f": "ф",
    "g": "г",
    "h": "х",
    "i": "и",
    "j": "дж",
    "k": "к",
    "l": "л",
    "m": "м",
    "n": "н",
    "o": "о",
    "p": "п",
    "q": "к",
    "r": "р",
    "s": "с",
    "t": "т",
    "u": "у",
    "v": "в",
    "w": "в",
    "x": "кс",
    "y": "й",
    "z": "з",
    "'": "",
    "-": "-",
    " ": " ",
}


def _strip_accents(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def _transliterate_token(token: str) -> str:
    lower = _strip_accents(token).lower()
    if not lower:
        return token
    if lower in {"de", "van", "von", "der", "di", "da", "le", "la", "el", "al"}:
        return lower
    i = 0
    out: list[str] = []
    while i < len(lower):
        matched = False
        for src, dst in _DIGRAPHS:
            if lower.startswith(src, i):
                out.append(dst)
                i += len(src)
                matched = True
                break
        if matched:
            continue
        ch = lower[i]
        out.append(_CHAR_MAP.get(ch, ch))
        i += 1
    result = "".join(out)
    if token.isupper():
        return result.upper()
    if token[0].isupper():
        return result[:1].upper() + result[1:]
    return result


def transliterate_name(latin_name: str) -> str:
    """Return Russian display name; keeps hyphenated / multi-part names."""
    latin_name = re.sub(r"\s+", " ", latin_name.strip())
    if not latin_name:
        return latin_name
    parts = re.split(r"(\s+|-)", latin_name)
    return "".join(
        _transliterate_token(p) if p not in {" ", "-"} else p for p in parts
    )
