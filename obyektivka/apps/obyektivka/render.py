"""Obyektivka render: HTML preview, PDF (WeasyPrint) va DOCX (python-docx).

Bu modul HTTP'dan mustaqil: kirish — ``schemas.Obyektivka``, chiqish — str/bytes.
Shu sababli kelajakda Telegram bot, rezyume generatori va boshqalar ham aynan shu
funksiyalardan foydalanadi (``render_preview_html``, ``render_pdf``, ``render_docx``).

Preview va PDF bitta shablondan chiqadi: ``templates/obyektivka/document.html``
va bitta stil fayli: ``static/css/document.css``.
"""

from __future__ import annotations

import io
import re
from pathlib import Path
from typing import Any, Literal
from urllib.parse import unquote, urlparse

from django.conf import settings
from django.template.loader import render_to_string
from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Emu, Pt, Twips
from docx.table import Table, _Cell
from docx.text.paragraph import Paragraph

from .i18n import Labels, get_lang, get_tl, get_ui
from .schemas import Obyektivka, has

Mode = Literal["preview", "pdf"]

STATIC_DIR = Path(settings.BASE_DIR) / "static"
DOCUMENT_CSS = STATIC_DIR / "css" / "document.css"


# ---------------------------------------------------------------------------
# Umumiy kontekst
# ---------------------------------------------------------------------------
def display_fish(d: Obyektivka, tl: Labels) -> str:
    return d.fish if has(d.fish) else str(tl["blankName"])


def document_context(d: Obyektivka, mode: Mode) -> dict[str, Any]:
    tl = get_tl(d.lang)
    fish = display_fish(d, tl)
    return {
        "d": d,
        "T": tl,
        "U": get_ui(d.lang),
        "mode": mode,
        "html_lang": get_lang(d.lang).html_lang,
        "fish": fish,
        "rel_lines": tl.rel_lines(fish),
        "mehnat": [
            {"i": i, "m": m, "davr": tl.davr(m.dan, m.gacha)} for i, m in enumerate(d.mehnat) if m.is_filled()
        ],
        "qarindosh": [
            {"i": i, "r": r, "tug": "\n".join(x for x in (r.yil, r.joy) if has(x))}
            for i, r in enumerate(d.qarindosh)
            if r.is_filled()
        ],
    }


def render_preview_html(d: Obyektivka) -> str:
    """O'ng paneldagi A4 varaqlar (HTMX fragment)."""
    return render_to_string("obyektivka/document.html", document_context(d, "preview"))


# ---------------------------------------------------------------------------
# PDF
# ---------------------------------------------------------------------------
def _make_url_fetcher() -> Any:
    """WeasyPrint faqat data: URL va static/ ichidagi fayllarni o'qiy oladi (SSRF/LFI himoyasi)."""
    from weasyprint.urls import URLFetcher

    static_root = STATIC_DIR.resolve()

    class SafeURLFetcher(URLFetcher):  # type: ignore[misc]
        def fetch(self, url: str, headers: Any = None) -> Any:
            parsed = urlparse(url)
            if parsed.scheme == "file":
                path = Path(unquote(parsed.path)).resolve()
                if not (path.is_relative_to(static_root) and path.is_file()):
                    raise ValueError("Ruxsat etilmagan fayl")
            elif parsed.scheme != "data":
                raise ValueError("Ruxsat etilmagan protokol")
            return super().fetch(url, headers)

    return SafeURLFetcher(allowed_protocols=("data", "file"), allow_redirects=False)


def render_pdf(d: Obyektivka) -> bytes:
    from weasyprint import CSS, HTML
    from weasyprint.text.fonts import FontConfiguration

    ctx = document_context(d, "pdf")
    html = render_to_string("obyektivka/document_pdf.html", ctx)
    fonts = FontConfiguration()
    fetcher = _make_url_fetcher()
    css = CSS(filename=str(DOCUMENT_CSS), font_config=fonts, url_fetcher=fetcher)
    doc = HTML(string=html, base_url=STATIC_DIR.as_uri() + "/", url_fetcher=fetcher)
    pdf: bytes = doc.write_pdf(stylesheets=[css], font_config=fonts)
    return pdf


# ---------------------------------------------------------------------------
# DOCX — prototipdagi buildDocxFiles bilan bir xil tuzilish
# ---------------------------------------------------------------------------
PHOTO_CX, PHOTO_CY = 987552, 1316736  # 1.08in x 1.44in (EMU)


def _set_cell_margins(table: Table) -> None:
    tbl_pr = table._tbl.tblPr
    mar = OxmlElement("w:tblCellMar")
    for side, w in (("top", 40), ("left", 80), ("bottom", 40), ("right", 80)):
        el = OxmlElement(f"w:{side}")
        el.set(qn("w:w"), str(w))
        el.set(qn("w:type"), "dxa")
        mar.append(el)
    tbl_pr.append(mar)


