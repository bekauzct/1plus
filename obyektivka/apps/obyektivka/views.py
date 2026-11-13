"""Sahifalar va HTMX/API endpointlar.

Foydalanuvchi ma'lumoti faqat so'rov davomida xotirada ishlatiladi: diskka, bazaga
yoki log'ga yozilmaydi. API javoblari ``Cache-Control: no-store`` (middleware).
"""

from __future__ import annotations

import json
from typing import Any
from urllib.parse import quote

from django.conf import settings
from django.http import (
    HttpRequest,
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseRedirect,
    JsonResponse,
)
from django.shortcuts import render
from django.urls import reverse
from django.utils.cache import patch_vary_headers
from django.views.decorators.cache import cache_control
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST
from django_ratelimit.decorators import ratelimit
from pydantic import ValidationError

from . import render as renderer
from .editor_spec import resolve as resolve_sections
from .i18n import DEFAULT_LANG, LANGS, NOCONV, get_lang, get_sample, get_site, get_tl, get_ui, is_uzbek
from .photo import Crop, PhotoError, process_photo, to_data_url
from .ratelimit import client_ip
from .schemas import Obyektivka, errors_for_client, has, lenient
from .translit import deep_convert

DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


# ---------------------------------------------------------------------------
# Yordamchilar
# ---------------------------------------------------------------------------
class BadPayload(Exception):
    pass


def _payload(request: HttpRequest) -> Any:
    """JSON body yoki form maydoni ``payload`` (HTMX) dan ma'lumotni o'qiydi."""
    ctype = request.META.get("CONTENT_TYPE", "")
    try:
        if ctype.startswith("application/json"):
            return json.loads(request.body or b"{}")
        raw = request.POST.get("payload")
        if raw is None:
            raise BadPayload
        return json.loads(raw)
    except (ValueError, UnicodeDecodeError) as e:
        raise BadPayload from e


def _data_of(payload: Any) -> Any:
    return payload.get("data", payload) if isinstance(payload, dict) else payload


def _lang_urls(view: str) -> dict[str, str]:
    return {code: reverse(view, kwargs={"lang": code}) for code in LANGS}


def _page_context(request: HttpRequest, lang: str, view: str) -> dict[str, Any]:
    urls = _lang_urls(view)
    return {
        "lang": lang,
        "L": get_lang(lang),
        "U": get_ui(lang),
        "T": get_tl(lang),
        "site": get_site(lang),
        "lang_urls": [(LANGS[c], u) for c, u in urls.items()],
        "canonical": settings.SITE_URL + urls[lang],
        "alternates": [(LANGS[c].hreflang, settings.SITE_URL + u) for c, u in urls.items()],
        "x_default": settings.SITE_URL + "/",
        "home_url": reverse("landing", kwargs={"lang": lang}),
        "editor_url": reverse("editor", kwargs={"lang": lang}),
    }


def ratelimited(request: HttpRequest, exception: Exception | None = None) -> HttpResponse:
    return JsonResponse({"error": "rate_limited", "key": "tRate"}, status=429)


def _invalid(exc: ValidationError) -> JsonResponse:
    return JsonResponse({"error": "invalid", "key": "tInvalid", "errors": errors_for_client(exc)}, status=422)


def _attachment(content: bytes, filename: str, mime: str) -> HttpResponse:
    resp = HttpResponse(content, content_type=mime)
    ascii_name = filename.encode("ascii", "ignore").decode() or "obyektivka" + filename[filename.rfind(".") :]
    resp["Content-Disposition"] = f"attachment; filename=\"{ascii_name}\"; filename*=UTF-8''{quote(filename)}"
    resp["X-Filename"] = quote(filename)
    return resp


# ---------------------------------------------------------------------------
# Sahifalar
# ---------------------------------------------------------------------------
@require_GET
def root_redirect(request: HttpRequest) -> HttpResponse:
    """/ -> brauzer tiliga mos prefiks (rus bo'lsa /ru/, aks holda /uzb/)."""
    accept = request.META.get("HTTP_ACCEPT_LANGUAGE", "").lower()
    first = accept.split(",")[0].strip()[:2] if accept else ""
    lang = "ru" if first == "ru" else DEFAULT_LANG
    resp = HttpResponseRedirect(reverse("landing", kwargs={"lang": lang}))
    patch_vary_headers(resp, ["Accept-Language"])
    return resp


