from typing import Any

from django.conf import settings
from django.http import HttpRequest

from .i18n import LANGS


def site(request: HttpRequest) -> dict[str, Any]:
    return {
        "SITE_NAME": "Obyektivka.online",
        "SITE_URL": settings.SITE_URL,
        "LANGS": list(LANGS.values()),
    }
