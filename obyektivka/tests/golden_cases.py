"""Prototip JS funksiyalari bilan solishtiriladigan holatlar ro'yxati.

Kutilgan natijalar ``tests/fixtures/js_golden.json`` da; ularni qayta hosil qilish:
    uv run python scripts/gen_golden.py
"""

from __future__ import annotations

from typing import Any

from apps.obyektivka.i18n import uz_lat

WORDS_LAT = [
    "o'g'li", "o‘g‘li", "oʻgʻli", "Yo'q", "Yo‘q", "YO‘Q", "MA'LUMOT", "Ma’lumotnoma", "Yevropa", "SHAHAR",
    "Shahar", "shahar", "CHIRCHIQ", "Chirchiq", "choy", "Yangiyo‘l", "yoz", "yulduz", "yer", "Elektr",
    "ekran", "metro", "san’at", "SAN’AT", "ta'lim", "Mas’uliyat", "G‘ulom", "g‘isht", "O‘zbekiston",
    "o‘zbek", "Qo‘qon", "Xorazm", "Sirdaryo", "MChJ", "“Chirchiq transport” MChJ", "2024-yil 2-sentabrdan",
    "h.v.", "F.I.Sh", "Ish joyi", "Shoh", "ShOH", "Ch", "CH", "sH", "cH", "y", "Y", "E", "e", "",
    "Karimov Aziz Rustam o‘g‘li", "Toshkent viloyati, Chirchiq shahri", "Yo‘ldoshev", "maktab\no‘qituvchi",
    "Tsex", "Ts", "w", "Washington", "C++", "Ça", "Yoʻq", "a'b", "A'B", "a'B", "'start", "end'", "o`g`il",
    "o´g´il", "1976", "No 7", "Ye", "YE", "Yo", "YO", "Yu", "YU", "Ya", "YA", "ye'", "yo'l", "YO'L",
]  # fmt: skip

WORDS_CYR = [
    "Йўқ", "МАЪЛУМОТ", "Европа", "ШАҲАР", "Шаҳар", "ўғли", "Ўзбекистон", "ЎЗБЕКИСТОН", "объектив",
    "Объективка", "съезд", "Цех", "цирк", "ЦЕХ", "Щука", "Юлдуз", "ЮЛДУЗ", "Ёзувчи", "ЁЗ", "Яхши",
    "ЯХШИ", "Электр", "поэт", "мае", "Ер", "ер", "Салом", "ЧОЙ", "Чой", "Ғулом", "ҒУЛОМ", "Қўқон",
    "Ҳа", "ҲА", "Ьь", "сентябрь", "Ы", "Хорижий", "", "12.03.2006", "а-е", "ЕР", "ЮЕ",
]  # fmt: skip

WORDS_NEW = [
    "öğli", "Öğli", "ÖĞLI", "Şahar", "ŞAHAR", "Şa", "ŞA", "Çirçiq", "ÇIRÇIQ", "Ç", "Ş", "aŞ", "AŞ",
    "Şh", "ça", "Yöq", "",
]  # fmt: skip

PERIODS: list[dict[str, Any]] = [
    {"dan": "2021", "gacha": "2024"},
    {"dan": "2024", "gacha": ""},
    {"dan": "", "gacha": ""},
    {"dan": " 2020 ", "gacha": " 2022 "},
    {"dan": "", "gacha": "2019"},
    {"dan": "2010", "gacha": None},
    {},
]
LANGS = ["new", "lat", "cyr", "ru"]


def build_cases() -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for w in WORDS_LAT:
        cases += [{"fn": "lat2cyr", "args": [w]}, {"fn": "lat2new", "args": [w]}]
        for a, b in [
            ("lat", "cyr"),
            ("lat", "new"),
            ("cyr", "lat"),
            ("new", "lat"),
            ("cyr", "new"),
            ("new", "cyr"),
        ]:
            cases.append({"fn": "convertScript", "args": [w, a, b]})
    for w in WORDS_CYR:
        cases.append({"fn": "cyr2lat", "args": [w]})
        cases.append({"fn": "convertScript", "args": [w, "cyr", "new"]})
    for w in WORDS_NEW:
        cases.append({"fn": "new2lat", "args": [w]})
        cases.append({"fn": "convertScript", "args": [w, "new", "cyr"]})
    for lang in LANGS:
        cases.append({"fn": "getTL", "args": [lang]})
        cases.append({"fn": "getUI", "args": [lang]})
        cases.append({"fn": "getSample", "args": [lang]})
        cases.append({"fn": "relLines", "args": [lang, "Karimov Aziz Rustam o‘g‘li"]})
        for m in PERIODS:
            cases.append({"fn": "davr", "args": [lang, m]})
    # Namuna ma'lumotlarni yozuvlar orasida o'girish (til almashtirishdagi deepConvert)
    for a in ["lat", "new", "cyr"]:
        for b in ["lat", "new", "cyr"]:
            if a != b:
                cases.append({"fn": "deepConvertSample", "args": [a, b]})
    # Lug'atdagi barcha satrlar — keng qamrovli tekshiruv
    strings: list[str] = []

    def walk(o: Any) -> None:
        if isinstance(o, str):
            strings.append(o)
        elif isinstance(o, list):
            for x in o:
                walk(x)
        elif isinstance(o, dict):
            for x in o.values():
                walk(x)

    for d in (uz_lat.TL, uz_lat.UI, uz_lat.SAMPLE, uz_lat.SITE):
        walk(d)
    for s in sorted(set(strings)):
        cases.append({"fn": "lat2cyr", "args": [s]})
        cases.append({"fn": "lat2new", "args": [s]})
        cases.append({"fn": "convertScript", "args": [s, "cyr", "lat"]})
    return cases
