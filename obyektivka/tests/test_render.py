"""render.py: preview HTML, PDF (pypdf bilan) va DOCX (python-docx bilan qayta ochib) tekshiruvi."""

import io

import pytest
from docx import Document
from pypdf import PdfReader

from apps.obyektivka.i18n import get_sample, get_tl
from apps.obyektivka.render import export_filename, render_docx, render_pdf, render_preview_html
from apps.obyektivka.schemas import Obyektivka

LANGS = ["new", "lat", "cyr", "ru"]


def _sample(lang: str, **kw: object) -> Obyektivka:
    data = get_sample(lang)
    data.update(kw)
    return Obyektivka.model_validate(data)


def _pdf_text(pdf: bytes) -> tuple[int, list[str]]:
    r = PdfReader(io.BytesIO(pdf))
    return len(r.pages), [" ".join((p.extract_text() or "").split()) for p in r.pages]


def _docx_text(blob: bytes) -> str:
    doc = Document(io.BytesIO(blob))
    parts = [p.text for p in doc.paragraphs]
    for t in doc.tables:
        for row in t.rows:
            for c in row.cells:
                parts.append(c.text)
    return "\n".join(parts)


@pytest.mark.parametrize("lang", LANGS)
def test_pdf_two_pages_with_fish(lang: str) -> None:
    d = _sample(lang)
    pages, texts = _pdf_text(render_pdf(d))
    assert pages == 2
    assert d.fish in texts[0]
    tl = get_tl(lang)
    assert tl["title"] in texts[0]
    assert tl["thRel"] in texts[1]
    assert d.qarindosh[0].fish in texts[1]


def test_pdf_with_photo(photo_data_url: str) -> None:
    pdf = render_pdf(_sample("lat", photo=photo_data_url))
    r = PdfReader(io.BytesIO(pdf))
    assert len(r.pages) == 2
    assert len(r.pages[0].images) == 1


def test_pdf_empty_document_still_two_pages() -> None:
    pages, texts = _pdf_text(render_pdf(Obyektivka()))
    assert pages == 2
    assert "________________" in texts[1]


def test_pdf_long_relatives_table_repeats_header() -> None:
    rels = [
        {"rel": f"Qarindosh {i}", "fish": f"Familiya{i} Ism Otasining ismi", "yil": "1970",
         "joy": "Toshkent viloyati, Chirchiq shahri", "ish": "Tashkilot\nlavozim", "turar": "Viloyat, tuman, mahalla, uy " * 3}
        for i in range(30)
    ]  # fmt: skip
    pages, texts = _pdf_text(render_pdf(_sample("lat", qarindosh=rels)))
    assert pages >= 3
    for t in texts[1:]:
        assert "Qarindoshligi" in t  # sarlavha qatori har sahifada
    joined = " ".join(texts)
    assert "Familiya29" in joined


def test_pdf_long_mehnat_flows_to_next_page() -> None:
    mehnat = [
        {"dan": str(1990 + i), "gacha": str(1991 + i), "matn": "Juda uzun tashkilot nomi va lavozim " * 4}
        for i in range(30)
    ]
    pages, texts = _pdf_text(render_pdf(_sample("lat", mehnat=mehnat)))
    assert pages >= 3
    assert "2019-2020 yy." in " ".join(texts)
    # qarindoshlar har doim yangi sahifadan boshlanadi
    assert any(t.startswith("Karimov Aziz Rustam o‘g‘lining") for t in texts[1:])


@pytest.mark.parametrize("lang", LANGS)
def test_docx_contains_texts(lang: str) -> None:
    d = _sample(lang)
    text = _docx_text(render_docx(d))
    tl = get_tl(lang)
    for needle in (
        tl["title"],
        d.fish,
        tl["mehnat"],
        tl["thFish"],
        d.qarindosh[2].fish,
        tl.davr("2024", ""),
        d.tugSana,
    ):
        assert needle in text, needle
    assert tl.rel_lines(d.fish)[0] in text


def test_docx_structure(photo_data_url: str) -> None:
    doc = Document(io.BytesIO(render_docx(_sample("cyr", photo=photo_data_url))))
    assert len(doc.tables) == 4  # sarlavha, ma'lumotlar, mehnat, qarindoshlar
    assert len(doc.inline_shapes) == 1
    sec = doc.sections[0]
    assert (sec.page_width.twips, sec.page_height.twips) == (11906, 16838)  # type: ignore[union-attr]
    assert (sec.left_margin.twips, sec.right_margin.twips) == (1300, 850)  # type: ignore[union-attr]
    rel = doc.tables[3]
    assert len(rel.rows) == 4
    xml = doc.element.xml
    assert "w:tblHeader" in xml and "w:pageBreakBefore" in xml and "w:cantSplit" in xml
    assert 'w:val="uz-Cyrl-UZ"' in doc.styles.element.xml
    assert doc.core_properties.author == ""


def test_docx_without_mehnat_has_no_mehnat_table() -> None:
    doc = Document(io.BytesIO(render_docx(_sample("lat", mehnat=[]))))
    assert len(doc.tables) == 3


def test_docx_multiline_cells() -> None:
    doc = Document(io.BytesIO(render_docx(_sample("lat"))))
    assert "“Chirchiq transport” MChJ\nhaydovchi" in doc.tables[3].rows[1].cells[3].text


def test_preview_html() -> None:
    html = render_preview_html(_sample("lat", fish="<script>x</script>"))
    assert "&lt;script&gt;" in html and "<script>x" not in html
    assert 'data-p="fish"' in html and 'data-row="mehnat" data-i="1"' in html
    assert "2024 y. – h.v." in html


def test_preview_placeholders() -> None:
    html = render_preview_html(Obyektivka())
    assert "Familiya Ism Otasining ismi" in html
    assert "Mehnat faoliyati kiritilmagan" in html and "Rasm 3×4" in html


@pytest.mark.parametrize(
    ("fish", "expected"),
    [
        ("Karimov Aziz", "Karimov_Aziz_obyektivka.pdf"),
        ("", "obyektivka_obyektivka.pdf"),
        ('a/b:c*?"', "abc_obyektivka.pdf"),
    ],
)
def test_filename(fish: str, expected: str) -> None:
    assert export_filename(Obyektivka(fish=fish), "pdf") == expected


def test_pdf_uses_bundled_tinos_font() -> None:
    r = PdfReader(io.BytesIO(render_pdf(_sample("lat"))))
    fonts = set()
    for page in r.pages:
        for f in page["/Resources"]["/Font"].values():
            fonts.add(str(f.get_object()["/BaseFont"]))
    assert any("Tinos" in f for f in fonts), fonts


def test_pdf_fetcher_blocks_external_and_local_files() -> None:
    from apps.obyektivka.render import _make_url_fetcher

    fetcher = _make_url_fetcher()
    for url in ("http://169.254.169.254/latest", "file:///etc/passwd", "https://example.com/x.png"):
        with pytest.raises(ValueError):
            fetcher.fetch(url)
