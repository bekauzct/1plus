from django.urls import path, register_converter

from . import views
from .i18n import PREFIX_TO_CODE


class LangPrefixConverter:
    """URL prefiksi (/uz/, /uzb/, /kr/, /ru/) -> ichki til kodi (new, lat, cyr, ru)."""

    regex = "|".join(sorted(PREFIX_TO_CODE, key=len, reverse=True))

    def to_python(self, value: str) -> str:
        return PREFIX_TO_CODE[value]

    def to_url(self, value: str) -> str:
        from .i18n import LANGS

        return LANGS[value].prefix if value in LANGS else value


register_converter(LangPrefixConverter, "lang")

urlpatterns = [
    path("", views.root_redirect, name="root"),
    path("<lang:lang>/", views.landing, name="landing"),
    path("<lang:lang>/obyektivka/", views.editor, name="editor"),
    path("api/preview", views.api_preview, name="api_preview"),
    path("api/export/pdf", views.api_export_pdf, name="api_export_pdf"),
    path("api/export/docx", views.api_export_docx, name="api_export_docx"),
    path("api/convert-script", views.api_convert_script, name="api_convert_script"),
    path("api/photo", views.api_photo, name="api_photo"),
    path("sitemap.xml", views.sitemap, name="sitemap"),
    path("robots.txt", views.robots, name="robots"),
    path("healthz", views.healthz, name="healthz"),
]
