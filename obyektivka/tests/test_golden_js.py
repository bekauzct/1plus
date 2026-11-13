"""Python port prototipdagi JS funksiyalar bilan belgima-belgi bir xil natija beradi."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest

from apps.obyektivka import translit
from apps.obyektivka.i18n import NOCONV, get_sample, get_tl, get_ui, uz_cyr
from tests.golden_cases import build_cases

ROOT = Path(__file__).resolve().parent.parent
GOLDEN = json.loads((ROOT / "tests" / "fixtures" / "js_golden.json").read_text(encoding="utf-8"))


def _sample_without_lang(lang: str) -> dict[str, Any]:
    d = get_sample(lang)
    d.pop("lang")
    return d


def py_call(fn: str, args: list[Any]) -> Any:
    if fn == "lat2cyr":
        return translit.lat2cyr(*args)
    if fn == "cyr2lat":
        return translit.cyr2lat(*args)
    if fn == "lat2new":
        return translit.lat2new(*args)
    if fn == "new2lat":
        return translit.new2lat(*args)
    if fn == "convertScript":
        return translit.convert_script(*args)
    if fn == "getTL":
        return dict(get_tl(args[0]))
    if fn == "getUI":
        return get_ui(args[0])
    if fn == "getSample":
        return _sample_without_lang(args[0])
    if fn == "davr":
        m = args[1]
        return get_tl(args[0]).davr(m.get("dan"), m.get("gacha"))
    if fn == "relLines":
        return get_tl(args[0]).rel_lines(args[1])
    if fn == "deepConvertSample":
        src, dst = args
        return translit.deep_convert(_sample_without_lang(src), src, dst, NOCONV)
    raise AssertionError(fn)


def _subset(expected: Any, actual: Any) -> bool:
    """UI lug'atiga sayt uchun yangi kalitlar qo'shilgan — prototipdagi kalitlar aynan bir xil bo'lsin."""
    if isinstance(expected, dict) and isinstance(actual, dict):
        return all(k in actual and actual[k] == v for k, v in expected.items())
    return bool(expected == actual)


@pytest.mark.parametrize("case", GOLDEN, ids=lambda c: f"{c['fn']}:{str(c['args'])[:40]}")
def test_matches_prototype(case: dict[str, Any]) -> None:
    actual = py_call(case["fn"], case["args"])
    expected = case["expected"]
    if case["fn"] in ("getUI", "getTL", "getSample") and case["args"][0] == "cyr":
        # Kirill lug'atlari: prototip natijasi + hujjatlashtirilgan tuzatishlar (uz_cyr.FIXUPS, masalan ПДФ -> PDF)
        expected = uz_cyr._fix(expected)
    if case["fn"] == "getUI":
        assert _subset(expected, actual)
    else:
        assert actual == expected


def test_fixture_is_up_to_date() -> None:
    """Holatlar ro'yxati o'zgarsa, fixture qayta hosil qilinishi kerak."""
    cases = [{"fn": c["fn"], "args": c["args"]} for c in GOLDEN]
    assert cases == build_cases(), "uv run python scripts/gen_golden.py ni ishga tushiring"


@pytest.mark.skipif(shutil.which("node") is None, reason="node o'rnatilmagan")
def test_fixture_matches_live_js() -> None:
    """Fixture haqiqatan prototipdagi JS chiqishi ekanini tekshiradi (node bo'lsa)."""
    cases = [{"fn": c["fn"], "args": c["args"]} for c in GOLDEN]
    proc = subprocess.run(
        ["node", str(ROOT / "scripts" / "js_reference.mjs")],
        input=json.dumps(cases, ensure_ascii=False),
        capture_output=True,
        text=True,
        check=True,
    )
    assert json.loads(proc.stdout) == [c["expected"] for c in GOLDEN]