@require_GET
@ensure_csrf_cookie
def landing(request: HttpRequest, lang: str) -> HttpResponse:
    ctx = _page_context(request, lang, "landing")
    sample = Obyektivka.model_validate(get_sample(lang))
    ctx["sample_html"] = renderer.render_preview_html(sample, page_labels=False)
    ctx["sample_full_html"] = renderer.render_preview_html(sample, page_labels=True)
    site = ctx["site"]
    ctx["ld_json"] = [
        {
            "@context": "https://schema.org",
            "@type": "WebApplication",
            "name": "Obyektivka.online",
            "url": ctx["canonical"],
            "inLanguage": get_lang(lang).html_lang,
            "applicationCategory": "BusinessApplication",
            "operatingSystem": "Any",
            "description": site["metaDesc"],
            "offers": {"@type": "Offer", "price": "0", "priceCurrency": "UZS"},
        },
        {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": [
                {"@type": "Question", "name": q["q"], "acceptedAnswer": {"@type": "Answer", "text": q["a"]}}
                for q in site["faq"]
            ],
        },
    ]
    return render(request, "obyektivka/landing.html", ctx)


@require_GET
@ensure_csrf_cookie
def editor(request: HttpRequest, lang: str) -> HttpResponse:
    ctx = _page_context(request, lang, "editor")
    ui = get_ui(lang)
    ctx["boot"] = {
        "lang": lang,
        "ui": ui,
        "sample": get_sample(lang),
        "urls": {
            "preview": reverse("api_preview"),
            "pdf": reverse("api_export_pdf"),
            "docx": reverse("api_export_docx"),
            "convert": reverse("api_convert_script"),
            "photo": reverse("api_photo"),
            "langs": {c: u for c, u in _lang_urls("editor").items()},
        },
    }
    ctx["sections"] = resolve_sections(ui)
    ctx["initial_html"] = renderer.render_preview_html(Obyektivka.model_validate({"lang": lang}))
    return render(request, "obyektivka/editor.html", ctx)


def not_found(request: HttpRequest, exception: Exception | None = None) -> HttpResponse:
    lang = DEFAULT_LANG
    parts = request.path.strip("/").split("/")
    for code, lg in LANGS.items():
        if parts and parts[0] == lg.prefix:
            lang = code
    ctx = _page_context(request, lang, "landing")
    ctx["noindex"] = True
    return render(request, "obyektivka/404.html", ctx, status=404)


@require_GET
@cache_control(max_age=3600, public=True)
def sitemap(request: HttpRequest) -> HttpResponse:
    entries = []
    for view, prio in (("landing", "1.0"), ("editor", "0.9")):
        urls = _lang_urls(view)
        for code in LANGS:
            entries.append(
                {
                    "loc": settings.SITE_URL + urls[code],
                    "priority": prio,
                    "alternates": [(LANGS[c].hreflang, settings.SITE_URL + u) for c, u in urls.items()],
                }
            )
    return render(request, "sitemap.xml", {"entries": entries}, content_type="application/xml")


@require_GET
@cache_control(max_age=3600, public=True)
def robots(request: HttpRequest) -> HttpResponse:
    lines = ["User-agent: *", "Disallow: /api/", "Allow: /", f"Sitemap: {settings.SITE_URL}/sitemap.xml", ""]
    return HttpResponse("\n".join(lines), content_type="text/plain; charset=utf-8")


@require_GET
def healthz(request: HttpRequest) -> HttpResponse:
    return HttpResponse("ok", content_type="text/plain")


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------
@require_POST
@ratelimit(key=client_ip, rate="240/m", block=True)
def api_preview(request: HttpRequest) -> HttpResponse:
    """Jonli preview: HTML fragment. Noto'g'ri maydonlar bo'lsa ham varaq chiziladi,
    xatolar ``HX-Trigger: {"obv-errors": {"errors": [...]}}`` sarlavhasida qaytadi."""
    try:
        data = _data_of(_payload(request))
    except BadPayload:
        return HttpResponseBadRequest("bad payload")
    errors: list[dict[str, str]] = []
    try:
        model = Obyektivka.model_validate(data)
    except ValidationError as exc:
        errors = errors_for_client(exc)
        model = lenient(data)
    resp = HttpResponse(renderer.render_preview_html(model))
    resp["HX-Trigger"] = json.dumps({"obv-errors": {"errors": errors}})
    return resp


