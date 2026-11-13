"""O'zbek tili (kirill) — uz_lat'dan avtomatik hosil qilinadi (translit.lat2cyr).

Avtomatik o'girish noto'g'ri chiqadigan so'zlar ``FIXUPS`` da tuzatiladi
(masalan, "obyektivka" -> "Объективка", lotin qisqartmalari).
"""

from typing import Any

from ..translit import deep_convert
from . import uz_lat

FIXUPS: list[tuple[str, str]] = [
    ("ОБЕКТИВ", "ОБЪЕКТИВ"),
    ("Обектив", "Объектив"),
    ("обектив", "объектив"),
    ("ПДФ", "PDF"),
    ("А4", "A4"),  # kirill "А" + 4 -> lotin A4
]


def _fix(o: Any) -> Any:
    if isinstance(o, str):
        for a, b in FIXUPS:
            o = o.replace(a, b)
        return o
    if isinstance(o, list):
        return [_fix(x) for x in o]
    if isinstance(o, dict):
        return {k: _fix(v) for k, v in o.items()}
    return o


def derive(d: dict[str, Any], skip: list[str] | None = None) -> dict[str, Any]:
    return _fix(deep_convert(d, "lat", "cyr", skip))


TL: dict[str, Any] = derive(uz_lat.TL)
UI: dict[str, Any] = derive(uz_lat.UI, ["fname"])
SAMPLE: dict[str, Any] = derive(uz_lat.SAMPLE, ["photo", "tugSana"])
SITE: dict[str, Any] = derive(uz_lat.SITE)
