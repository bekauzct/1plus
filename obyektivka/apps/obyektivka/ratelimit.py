"""Rate limit kaliti: mijoz IP manzili.

Proksi (nginx, Railway) ortida REMOTE_ADDR — proksi manzili bo'ladi. ``TRUST_PROXY_HEADERS=1``
bo'lsa, X-Real-IP yoki X-Forwarded-For'ning birinchi qiymati olinadi. Ishonchsiz muhitda
yoqmang: mijoz sarlavhani soxtalashtirib limitdan qochishi mumkin.
"""

from __future__ import annotations

import os

from django.http import HttpRequest


def client_ip(group: str, request: HttpRequest) -> str:
    meta = request.META
    if os.environ.get("TRUST_PROXY_HEADERS", "").lower() in {"1", "true", "yes"}:
        real = meta.get("HTTP_X_REAL_IP", "").strip()
        if real:
            return real
        xff = meta.get("HTTP_X_FORWARDED_FOR", "")
        if xff:
            return xff.split(",")[0].strip()
    return str(meta.get("REMOTE_ADDR", ""))