def _export(request: HttpRequest, kind: str) -> HttpResponse:
    try:
        data = _data_of(_payload(request))
    except BadPayload:
        return HttpResponseBadRequest("bad payload")
    try:
        model = Obyektivka.model_validate(data)
    except ValidationError as exc:
        return _invalid(exc)
    if kind == "pdf":
        return _attachment(
            renderer.render_pdf(model), renderer.export_filename(model, "pdf"), "application/pdf"
        )
    return _attachment(renderer.render_docx(model), renderer.export_filename(model, "docx"), DOCX_MIME)


@require_POST
@ratelimit(key=client_ip, rate="30/m", block=True)
def api_export_pdf(request: HttpRequest) -> HttpResponse:
    return _export(request, "pdf")


@require_POST
@ratelimit(key=client_ip, rate="30/m", block=True)
def api_export_docx(request: HttpRequest) -> HttpResponse:
    return _export(request, "docx")


def convert_data(data: dict[str, Any], src: str, dst: str) -> tuple[dict[str, Any], str | None]:
    """Prototipdagi switchLang mantiqi.

    O'zbek yozuvlari orasida — barcha matn o'giriladi (photo/tugSana/lang dan tashqari).
    Rus tiliga yoki undan — faqat F.I.Sh. kiritilmagan qatorlardagi standart qarindoshlik nomlari
    tarjima qilinadi, foydalanuvchi matni o'zgarmaydi.
    Qaytaradi: (yangi ma'lumot, toast kaliti yoki None).
    """
    keys = ("fish", "lavozim", "tugSana", "tugJoy", "millati", "partiya", "malumoti", "tamomlagan",
            "mutaxassislik", "ilmiyDaraja", "ilmiyUnvon", "tillar", "mukofot", "deputat")  # fmt: skip
    mehnat = data.get("mehnat") or []
    qarindosh = data.get("qarindosh") or []
    any_data = (
        any(has(data.get(k)) for k in keys)
        or any(isinstance(m, dict) and has(m.get("matn")) for m in mehnat)
        or any(isinstance(r, dict) and has(r.get("fish")) for r in qarindosh)
    )
    if is_uzbek(src) and is_uzbek(dst):
        out: dict[str, Any] = deep_convert(data, src, dst, NOCONV)
        toast = "tConv"
    else:
        out = json.loads(json.dumps(data))
        fu, tu = get_ui(src)["rels"], get_ui(dst)["rels"]
        for r in out.get("qarindosh") or []:
            if not isinstance(r, dict):
                continue
            rel = r.get("rel")
            if rel in fu and not has(r.get("fish")):
                i = min(fu.index(rel), len(tu) - 1)
                if tu[i]:
                    r["rel"] = tu[i]
        toast = "tLangOnly"
    out["lang"] = dst
    return out, (toast if any_data else None)


@require_POST
@ratelimit(key=client_ip, rate="60/m", block=True)
def api_convert_script(request: HttpRequest) -> HttpResponse:
    """{"data": {...}, "from": "lat", "to": "cyr"} -> {"data": {...}, "toast": "tConv" | "tLangOnly" | null}"""
    try:
        payload = _payload(request)
    except BadPayload:
        return HttpResponseBadRequest("bad payload")
    if not isinstance(payload, dict) or not isinstance(payload.get("data"), dict):
        return HttpResponseBadRequest("bad payload")
    src = payload.get("from") or payload["data"].get("lang") or DEFAULT_LANG
    dst = payload.get("to")
    if src not in LANGS or dst not in LANGS:
        return HttpResponseBadRequest("bad lang")
    data, toast = convert_data(payload["data"], src, dst)
    return JsonResponse({"data": data, "toast": toast})


@require_POST
@ratelimit(key=client_ip, rate="30/m", block=True)
def api_photo(request: HttpRequest) -> HttpResponse:
    """multipart: photo=<fayl>, crop={"x","y","width","height","rotate"} (Cropper.js getData) -> {"photo": dataURL}"""
    f = request.FILES.get("photo")
    if f is None:
        return JsonResponse({"error": "no_file", "key": "tPhotoErr"}, status=400)
    crop = None
    raw_crop = request.POST.get("crop")
    if raw_crop:
        try:
            c = json.loads(raw_crop)
            crop = Crop(
                x=float(c["x"]),
                y=float(c["y"]),
                width=float(c["width"]),
                height=float(c["height"]),
                rotate=float(c.get("rotate") or 0),
            )
        except (ValueError, KeyError, TypeError):
            crop = None
    try:
        jpeg = process_photo(f.read(), crop)
    except PhotoError as e:
        return JsonResponse({"error": "photo", "key": e.code}, status=400)
    finally:
        f.close()
    return JsonResponse({"photo": to_data_url(jpeg)})
