"""Tillar ro'yxati va lug'atlarga kirish.

Ichki kodlar prototip bilan bir xil: ``new`` (UZ, yangi lotin), ``lat`` (UZB, lotin),
``cyr`` (Кирилл), ``ru`` (Рус). URL prefikslari: /uz/, /uzb/, /kr/, /ru/.

Yangi til qo'shish — README'dagi "Yangi til qo'shish" bo'limiga qarang.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass
from functools import cache
from types import ModuleType
from typing import Any

from . import ru, uz_cyr, uz_lat, uz_new


@dataclass(frozen=True)
class Lang:
    code: str  # ichki kod (ma'lumotlardagi "lang" maydoni)
    prefix: str  # URL prefiksi
    label: str  # tugmadagi qisqa nom
    title: str  # tugma title / to'liq nom
    html_lang: str  # <html lang>
    hreflang: str  # SEO alternate
    og_locale: str
    docx_lang: str  # Word'dagi w:lang
    script: str  # transliteratsiya yozuvi (translit.Script)
    module: ModuleType


LANGS: dict[str, Lang] = {
    "new": Lang(
        "new",
        "uz",
        "UZ",
        "O‘zbek — yangi lotin (ç, ş, ğ, ö)",
        "uz",
        "uz-Latn",
        "uz_UZ",
        "uz-Latn-UZ",
        "new",
        uz_new,
    ),
    "lat": Lang("lat", "uzb", "UZB", "O‘zbek — lotin", "uz", "uz", "uz_UZ", "uz-Latn-UZ", "lat", uz_lat),
    "cyr": Lang(
        "cyr", "kr", "Кирилл", "Ўзбек — кирилл", "uz-Cyrl", "uz-Cyrl", "uz_UZ", "uz-Cyrl-UZ", "cyr", uz_cyr
    ),
    "ru": Lang("ru", "ru", "Рус", "Русский", "ru", "ru", "ru_RU", "ru-RU", "ru", ru),
}
DEFAULT_LANG = "lat"
PREFIX_TO_CODE = {lang.prefix: code for code, lang in LANGS.items()}

# Til almashganda o'girilmaydigan maydonlar (prototip: NOCONV)
NOCONV = ("photo", "tugSana", "lang")


def is_uzbek(code: str) -> bool:
    """O'zbek yozuvlari orasida ma'lumot transliteratsiya qilinadi; rus tiliga — yo'q."""
    return code != "ru"


def get_lang(code: str | None) -> Lang:
    return LANGS.get(code or "", LANGS[DEFAULT_LANG])


class Labels(dict[str, Any]):
    """Varaq yorliqlari (prototip: getTL). Lug'at + ``davr`` va ``rel_lines`` yordamchilari."""

    @property
    def lang(self) -> str:
        return str(self["lang"])

    def davr(self, dan: object, gacha: object) -> str:
        a = ("" if dan is None else str(dan)).strip()
        b = ("" if gacha is None else str(gacha)).strip()
        if not a and not b:
            return ""
        return f"{a}-{b} {self['yy']}" if b else f"{a} {self['y']} – {self['hv']}"

    def rel_lines(self, name: str) -> list[str]:
        if self.lang == "ru":
            return [self["relTitle"], self["relPre"] + name]
        return [name + self["relSfx"], self["relTitle"]]


@cache
def _tl(code: str) -> Labels:
    labels = Labels(get_lang(code).module.TL)
    labels["lang"] = get_lang(code).code
    return labels


def get_tl(code: str) -> Labels:
    return _tl(get_lang(code).code)


def get_ui(code: str) -> dict[str, Any]:
    return get_lang(code).module.UI


def get_site(code: str) -> dict[str, Any]:
    return get_lang(code).module.SITE


def get_sample(code: str) -> dict[str, Any]:
    """Namuna ma'lumot (har chaqiruvda yangi nusxa)."""
    data = copy.deepcopy(get_lang(code).module.SAMPLE)
    data["lang"] = get_lang(code).code
    return data
