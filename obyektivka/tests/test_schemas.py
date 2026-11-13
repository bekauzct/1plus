"""pydantic modellari: sana va yil validatsiyasi, rasm turi, yengil (lenient) rejim."""

import base64
import io

import pytest
from PIL import Image
from pydantic import ValidationError

from apps.obyektivka.i18n import get_sample
from apps.obyektivka.schemas import Obyektivka, errors_for_client, lenient, parse_birth_date


def _img(fmt: str = "JPEG") -> str:
    buf = io.BytesIO()
    Image.new("RGB", (30, 40), "white").save(buf, fmt)
    mime = {"JPEG": "image/jpeg", "PNG": "image/png", "GIF": "image/gif"}[fmt]
    return f"data:{mime};base64," + base64.b64encode(buf.getvalue()).decode()


@pytest.mark.parametrize("lang", ["new", "lat", "cyr", "ru"])
def test_sample_is_valid(lang: str) -> None:
    m = Obyektivka.model_validate(get_sample(lang))
    assert m.lang == lang
    assert len(m.filled_mehnat()) == 2
    assert len(m.filled_qarindosh()) == 3


@pytest.mark.parametrize("value", ["", "12.03.2006", "29.02.2000", "01.01.1950"])
def test_date_ok(value: str) -> None:
    assert Obyektivka(tugSana=value).tugSana == value


@pytest.mark.parametrize(
    "value",
    [
        "12.03",
        "1203.2006",
        "31.02.2006",
        "12/03/2006",
        "00.01.2000",
        "12.13.2000",
        "01.01.1800",
        "01.01.2999",
    ],
)
def test_date_invalid(value: str) -> None:
    with pytest.raises(ValidationError) as e:
        Obyektivka(tugSana=value)
    assert errors_for_client(e.value) == [{"loc": "tugSana", "key": "errDate"}]


def test_parse_birth_date() -> None:
    assert parse_birth_date("12.03.2006").isoformat() == "2006-03-12"  # type: ignore[union-attr]
    assert parse_birth_date("  ") is None


def test_years() -> None:
    Obyektivka.model_validate({"mehnat": [{"dan": "2020", "gacha": ""}], "qarindosh": [{"yil": "1976"}]})
    with pytest.raises(ValidationError) as e:
        Obyektivka.model_validate({"mehnat": [{"dan": "20", "gacha": "abcd"}]})
    locs = {x["loc"] for x in errors_for_client(e.value)}
    assert locs == {"mehnat.0.dan", "mehnat.0.gacha"}


def test_numbers_and_nulls_are_coerced() -> None:
    m = Obyektivka.model_validate({"fish": None, "qarindosh": [{"yil": 1976, "fish": None}]})
    assert m.fish == "" and m.qarindosh[0].yil == "1976"


def test_unknown_lang_falls_back() -> None:
    assert Obyektivka.model_validate({"lang": "xx"}).lang == "lat"


@pytest.mark.parametrize("fmt", ["JPEG", "PNG"])
def test_photo_ok(fmt: str) -> None:
    m = Obyektivka(photo=_img(fmt))
    assert m.photo_bytes()


@pytest.mark.parametrize(
    "photo",
    [
        _img("GIF").replace("image/gif", "image/png"),  # yolg'on MIME
        "data:image/png;base64,AAAA",
        "data:text/html;base64,PHNjcmlwdD4=",
        "javascript:alert(1)",
    ],
)
def test_photo_rejected(photo: str) -> None:
    with pytest.raises(ValidationError) as e:
        Obyektivka(photo=photo)
    assert errors_for_client(e.value)[0]["key"] == "tPhotoType"


def test_lenient_keeps_text_drops_bad_photo() -> None:
    m = lenient(
        {
            "fish": "Ali",
            "tugSana": "12.0",
            "photo": "data:image/png;base64,AAAA",
            "mehnat": [{"dan": "20", "matn": "X"}],
        }
    )
    assert m.fish == "Ali" and m.tugSana == "12.0" and m.photo == ""
    assert m.mehnat[0].dan == "20" and m.filled_mehnat()


def test_lenient_garbage() -> None:
    assert lenient("nope").fish == ""
    assert lenient({"mehnat": "x", "qarindosh": [1, {"fish": "A"}]}).qarindosh[0].fish == "A"


def test_limits() -> None:
    with pytest.raises(ValidationError):
        Obyektivka(fish="x" * 1000)
    with pytest.raises(ValidationError):
        Obyektivka.model_validate({"mehnat": [{}] * 100})
