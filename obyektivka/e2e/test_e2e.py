"""E2E: namuna -> 4 til -> PDF va DOCX yuklab olish; mobil tablar; JSON eksport/import."""

import io
import json
import re

import pytest
from docx import Document
from pypdf import PdfReader

pytestmark = [pytest.mark.e2e, pytest.mark.django_db(transaction=True)]

LANGS = [  # (prefiks, til tugmasi, F.I.Sh. namunada, qarindosh sarlavhasi)
    ("uzb", "lat", "Karimov Aziz Rustam o‘g‘li", "Qarindoshligi"),
    ("kr", "cyr", "Каримов Азиз Рустам ўғли", "Қариндошлиги"),
    ("uz", "new", "Karimov Aziz Rustam öğli", "Qarindoşligi"),
    ("ru", "ru", "Karimov Aziz Rustam öğli", "Степень родства"),  # rus tiliga o‘tganda matn o‘girilmaydi
]


def _wait_preview(page, text: str) -> None:  # type: ignore[no-untyped-def]
    page.wait_for_function(
        "t => document.querySelector('#preview') && document.querySelector('#preview').innerText.includes(t)",
        arg=text,
        timeout=10_000,
    )


def _download(page, button: str) -> bytes:  # type: ignore[no-untyped-def]
    with page.expect_download(timeout=30_000) as dl:
        page.click(button)
    path = dl.value.path()
    assert path
    with open(path, "rb") as fh:
        return fh.read(), dl.value.suggested_filename


def test_sample_four_languages_pdf_docx(page) -> None:  # type: ignore[no-untyped-def]
    page.goto(page.base + "/uzb/obyektivka/")
    page.get_by_role("button", name="Namuna bilan to‘ldirish").first.click()
    _wait_preview(page, "Karimov Aziz Rustam o‘g‘li")

    for prefix, code, fish, th in LANGS:
        page.click(f'nav.seg a[data-lang="{code}"]')
        page.wait_for_url(re.compile(f"/{prefix}/obyektivka/$"))
        _wait_preview(page, fish)
        _wait_preview(page, th)
        assert page.input_value("#f-fish") == fish

        pdf, pdf_name = _download(page, "#btnPdf")
        reader = PdfReader(io.BytesIO(pdf))
        assert len(reader.pages) == 2
        assert fish in " ".join(reader.pages[0].extract_text().split())
        assert pdf_name.endswith("_obyektivka.pdf")

        docx, docx_name = _download(page, "#btnDocx")
        doc = Document(io.BytesIO(docx))
        cells = " ".join(c.text for t in doc.tables for row in t.rows for c in row.cells)
        assert fish in cells and th in cells
        assert docx_name.endswith("_obyektivka.docx")


def test_language_switch_undo(page) -> None:  # type: ignore[no-untyped-def]
    page.goto(page.base + "/uzb/obyektivka/")
    page.fill("#f-fish", "Yo‘ldoshev Shoh")
    _wait_preview(page, "Yo‘ldoshev Shoh")
    page.click('nav.seg a[data-lang="cyr"]')
    page.wait_for_url(re.compile("/kr/obyektivka/$"))
    _wait_preview(page, "Йўлдошев Шоҳ")
    page.get_by_role("button", name="Қайтариш").click()
    page.wait_for_url(re.compile("/uzb/obyektivka/$"))
    assert page.input_value("#f-fish") == "Yo‘ldoshev Shoh"


