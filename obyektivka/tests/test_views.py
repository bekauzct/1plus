"""Sahifalar, API endpointlar, SEO va xavfsizlik."""

import io
import json
import logging

import pytest
from django.test import Client
from docx import Document
from PIL import Image
from pypdf import PdfReader

from apps.obyektivka.i18n import get_sample

pytestmark = pytest.mark.django_db


def _post(client: Client, url: str, body: object) -> object:
    return client.post(url, data=json.dumps(body), content_type="application/json")


# ---------------- sahifalar ----------------
@pytest.mark.parametrize(("accept", "target"), [("ru-RU,ru;q=0.9", "/ru/"), ("uz", "/uzb/"), ("", "/uzb/")])
def test_root_redirect(client: Client, accept: str, target: str) -> None:
    r = client.get("/", HTTP_ACCEPT_LANGUAGE=accept)
    assert r.status_code == 302 and r["Location"] == target


@pytest.mark.parametrize(
    ("prefix", "html_lang", "needle"),
    [("uz", "uz", "Boşlaş"), ("uzb", "uz", "Boshlash"), ("kr", "uz-Cyrl", "Бошлаш"), ("ru", "ru", "Начать")],
)
def test_landing(client: Client, prefix: str, html_lang: str, needle: str) -> None:
    r = client.get(f"/{prefix}/")
    html = r.content.decode()
    assert r.status_code == 200
    assert f'<html lang="{html_lang}">' in html
    assert needle in html
    # SEO
    for hl in ("uz-Latn", "uz", "uz-Cyrl", "ru", "x-default"):
        assert f'hreflang="{hl}"' in html
    assert f'<link rel="canonical" href="http://localhost:8000/{prefix}/">' in html
    assert 'property="og:title"' in html and "application/ld+json" in html
    # namuna varaq landingda
    assert "obv-doc" in html


def test_landing_privacy_and_keywords(client: Client) -> None:
    html = client.get("/uzb/").content.decode()
    assert "Ma’lumotlaringiz serverda saqlanmaydi" in html
    assert "obyektivka namuna" in html and "ma’lumotnoma yozish" in html
    ru = client.get("/ru/").content.decode()
    assert "объективка образец" in ru.lower() and "Ваши данные не хранятся на сервере" in ru


def test_editor_page(client: Client) -> None:
    r = client.get("/kr/obyektivka/")
    html = r.content.decode()
    assert r.status_code == 200
    assert 'id="obv-boot"' in html and 'hx-post="/api/preview"' in html
    assert "csrftoken" in r.cookies
    assert 'for="f-fish"' in html and 'id="f-fish"' in html  # label'lar


def test_404(client: Client) -> None:
    r = client.get("/ru/nope/")
    assert r.status_code == 404 and "Страница не найдена" in r.content.decode()


def test_sitemap_and_robots(client: Client) -> None:
    sm = client.get("/sitemap.xml").content.decode()
    assert sm.count("<url>") == 8 and "/kr/obyektivka/" in sm and 'hreflang="uz-Cyrl"' in sm
    rb = client.get("/robots.txt").content.decode()
    assert "Disallow: /api/" in rb and "Sitemap: http://localhost:8000/sitemap.xml" in rb


# ---------------- preview ----------------
def test_preview_json(client: Client) -> None:
    r = _post(client, "/api/preview", {"data": get_sample("ru")})
    assert r.status_code == 200
    assert "Каримов Азиз Рустамович" in r.content.decode()
    assert json.loads(r["HX-Trigger"]) == {"obv-errors": {"errors": []}}
    assert r["Cache-Control"] == "no-store"


def test_preview_htmx_form_payload(client: Client) -> None:
    r = client.post(
        "/api/preview", {"payload": json.dumps({"fish": "Ali", "lang": "lat"})}, HTTP_HX_REQUEST="true"
    )
    assert r.status_code == 200 and "Ali" in r.content.decode()


def test_preview_invalid_still_renders_with_errors(client: Client) -> None:
    r = _post(client, "/api/preview", {"fish": "Vali", "tugSana": "31.02.2000", "mehnat": [{"dan": "20"}]})
    assert r.status_code == 200 and "Vali" in r.content.decode()
    errs = json.loads(r["HX-Trigger"])["obv-errors"]["errors"]
    assert {e["loc"] for e in errs} == {"tugSana", "mehnat.0.dan"}


