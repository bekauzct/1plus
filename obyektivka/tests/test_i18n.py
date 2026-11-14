"""i18n: davr formatlash va lug'atlar."""

import pytest

from apps.obyektivka.i18n import LANGS, PREFIX_TO_CODE, get_sample, get_site, get_tl, get_ui


@pytest.mark.parametrize(
    ("lang", "dan", "gacha", "expected"),
    [
        ("lat", "2021", "2024", "2021-2024 yy."),
        ("lat", "2024", "", "2024 y. – h.v."),
        ("new", "2024", "", "2024 y. – h.v."),
        ("cyr", "2021", "2024", "2021-2024 йй."),
        ("cyr", "2024", "", "2024 й. – ҳ.в."),
        ("ru", "2021", "2024", "2021-2024 гг."),
        ("ru", "2024", "", "2024 г. – по н.в."),
        ("lat", "", "", ""),
        ("lat", " 2020 ", None, "2020 y. – h.v."),
    ],
)
def test_davr(lang: str, dan: str, gacha: str | None, expected: str) -> None:
    assert get_tl(lang).davr(dan, gacha) == expected


def test_rel_lines() -> None:
    assert get_tl("lat").rel_lines("Karimov A.") == ["Karimov A.ning yaqin qarindoshlari haqida", "MA’LUMOT"]
    assert get_tl("ru").rel_lines("Каримов А.") == ["СВЕДЕНИЯ", "о близких родственниках Каримов А."]
    assert get_tl("cyr")["title"] == "Маълумотнома"


def test_all_languages_have_same_keys() -> None:
    base_ui, base_tl, base_site = set(get_ui("lat")), set(get_tl("lat")), set(get_site("lat"))
    for code in LANGS:
        assert set(get_ui(code)) == base_ui, code
        assert set(get_tl(code)) - {"relPre", "relSfx"} == base_tl - {"relSfx"}, code
        assert set(get_site(code)) == base_site, code
        assert len(get_site(code)["faq"]) == len(get_site("lat")["faq"])


def test_prefixes() -> None:
    assert PREFIX_TO_CODE == {"uz": "new", "uzb": "lat", "kr": "cyr", "ru": "ru"}


def test_cyr_fixups() -> None:
    site = get_site("cyr")
    assert "Объективка" in site["metaTitle"] or "объективка" in site["metaTitle"].lower()
    assert "ЖСОН" not in str(site)
    assert get_ui("cyr")["fname"] == "obyektivka"


def test_sample_is_fresh_copy() -> None:
    a = get_sample("lat")
    a["mehnat"].append({})
    assert len(get_sample("lat")["mehnat"]) == 2
