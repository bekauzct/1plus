from collections.abc import Callable

from django.conf import settings
from django.http import HttpRequest, HttpResponse, JsonResponse


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
