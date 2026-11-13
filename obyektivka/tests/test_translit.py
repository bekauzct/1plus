"""Transliteratsiya: talab qilingan so'zlar, round-trip va chegaraviy holatlar."""

import pytest

from apps.obyektivka.translit import convert_script, cyr2lat, deep_convert, lat2cyr, lat2new, new2lat


@pytest.mark.parametrize(
    ("lat", "cyr"),
    [
        ("o‘g‘li", "ўғли"),
        ("o'g'li", "ўғли"),
        ("Yo‘q", "Йўқ"),
        ("MA’LUMOT", "МАЪЛУМОТ"),
        ("Yevropa", "Европа"),
        ("SHAHAR", "ШАҲАР"),
        ("Elektr", "Электр"),
        ("metro", "метро"),
        ("Chirchiq", "Чирчиқ"),
        ("san’at", "санъат"),
    ],
)
def test_lat2cyr(lat: str, cyr: str) -> None:
    assert lat2cyr(lat) == cyr


@pytest.mark.parametrize(
    ("lat", "new"),
    [
        ("o‘g‘li", "öğli"),
        ("Yo‘q", "Yöq"),
        ("SHAHAR", "ŞAHAR"),
        ("Shahar", "Şahar"),
        ("choy", "çoy"),
        ("MA’LUMOT", "MA’LUMOT"),
    ],
)
def test_lat2new(lat: str, new: str) -> None:
    assert lat2new(lat) == new


# Round-trip: apostrof variantlari ‘ ' ` -> ʻ ga normallashadi, shuning uchun oʻ/gʻ bilan solishtiramiz
@pytest.mark.parametrize(
    ("src", "back"),
    [
        ("oʻgʻli", "oʻgʻli"),
        ("o'g'li", "oʻgʻli"),
        ("Yoʻq", "Yoʻq"),
        ("Yo‘q", "Yoʻq"),
        ("MAʼLUMOT", "MAʼLUMOT"),
        ("Yevropa", "Yevropa"),
        ("SHAHAR", "SHAHAR"),
        ("Toshkent viloyati, Chirchiq shahri", "Toshkent viloyati, Chirchiq shahri"),
    ],
)
def test_round_trip_lat_cyr_lat(src: str, back: str) -> None:
    assert cyr2lat(lat2cyr(src)) == back


@pytest.mark.parametrize(
    "src", ["oʻgʻli", "Yoʻq", "MAʼLUMOT", "Yevropa", "SHAHAR", "Shahar", "CHIRCHIQ", "Chirchiq"]
)
def test_round_trip_lat_new_lat(src: str) -> None:
    assert new2lat(lat2new(src)) == src


def test_convert_same_script_is_identity() -> None:
    assert convert_script("Yo'q", "lat", "lat") == "Yo'q"


def test_ru_is_passthrough() -> None:
    assert convert_script("Привет", "ru", "lat") == "Привет"


def test_none_and_numbers() -> None:
    assert lat2cyr(None) == ""
    assert cyr2lat("12.03.2006") == "12.03.2006"


def test_deep_convert_skips_keys() -> None:
    data = {
        "fish": "Yo‘q",
        "tugSana": "12.03.2006",
        "photo": "data:x",
        "list": [{"photo": "Yo‘q", "a": "Yo‘q"}],
    }
    out = deep_convert(data, "lat", "cyr", ["photo", "tugSana"])
    assert out == {
        "fish": "Йўқ",
        "tugSana": "12.03.2006",
        "photo": "data:x",
        "list": [{"photo": "Yo‘q", "a": "Йўқ"}],
    }
    assert data["fish"] == "Yo‘q"  # asl ma'lumot o'zgarmaydi
