# syntax=docker/dockerfile:1.7
# Obyektivka — production image: Ubuntu 24.04 (tizim Python 3.12) + gunicorn + WeasyPrint

FROM ubuntu:24.04 AS base
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    LANG=C.UTF-8
# python3.12 — Ubuntu 24.04 ning standart Python'i.
# WeasyPrint uchun: Pango (matn joylash), HarfBuzz (+subset — PDF'ga shriftning faqat kerakli
# qismini qo'shish), fontconfig, shared-mime-info. Pillow wheel'i o'z kutubxonalari bilan keladi.
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      python3.12 python3.12-venv \
      libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz0b libharfbuzz-subset0 \
      libfontconfig1 shared-mime-info ca-certificates curl \
 && rm -rf /var/lib/apt/lists/*

# ---------- Python bog'liqliklari (uv.lock bo'yicha aniq versiyalar) ----------
FROM base AS deps
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PROJECT_ENVIRONMENT=/opt/venv UV_PYTHON_DOWNLOADS=never
RUN python3.12 -m venv /opt/uv && /opt/uv/bin/pip install --no-cache-dir "uv>=0.8,<0.9"
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    /opt/uv/bin/uv sync --frozen --no-dev --no-install-project --python /usr/bin/python3.12

# ---------- ilova ----------
FROM base AS runtime
RUN useradd --create-home --uid 10001 app
COPY --from=deps /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH" \
    DJANGO_SETTINGS_MODULE=config.settings \
    DJANGO_PRODUCTION=1 \
    SQLITE_PATH=/app/data/db.sqlite3 \
    PORT=8000
WORKDIR /app
COPY --chown=app:app . .
# Statik fayllar (hash'li nomlar + gzip/brotli) — build vaqtida
RUN DJANGO_SECRET_KEY=build-only python manage.py collectstatic --noinput -v0 \
 && mkdir -p /app/data && chown app:app /app/data
USER app
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD curl -fsS "http://127.0.0.1:${PORT}/healthz" || exit 1
CMD ["sh", "-c", "python manage.py migrate --noinput -v0 && exec gunicorn config.wsgi:application -c deploy/gunicorn.conf.py"]
