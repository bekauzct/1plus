"""O'zbek tili (yangi lotin: ç, ş, ğ, ö) — uz_lat'dan avtomatik hosil qilinadi (translit.lat2new)."""

from typing import Any

from ..translit import deep_convert
from . import uz_lat


def derive(d: dict[str, Any], skip: list[str] | None = None) -> dict[str, Any]:
    return deep_convert(d, "lat", "new", skip)  # type: ignore[no-any-return]


TL: dict[str, Any] = derive(uz_lat.TL)
UI: dict[str, Any] = derive(uz_lat.UI, ["fname"])
SAMPLE: dict[str, Any] = derive(uz_lat.SAMPLE, ["photo", "tugSana"])
SITE: dict[str, Any] = derive(uz_lat.SITE)