def _set_borders(table: Table, on: bool) -> None:
    tbl_pr = table._tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for side in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement(f"w:{side}")
        if on:
            el.set(qn("w:val"), "single")
            el.set(qn("w:sz"), "4")
            el.set(qn("w:space"), "0")
            el.set(qn("w:color"), "000000")
        else:
            el.set(qn("w:val"), "nil")
        borders.append(el)
    tbl_pr.append(borders)


def _table(doc: Any, widths: list[int], n_rows: int, border: bool = False) -> Table:
    table = doc.add_table(rows=n_rows, cols=len(widths))
    table.alignment = WD_TABLE_ALIGNMENT.LEFT
    table.autofit = False
    tbl_pr = table._tbl.tblPr
    tbl_w = tbl_pr.find(qn("w:tblW"))
    if tbl_w is None:
        tbl_w = OxmlElement("w:tblW")
        tbl_pr.append(tbl_w)
    tbl_w.set(qn("w:w"), str(sum(widths)))
    tbl_w.set(qn("w:type"), "dxa")
    style = tbl_pr.find(qn("w:tblStyle"))
    if style is not None:
        tbl_pr.remove(style)
    _set_borders(table, border)
    layout = OxmlElement("w:tblLayout")
    layout.set(qn("w:type"), "fixed")
    tbl_pr.append(layout)
    _set_cell_margins(table)
    grid = table._tbl.tblGrid
    for col, w in zip(grid.findall(qn("w:gridCol")), widths, strict=True):
        col.set(qn("w:w"), str(w))
    for row in table.rows:
        for cell, w in zip(row.cells, widths, strict=True):
            cell.width = Twips(w)
    return table


def _add_runs(p: Paragraph, text: str, b: bool = False, u: bool = False, sz: int | None = None) -> None:
    """Prototipdagi run(): har bir qator alohida run, keyingilari oldidan <w:br/>."""
    for i, line in enumerate(("" if text is None else str(text)).split("\n")):
        r = p.add_run()
        if i:
            r.add_break(WD_BREAK.LINE)
        r.add_text(line)
        r.bold = b or None
        if u:
            r.underline = True
        if sz:
            r.font.size = Pt(sz / 2)


def _fmt(
    p: Paragraph, before: int = 0, after: int = 0, jc: str | None = None, page_break: bool = False
) -> Paragraph:
    pf = p.paragraph_format
    pf.space_before = Twips(before)
    pf.space_after = Twips(after)
    if jc:
        pf.alignment = {
            "center": WD_ALIGN_PARAGRAPH.CENTER,
            "right": WD_ALIGN_PARAGRAPH.RIGHT,
            "both": WD_ALIGN_PARAGRAPH.JUSTIFY,
        }[jc]
    if page_break:
        pf.page_break_before = True
    return p


def _cell_p(
    cell: _Cell, text: str = "", first: bool = True, **fmt: Any
) -> Paragraph:  # first: katakdagi mavjud bo'sh paragrafdan foydalanish
    p = cell.paragraphs[0] if first else cell.add_paragraph()
    run_opts = {k: fmt.pop(k) for k in ("b", "u", "sz") if k in fmt}
    _add_runs(p, text, **run_opts)
    return _fmt(p, **fmt)


def _v(x: object) -> str:
    return str(x) if has(x) else ""


