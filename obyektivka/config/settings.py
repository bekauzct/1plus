"""Django sozlamalari. Barcha maxfiy/muhitga bog'liq qiymatlar environment'dan olinadi."""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def env_bool(name: str, default: bool = False) -> bool:
    return os.environ.get(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


def env_list(name: str, default: str = "") -> list[str]:
    return [x.strip() for x in os.environ.get(name, default).split(",") if x.strip()]


DEBUG = env_bool("DJANGO_DEBUG", False)
PRODUCTION = env_bool("DJANGO_PRODUCTION", False)
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "")
if not SECRET_KEY:
    if PRODUCTION:
        raise RuntimeError("DJANGO_SECRET_KEY o'rnatilmagan (DJANGO_PRODUCTION=1)")
    SECRET_KEY = "dev-insecure-key-faqat-lokal-uchun"

ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,[::1],testserver")
CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS")
SITE_URL = os.environ.get("SITE_URL", "http://localhost:8000").rstrip("/")

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.staticfiles",
    "apps.obyektivka",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "apps.obyektivka.middleware.RequestSizeLimitMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.obyektivka.middleware.SecurityHeadersMiddleware",
    # Ratelimited istisnosini RATELIMIT_VIEW (429 JSON) ga aylantiradi
    "django_ratelimit.middleware.RatelimitMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "apps.obyektivka.context_processors.site",
            ],
            "builtins": ["apps.obyektivka.templatetags.obv"],
        },
    }
]

# Baza faqat Django'ning o'zi uchun. Foydalanuvchi ma'lumotlari SAQLANMAYDI.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.environ.get("SQLITE_PATH", str(BASE_DIR / "db.sqlite3")),
    }
}

# Rate limit hisoblagichlari uchun kesh (bir nechta worker bo'lsa — umumiy kesh kerak).
CACHES = {
    "default": {
        "BACKEND": os.environ.get("CACHE_BACKEND", "django.core.cache.backends.locmem.LocMemCache"),
        "LOCATION": os.environ.get("CACHE_LOCATION", "obyektivka"),
    }
}
RATELIMIT_USE_CACHE = "default"
RATELIMIT_VIEW = "apps.obyektivka.views.ratelimited"
# Proksi ortida (nginx/Railway) haqiqiy IP: X-Forwarded-For dan olinadi
RATELIMIT_IP_META_KEY = os.environ.get("RATELIMIT_IP_META_KEY") or None
RATELIMIT_ENABLE = env_bool("RATELIMIT_ENABLE", True)

LANGUAGE_CODE = "uz"
USE_I18N = False
USE_TZ = True
TIME_ZONE = "Asia/Tashkent"

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": (
            "whitenoise.storage.CompressedManifestStaticFilesStorage"
            if PRODUCTION
            else "django.contrib.staticfiles.storage.StaticFilesStorage"
        )
    },
}
WHITENOISE_USE_FINDERS = not PRODUCTION

# So'rov hajmi limiti: rasm bilan 5 MB
MAX_REQUEST_BYTES = 5 * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = MAX_REQUEST_BYTES
FILE_UPLOAD_MAX_MEMORY_SIZE = MAX_REQUEST_BYTES
# Yuklangan rasm faqat xotirada: vaqtinchalik fayl (disk) handler'i ulanmagan
FILE_UPLOAD_HANDLERS = ["django.core.files.uploadhandler.MemoryFileUploadHandler"]

# Xavfsizlik
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
X_FRAME_OPTIONS = "DENY"
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = "Lax"
if PRODUCTION:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SESSION_COOKIE_SECURE = env_bool("DJANGO_SECURE_COOKIES", True)
    CSRF_COOKIE_SECURE = env_bool("DJANGO_SECURE_COOKIES", True)
    SECURE_SSL_REDIRECT = env_bool("DJANGO_SSL_REDIRECT", False)
    SECURE_HSTS_SECONDS = int(os.environ.get("DJANGO_HSTS_SECONDS", "0"))

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Log'larga request body hech qachon yozilmaydi: django.request xatolarida ham
# faqat metod/yo'l/status qoladi (apps.obyektivka.logging.NoBodyFilter).
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {"no_body": {"()": "apps.obyektivka.logging.NoBodyFilter"}},
    "formatters": {"plain": {"format": "%(asctime)s %(levelname)s %(name)s %(message)s"}},
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "plain", "filters": ["no_body"]},
    },
    "root": {"handlers": ["console"], "level": os.environ.get("LOG_LEVEL", "INFO")},
    "loggers": {
        "django.request": {"handlers": ["console"], "level": "WARNING", "propagate": False},
        "django.server": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "weasyprint": {"level": "ERROR"},
        "fontTools": {"level": "ERROR"},
    },
}
