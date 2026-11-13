"""O'zbek yozuvlari orasida transliteratsiya: lotin <-> kirill <-> yangi lotin (ç, ş, ğ, ö).

Bu modul ``reference/obyektivka.html`` dagi JS funksiyalarning (lat2cyr, cyr2lat, lat2new,
new2lat, convertScript, deepConvert) aniq porti. Natija JS bilan belgima-belgi bir xil bo'lishi
``tests/test_translit.py`` dagi golden testlar bilan tekshiriladi.

Yozuv identifikatorlari: ``new`` (UZ, yangi lotin), ``lat`` (UZB, lotin), ``cyr`` (kirill),
``ru`` (rus tili — matn o'girilmaydi, lotin kabi o'tadi).
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from typing import Any, Literal

Script = Literal["new", "lat", "cyr", "ru"]

APOS = frozenset("'‘’ʻʼ`´")  # JS: /['‘’ʻʼ`´]/
_LETTER_RE = re.compile(r"[A-Za-zА-Яа-яЁёЎўҚқҒғҲҳÇçŞşĞğÖö]")


def _at(s: str, i: int) -> str:
    """JS'dagi ``s[i]`` kabi: chegaradan tashqarida bo'sh satr (Python'dagi manfiy indeksdan saqlanish)."""
    return s[i] if 0 <= i < len(s) else ""


def _is_letter(c: str) -> bool:
    return bool(c) and _LETTER_RE.match(c) is not None


def _is_upper(c: str) -> bool:
    return bool(c) and c != c.lower() and c == c.upper()


def _is_apos(c: str) -> bool:
    return c in APOS if c else False


def _s(s: object) -> str:
    return "" if s is None else str(s)


_LAT2CYR = {
    "a": "а", "b": "б", "d": "д", "f": "ф", "g": "г", "h": "ҳ", "i": "и", "j": "ж", "k": "к",
    "l": "л", "m": "м", "n": "н", "o": "о", "p": "п", "q": "қ", "r": "р", "s": "с", "t": "т",
    "u": "у", "v": "в", "x": "х", "y": "й", "z": "з", "c": "ц", "w": "в", "e": "е",
}  # fmt: skip
_Y_VOWEL = {"a": "я", "o": "ё", "u": "ю", "e": "е"}


def lat2cyr(s: object) -> str:
    s = _s(s)
    out: list[str] = []
    i = 0
    n_len = len(s)
    while i < n_len:
        c = s[i]
        lo = c.lower()
        n = _at(s, i + 1)
        nlo = n.lower()
        nn = _at(s, i + 2)
        prev = _at(s, i - 1)
        up = _is_upper(c)

        def put(r: str, up: bool = up) -> None:
            out.append(r.upper() if up else r)

        if lo in ("o", "g") and _is_apos(n):
            put("ў" if lo == "o" else "ғ")
            i += 2
            continue
        if lo == "s" and nlo == "h":
            put("ш")
            i += 2
            continue
        if lo == "c" and nlo == "h":
            put("ч")
            i += 2
            continue
        if lo == "y" and nlo == "o" and _is_apos(nn):
            put("й")
            i += 1
            continue
        if lo == "y" and nlo and nlo in "aoue":
            put(_Y_VOWEL[nlo])
            i += 2
            continue
        if lo == "e":
            put("е" if _is_letter(prev) else "э")
            i += 1
            continue
        if _is_apos(c) and _is_letter(prev) and _is_letter(n):
            out.append("Ъ" if (_is_upper(prev) and _is_upper(n)) else "ъ")
            i += 1
            continue
        r = _LAT2CYR.get(lo)
        if r:
            put(r)
        else:
            out.append(c)
        i += 1
    return "".join(out)


_CYR2LAT = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "ё": "yo", "ж": "j", "з": "z", "и": "i",
    "й": "y", "к": "k", "л": "l", "м": "m", "н": "n", "о": "o", "п": "p", "р": "r", "с": "s",
    "т": "t", "у": "u", "ф": "f", "х": "x", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "sh", "ы": "i",
    "э": "e", "ю": "yu", "я": "ya", "ў": "oʻ", "қ": "q", "ғ": "gʻ", "ҳ": "h",
}  # fmt: skip
_CYR_VOWELS = "аеёиоуэюяўАЕЁИОУЭЮЯЎ"