def test_preview_bad_payload(client: Client) -> None:
    assert client.post("/api/preview", data="{oops", content_type="application/json").status_code == 400
    assert client.post("/api/preview", {}).status_code == 400
    assert client.get("/api/preview").status_code == 405


def test_csrf_enforced() -> None:
    c = Client(enforce_csrf_checks=True)
    r = c.post("/api/preview", data="{}", content_type="application/json")
    assert r.status_code == 403
    c.get("/uzb/obyektivka/")
    token = c.cookies["csrftoken"].value
    r = c.post("/api/preview", data="{}", content_type="application/json", HTTP_X_CSRFTOKEN=token)
    assert r.status_code == 200


# ---------------- eksport ----------------
@pytest.mark.parametrize("lang", ["new", "lat", "cyr", "ru"])
def test_export_pdf(client: Client, lang: str) -> None:
    data = get_sample(lang)
    r = _post(client, "/api/export/pdf", {"data": data})
    assert r.status_code == 200 and r["Content-Type"] == "application/pdf"
    assert "attachment;" in r["Content-Disposition"] and "filename*=UTF-8''" in r["Content-Disposition"]
    reader = PdfReader(io.BytesIO(r.content))
    assert len(reader.pages) == 2
    assert data["fish"] in " ".join(reader.pages[0].extract_text().split())


def test_export_docx(client: Client) -> None:
    r = _post(client, "/api/export/docx", {"data": get_sample("lat")})
    assert r.status_code == 200
    doc = Document(io.BytesIO(r.content))
    assert any(
        "Karimov Aziz Rustam o‘g‘li" in p.text
        for t in doc.tables
        for row in t.rows
        for c in row.cells
        for p in c.paragraphs
    )
    assert r["X-Filename"] == "Karimov_Aziz_Rustam_o%E2%80%98g%E2%80%98li_obyektivka.docx"


def test_export_validation_error(client: Client) -> None:
    r = _post(client, "/api/export/pdf", {"data": {"tugSana": "99.99.9999"}})
    assert r.status_code == 422
    assert r.json()["errors"] == [{"loc": "tugSana", "key": "errDate"}]


# ---------------- yozuvni o'girish ----------------
def test_convert_lat_to_cyr(client: Client) -> None:
    data = get_sample("lat")
    r = _post(client, "/api/convert-script", {"data": data, "from": "lat", "to": "cyr"})
    out = r.json()
    assert out["toast"] == "tConv"
    assert out["data"]["fish"] == "Каримов Азиз Рустам ўғли"
    assert out["data"]["tugSana"] == "12.03.2006" and out["data"]["lang"] == "cyr"


def test_convert_to_ru_only_relabels_empty_rows(client: Client) -> None:
    data = {
        "lang": "lat",
        "fish": "Ali",
        "qarindosh": [{"rel": "Otasi", "fish": ""}, {"rel": "Onasi", "fish": "Karimova"}],
    }
    out = _post(client, "/api/convert-script", {"data": data, "from": "lat", "to": "ru"}).json()
    assert out["toast"] == "tLangOnly"
    assert [r["rel"] for r in out["data"]["qarindosh"]] == ["Отец", "Onasi"]
    assert out["data"]["fish"] == "Ali"


def test_convert_empty_no_toast(client: Client) -> None:
    out = _post(client, "/api/convert-script", {"data": {"lang": "lat"}, "from": "lat", "to": "new"}).json()
    assert out["toast"] is None


def test_convert_bad(client: Client) -> None:
    assert _post(client, "/api/convert-script", {"data": {}, "from": "lat", "to": "xx"}).status_code == 400
    assert _post(client, "/api/convert-script", [1]).status_code == 400


# ---------------- rasm ----------------
def _upload(client: Client, img: bytes, name: str = "a.jpg", crop: dict | None = None) -> object:
    data: dict = {"photo": io.BytesIO(img)}
    data["photo"].name = name
    if crop:
        data["crop"] = json.dumps(crop)
    return client.post("/api/photo", data)


def _img_bytes(fmt: str, size: tuple[int, int] = (800, 600), mode: str = "RGB") -> bytes:
    buf = io.BytesIO()
    Image.new(mode, size, (10, 120, 200) if mode == "RGB" else (10, 120, 200, 0)).save(buf, fmt)
    return buf.getvalue()


