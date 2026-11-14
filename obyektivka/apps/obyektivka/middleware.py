from collections.abc import Callable

from django.conf import settings
from django.http import HttpRequest, HttpResponse, JsonResponse


class HealthCheckMiddleware:
    """``/healthz`` ga ALLOWED_HOSTS tekshiruvisiz ``ok`` qaytaradi.

    Docker HEALTHCHECK, Railway yoki yuklama balanslovchi so'rovni IP manzil (masalan,
    ``127.0.0.1:8000`` yoki ``172.18.0.1``) bilan yuboradi; u ALLOWED_HOSTS'da bo'lmasa,
    CommonMiddleware 400 qaytarib, konteyner "unhealthy" bo'lib qolardi.
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        if request.path == "/healthz" and request.method in ("GET", "HEAD"):
            return HttpResponse("ok", content_type="text/plain")
        return self.get_response(request)


class SecurityHeadersMiddleware:
    """Qo'shimcha xavfsizlik sarlavhalari va API javoblari uchun no-store."""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        response = self.get_response(request)
        response.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        response.setdefault("Cross-Origin-Opener-Policy", "same-origin")
        if request.path.startswith("/api/"):
            # Shaxsiy ma'lumot: hech qanday kesh (brauzer/proksi) saqlamasin
            response["Cache-Control"] = "no-store"
        return response


class RequestSizeLimitMiddleware:
    """So'rov hajmi limiti (rasm bilan 5 MB). Body o'qilmasdan Content-Length bo'yicha rad etiladi."""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        try:
            length = int(request.META.get("CONTENT_LENGTH") or 0)
        except ValueError:
            length = 0
        if length > settings.MAX_REQUEST_BYTES:
            return JsonResponse({"error": "too_large", "key": "tTooBig"}, status=413)
        return self.get_response(request)