def cyr2lat(s: object) -> str:
    s = _s(s)
    out: list[str] = []
    for i, c in enumerate(s):
        lo = c.lower()
        p = _at(s, i - 1)
        n = _at(s, i + 1)
        up = _is_upper(c)
        caps = up and ((_is_letter(n) and _is_upper(n)) or (_is_letter(p) and _is_upper(p)))
        r: str | None
        if lo == "е":
            r = "ye" if (not _is_letter(p) or p in _CYR_VOWELS or p in "ъьЪЬ") else "e"
        elif lo == "ъ":
            out.append("ʼ")
            continue
        elif lo == "ь":
            continue
        else:
            r = _CYR2LAT.get(lo)
        if r is None:
            out.append(c)
            continue
        if up:
            r = r.upper() if caps else r[0].upper() + r[1:]
        out.append(r)
    return "".join(out)


_NEW_APOS_RE = re.compile(r"([oOgG])['‘’ʻʼ`´]")
_NEW_MAP = {"o": "ö", "O": "Ö", "g": "ğ", "G": "Ğ"}


def lat2new(s: object) -> str:
    s = _s(s)
    s = _NEW_APOS_RE.sub(lambda m: _NEW_MAP[m.group(1)], s)
    s = s.replace("sh", "ş")
    s = re.sub(r"S[hH]", "Ş", s)
    s = s.replace("ch", "ç")
    s = re.sub(r"C[hH]", "Ç", s)
    return s


def new2lat(s: object) -> str:
    s = _s(s)

    def ctx(i: int, lo: str, up: str) -> str:
        p = _at(s, i - 1)
        n = _at(s, i + 1)
        caps = (_is_letter(n) and _is_upper(n)) or (_is_letter(p) and _is_upper(p))
        return up if caps else up[0] + lo[1:]

    simple = {"ö": "oʻ", "Ö": "Oʻ", "ğ": "gʻ", "Ğ": "Gʻ", "ş": "sh", "ç": "ch"}
    out: list[str] = []
    for i, c in enumerate(s):
        if c in simple:
            out.append(simple[c])
        elif c == "Ş":
            out.append(ctx(i, "sh", "SH"))
        elif c == "Ç":
            out.append(ctx(i, "ch", "CH"))
        else:
            out.append(c)
    return "".join(out)


def to_lat(s: object, src: str) -> str:
    if src == "cyr":
        return cyr2lat(s)
    if src == "new":
        return new2lat(s)
    return _s(s)


def from_lat(s: str, dst: str) -> str:
    if dst == "cyr":
        return lat2cyr(s)
    if dst == "new":
        return lat2new(s)
    return s


def convert_script(s: Any, src: str, dst: str) -> Any:
    if src == dst:
        return s
    return from_lat(to_lat(s, src), dst)


def deep_convert(o: Any, src: str, dst: str, skip: Iterable[str] | None = None) -> Any:
    """Ichma-ich (dict/list) tuzilmadagi barcha satrlarni o'giradi. ``skip`` kalitlari o'zgarmaydi."""
    skip_set = frozenset(skip or ())
    return _deep(o, src, dst, skip_set)


def _deep(o: Any, src: str, dst: str, skip: frozenset[str]) -> Any:
    if isinstance(o, str):
        return convert_script(o, src, dst)
    if isinstance(o, (list, tuple)):
        return [_deep(x, src, dst, skip) for x in o]
    if isinstance(o, dict):
        return {k: (v if k in skip else _deep(v, src, dst, skip)) for k, v in o.items()}
    return o