@pytest.mark.parametrize("fmt", ["JPEG", "PNG", "WEBP"])
def test_photo_ok(client: Client, fmt: str) -> None:
    r = _upload(client, _img_bytes(fmt))
    assert r.status_code == 200
    url = r.json()["photo"]
    assert url.startswith("data:image/jpeg;base64,")
    import base64

    im = Image.open(io.BytesIO(base64.b64decode(url.split(",", 1)[1])))
    assert im.size == (450, 600) and im.format == "JPEG"


def test_photo_crop_and_rotate(client: Client) -> None:
    r = _upload(
        client,
        _img_bytes("JPEG", (1000, 1000)),
        crop={"x": 100, "y": 50, "width": 300, "height": 400, "rotate": 90},
    )
    assert r.status_code == 200


def test_photo_transparent_png_gets_white_bg(client: Client) -> None:
    import base64

    r = _upload(client, _img_bytes("PNG", mode="RGBA"), "a.png")
    im = Image.open(io.BytesIO(base64.b64decode(r.json()["photo"].split(",", 1)[1])))
    assert im.getpixel((10, 10)) >= (250, 250, 250)


@pytest.mark.parametrize(
    ("payload", "name"),
    [
        (b"<svg xmlns='http://www.w3.org/2000/svg'/>", "a.svg"),
        (b"GIF89a....", "a.gif"),
        (b"not an image", "a.jpg"),
    ],
)
def test_photo_rejects_wrong_type(client: Client, payload: bytes, name: str) -> None:
    r = _upload(client, payload, name)
    assert r.status_code == 400 and r.json()["key"] == "tPhotoType"


def test_photo_rejects_gif(client: Client) -> None:
    r = _upload(client, _img_bytes("GIF"), "a.gif")
    assert r.status_code == 400 and r.json()["key"] == "tPhotoType"


def test_photo_missing(client: Client) -> None:
    assert client.post("/api/photo", {}).status_code == 400


def test_request_too_large(client: Client) -> None:
    big = json.dumps({"fish": "x" * (6 * 1024 * 1024)})
    r = client.post("/api/preview", data=big, content_type="application/json")
    assert r.status_code == 413


# ---------------- rate limit ----------------
@pytest.mark.ratelimit
def test_rate_limit(client: Client) -> None:
    # Limit 30/daqiqa. Oyna daqiqa chegarasida yangilanadi: chegara 429 ni faqat kechiktiradi,
    # shuning uchun 62 so'rovda u albatta chiqadi, birinchi 30 tasi esa doim 200.
    codes = [_post(client, "/api/export/docx", {"data": {}}).status_code for _ in range(62)]
    assert all(c == 200 for c in codes[:30])
    assert 429 in codes


# ---------------- maxfiylik ----------------
def test_no_body_in_logs(client: Client, caplog: pytest.LogCaptureFixture) -> None:
    secret = "MAXFIY-Familiya-12345"
    with caplog.at_level(logging.DEBUG):
        _post(client, "/api/preview", {"fish": secret})
        _post(client, "/api/export/pdf", {"data": {"fish": secret, "tugSana": "bad"}})
        _post(client, "/api/convert-script", {"data": {"fish": secret}, "from": "lat", "to": "zz"})
    assert secret not in caplog.text


def test_nothing_written_to_db(client: Client) -> None:
    from django.db import connection

    _post(client, "/api/export/pdf", {"data": get_sample("lat")})
    with connection.cursor() as c:
        c.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {r[0] for r in c.fetchall()}
    assert not any("obyektivka" in t for t in tables)


def test_security_headers(client: Client) -> None:
    r = client.get("/uzb/")
    assert r["X-Frame-Options"] == "DENY" and r["X-Content-Type-Options"] == "nosniff"
    assert "Permissions-Policy" in r


@pytest.mark.parametrize("host", ["127.0.0.1:8000", "172.18.0.1", "evil.example"])
def test_healthz_ignores_allowed_hosts(client: Client, settings, host: str) -> None:  # type: ignore[no-untyped-def]
    settings.ALLOWED_HOSTS = ["obyektivka.example.uz"]
    r = client.get("/healthz", HTTP_HOST=host)
    assert r.status_code == 200 and r.content == b"ok"
    # boshqa sahifalar uchun Host tekshiruvi saqlanadi
    assert client.get("/uzb/", HTTP_HOST="evil.example").status_code == 400


def test_loopback_always_allowed() -> None:
    from django.conf import settings

    assert {"localhost", "127.0.0.1"} <= set(settings.ALLOWED_HOSTS)