def test_live_preview_flash_and_lists(page) -> None:  # type: ignore[no-untyped-def]
    page.goto(page.base + "/uzb/obyektivka/")
    page.fill("#f-lavozim", "Bosh mutaxassis")
    _wait_preview(page, "Bosh mutaxassis")
    page.wait_for_selector('#preview [data-p="lavozim"].flash')
    # Mehnat: qo'shish va tartiblash
    page.click("summary:has-text('Mehnat faoliyati')")
    page.locator("[data-m=dan]").first.fill("2015")
    page.locator("[data-m=gacha]").first.fill("2018")
    page.locator("[data-m=matn]").first.fill("Birinchi ish")
    page.get_by_role("button", name="+ Davr qo‘shish").click()
    assert page.locator("[data-m=dan]").nth(1).input_value() == "2018"  # oldingi "gacha"dan
    page.locator("[data-m=matn]").nth(1).fill("Ikkinchi ish")
    _wait_preview(page, "2018 y. – h.v.")
    page.locator(".row-card").nth(1).get_by_role("button", name="Yuqoriga").click()
    page.wait_for_function(
        "() => document.querySelector('#preview .p-mehnat tr td:last-child').innerText.includes('Ikkinchi')"
    )
    page.locator(".row-card").first.get_by_role("button", name="O‘chirish").click()
    page.wait_for_function("() => !document.querySelector('#preview').innerText.includes('Ikkinchi')")


def test_date_mask_and_validation(page) -> None:  # type: ignore[no-untyped-def]
    page.goto(page.base + "/uzb/obyektivka/")
    page.locator("#f-tugSana").press_sequentially("31022000")
    assert page.input_value("#f-tugSana") == "31.02.2000"
    page.wait_for_selector("#err-tugSana:visible")
    page.click("#btnPdf")
    page.wait_for_selector(".toast.show")
    page.fill("#f-tugSana", "")
    page.locator("#f-tugSana").press_sequentially("12032006")
    page.locator("#f-fish").focus()
    page.wait_for_selector("#err-tugSana", state="hidden")


def test_json_export_import(page, tmp_path) -> None:  # type: ignore[no-untyped-def]
    page.goto(page.base + "/ru/obyektivka/")
    page.get_by_role("button", name="Заполнить образцом").first.click()
    _wait_preview(page, "Каримов Азиз Рустамович")
    with page.expect_download() as dl:
        page.get_by_role("button", name="JSON экспорт").click()
    with open(dl.value.path(), encoding="utf-8") as fh:
        data = json.load(fh)
    assert data["fish"] == "Каримов Азиз Рустамович" and data["lang"] == "ru"
    assert "_id" not in json.dumps(data)
    # boshqa "qurilma": yangi kontekst
    page.context.clear_cookies()
    page.evaluate("localStorage.clear()")
    page.reload()
    f = tmp_path / "d.json"
    f.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    page.set_input_files("#jsonInput", str(f))
    _wait_preview(page, "Каримов Азиз Рустамович")


def test_mobile_tabs_360(browser, live_server) -> None:  # type: ignore[no-untyped-def]
    ctx = browser.new_context(viewport={"width": 360, "height": 740}, is_mobile=True, has_touch=True)
    page = ctx.new_page()
    page.goto(live_server.url + "/uzb/obyektivka/")
    assert page.locator("#form").is_visible()
    assert not page.locator("#previewPane").is_visible()
    # gorizontal scroll yo'q
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 1")
    page.click("#tab-preview")
    assert page.locator("#previewPane").is_visible()
    assert not page.locator("#form").is_visible()
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 1")
    ctx.close()


def test_photo_upload_with_crop(page, tmp_path) -> None:  # type: ignore[no-untyped-def]
    from PIL import Image

    img = tmp_path / "p.png"
    Image.new("RGB", (900, 900), (40, 90, 160)).save(img)
    page.goto(page.base + "/uzb/obyektivka/")
    page.set_input_files("#photoInput", str(img))
    page.wait_for_selector(".crop-modal .cropper-container")
    page.get_by_role("button", name="Saqlash").click()
    page.wait_for_selector('#preview [data-p="photo"] img', timeout=10_000)
    assert page.evaluate(
        "document.querySelector('#preview [data-p=photo] img').src.startsWith('data:image/jpeg')"
    )


def test_landing(page) -> None:  # type: ignore[no-untyped-def]
    page.goto(page.base + "/")
    assert page.url.endswith("/uzb/")
    assert page.get_by_text("Ma’lumotlaringiz serverda saqlanmaydi").first.is_visible()
    page.get_by_role("link", name=re.compile("Boshlash")).first.click()
    page.wait_for_url(re.compile("/uzb/obyektivka/$"))