def render_docx(d: Obyektivka) -> bytes:
    tl = get_tl(d.lang)
    lang = get_lang(d.lang)
    fish = display_fish(d, tl)
    doc = Document()

    # --- Sahifa: A4, chegaralar (twips) ---
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Twips(11906), Twips(16838)
    sec.top_margin, sec.right_margin = Twips(1000), Twips(850)
    sec.bottom_margin, sec.left_margin = Twips(1000), Twips(1300)
    sec.header_distance = sec.footer_distance = Twips(0)
    sec.gutter = Twips(0)

    # --- Standart shrift va til ---
    normal = doc.styles["Normal"]
    normal.font.name = "Times New Roman"
    normal.font.size = Pt(12)
    rpr = normal.element.get_or_add_rPr()
    fonts = rpr.find(qn("w:rFonts"))
    if fonts is None:
        fonts = OxmlElement("w:rFonts")
        rpr.append(fonts)
    for attr in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        fonts.set(qn(attr), "Times New Roman")
    lang_el = OxmlElement("w:lang")
    lang_el.set(qn("w:val"), lang.docx_lang)
    rpr.append(lang_el)
    npf = normal.paragraph_format
    npf.space_after = Twips(0)
    npf.space_before = Twips(0)
    npf.line_spacing = 1.0

    # Document() bo'sh paragraf bilan boshlanadi — olib tashlaymiz
    body = doc.element.body
    for p_el in list(body.findall(qn("w:p"))):
        body.remove(p_el)

    # --- Sarlavha + rasm ---
    head = _table(doc, [7600, 2000], 1)
    c0, c1 = head.rows[0].cells
    for c in (c0, c1):
        c.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
    _cell_p(c0, "", after=300)
    _cell_p(c0, str(tl["title"]), first=False, b=True, u=True, sz=28, jc="center")
    _cell_p(c0, fish, first=False, b=True, u=True, sz=26, jc="center")
    photo = d.photo_bytes()
    p_img = c1.paragraphs[0]
    _fmt(p_img, jc="right")
    if photo:
        p_img.add_run().add_picture(io.BytesIO(photo), width=Emu(PHOTO_CX), height=Emu(PHOTO_CY))
    else:
        _add_runs(p_img, str(tl["photo"]))

    # --- Lavozim ---
    _fmt(doc.add_paragraph(), before=200, after=120, jc="both")
    _add_runs(doc.paragraphs[-1], _v(d.lavozim))

    # --- Ma'lumotlar jadvali ---
    rows = [
        (tl["tugYil"], d.tugSana, tl["tugJoy"], d.tugJoy),
        (tl["millati"], d.millati, tl["partiya"], d.partiya),
        (tl["malumoti"], d.malumoti, tl["tamomlagan"], d.tamomlagan),
        (tl["mutax"], d.mutaxassislik, None, None),
        (tl["ilmiyD"], d.ilmiyDaraja, tl["ilmiyU"], d.ilmiyUnvon),
    ]
    info = _table(doc, [1700, 2300, 1700, 3900], len(rows))
    for r_i, (l1, v1, l2, v2) in enumerate(rows):
        cells = info.rows[r_i].cells
        _cell_p(cells[0], str(l1), b=True)
        _cell_p(cells[1], _v(v1))
        if l2 is not None:
            _cell_p(cells[2], str(l2), b=True)
            _cell_p(cells[3], _v(v2))

    # --- Savol-javoblar ---
    for q, a in ((tl["qTil"], d.tillar), (tl["qMuk"], d.mukofot), (tl["qDep"], d.deputat)):
        p = doc.add_paragraph()
        _add_runs(p, str(q), b=True)
        _fmt(p, before=120)
        p = doc.add_paragraph()
        _add_runs(p, _v(a))
        _fmt(p)

    # --- Mehnat faoliyati ---
    p = doc.add_paragraph()
    _add_runs(p, str(tl["mehnat"]), b=True)
    _fmt(p, jc="center", before=240, after=120)
    mehnat = d.filled_mehnat()
    if mehnat:
        mt = _table(doc, [2200, 7400], len(mehnat))
        for r_i, m in enumerate(mehnat):
            cells = mt.rows[r_i].cells
            _cell_p(cells[0], tl.davr(m.dan, m.gacha))
            _cell_p(cells[1], "– " + _v(m.matn), jc="both")

    # --- 2-sahifa: qarindoshlar ---
    rl = tl.rel_lines(fish)
    p = doc.add_paragraph()
    _add_runs(p, rl[0], b=True)
    _fmt(p, jc="center", page_break=True)
    p = doc.add_paragraph()
    _add_runs(p, rl[1], b=True)
    _fmt(p, jc="center", after=200)

    rel = d.filled_qarindosh()
    rt = _table(doc, [1750, 1950, 1950, 1900, 2050], 1 + len(rel), border=True)
    header = rt.rows[0]
    # Sarlavha qatori har sahifada takrorlanadi
    tr_pr = header._tr.get_or_add_trPr()
    tbl_header = OxmlElement("w:tblHeader")
    tr_pr.append(tbl_header)
    for cell, t in zip(header.cells, ("thRel", "thFish", "thTug", "thIsh", "thTur"), strict=True):
        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        _cell_p(cell, str(tl[t]), b=True, sz=22, jc="center")
    for r_i, r in enumerate(rel, start=1):
        tug = "\n".join(x for x in (_v(r.yil), _v(r.joy)) if x)
        row = rt.rows[r_i]
        tr_pr = row._tr.get_or_add_trPr()
        cant = OxmlElement("w:cantSplit")
        tr_pr.append(cant)
        for cell, t in zip(row.cells, (r.rel, r.fish, tug, r.ish, r.turar), strict=True):
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            _cell_p(cell, _v(t), sz=22, jc="center")

    # Hujjat xususiyatlari: shaxsiy ma'lumot qo'ymaymiz
    cp = doc.core_properties
    cp.author = ""
    cp.last_modified_by = ""
    cp.title = str(tl["title"])
    cp.comments = ""

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Fayl nomi
# ---------------------------------------------------------------------------
_BAD_FN = re.compile(r'[\\/:*?"<>|\x00-\x1f]+')


def export_filename(d: Obyektivka, ext: str) -> str:
    """Prototip: ``Familiya_Ism_obyektivka.pdf``."""
    base = d.fish if has(d.fish) else str(get_ui(d.lang)["fname"])
    name = re.sub(r"\s+", "_", _BAD_FN.sub("", base).strip())[:120] or "obyektivka"
    return f"{name}_obyektivka.{ext}"
