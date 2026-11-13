from collections.abc import Callable

from django.http import HttpRequest, HttpResponse


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
