# Obyektivka.online

Obyektivka (ma'lumotnoma) ni online to'ldirish: chapda forma, o'ngda A4 varaqning jonli ko'rinishi,
PDF va Word (.docx) yuklab olish. To'rt yozuv/til: **UZ** (yangi lotin: ç ş ğ ö), **UZB** (lotin),
**Кирилл**, **Рус**.

Bu loyiha `../reference/obyektivka.html` dagi bitta faylli JS prototipning Python/Django'dagi
production versiyasi. Prototipdagi barcha funksiyalar saqlangan; transliteratsiya va lug'atlar
prototip JS kodi bilan avtomatik solishtiriladi (1475 ta golden holat).

**Maxfiylik:** foydalanuvchi ma'lumotlari serverda saqlanmaydi. Holat brauzerdagi `localStorage`'da
turadi; server uni faqat so'rov davomida xotirada ishlatadi (preview/PDF/DOCX), diskka, bazaga
yoki log'ga yozmaydi.

---

## Tezkor ishga tushirish

Talablar: [uv](https://docs.astral.sh/uv/), Python 3.12 (uv o'zi o'rnatadi), WeasyPrint uchun Pango
(Ubuntu/Debian: `apt install libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz-subset0`,
macOS: `brew install pango`).

```bash
cd obyektivka
uv sync                                   # bog'liqliklar (.venv)
DJANGO_DEBUG=1 uv run python manage.py migrate
DJANGO_DEBUG=1 uv run python manage.py runserver
# -> http://127.0.0.1:8000/  (/uzb/ ga yo'naltiradi)
```

Docker bilan:

```bash
cd obyektivka
docker compose up --build                  # http://localhost:8000
docker compose --profile proxy up --build  # nginx orqali: http://localhost:8080
```

### Testlar va sifat

```bash
uv run pytest                 # unit/integratsiya: translit, i18n, schemas, render (PDF/DOCX), API
uv run pytest e2e             # Playwright e2e (brauzer kerak: uv run playwright install chromium)
uv run ruff check . && uv run ruff format --check .
uv run mypy apps config
uv run pre-commit install     # commit oldidan ruff + mypy (repo ildizidagi .pre-commit-config.yaml)
```

`tests/test_golden_js.py` Python portini prototipdagi JS bilan solishtiradi. Kutilgan natijalar
`tests/fixtures/js_golden.json` da; `node` o'rnatilgan bo'lsa, test fixture'ni prototipning o'zida
qayta ishga tushirib ham tekshiradi. Holatlar ro'yxatini o'zgartirsangiz:
`uv run python scripts/gen_golden.py`.

### CSS (Tailwind)

Tayyor `static/css/app.css` repoda bor. Shablonlarda yangi Tailwind klass ishlatsangiz:

```bash
./scripts/build_css.sh          # standalone CLI'ni yuklab, minify bilan yig'adi (Node shart emas)
./scripts/build_css.sh --watch  # ishlab chiqishda
```

---

## Tuzilma

```
obyektivka/
├── config/                    Django sozlamalari (env orqali), urls, wsgi
├── apps/obyektivka/
│   ├── translit.py            lat↔cyr↔new transliteratsiya — JS'ning aniq porti
│   ├── i18n/                  lug'atlar: uz_lat (manba), ru (manba), uz_cyr/uz_new (avtomatik)
│   ├── schemas.py             pydantic: Obyektivka, MehnatDavr, Qarindosh (+ validatsiya)
│   ├── render.py              HTML preview, PDF (WeasyPrint), DOCX (python-docx) — HTTP'dan mustaqil
│   ├── photo.py               Pillow: tur tekshiruvi, EXIF, 3×4 kesish, JPEG
│   ├── views.py               sahifalar + API (HTMX)
│   ├── editor_spec.py         formadagi bo'limlar/maydonlar ro'yxati
│   ├── middleware.py          5 MB limit, xavfsizlik sarlavhalari, API uchun no-store
│   ├── logging.py             log'dan request body'ni olib tashlovchi filtr
│   └── templates/obyektivka/
│       ├── document.html      VARAQ: preview va PDF uchun YAGONA shablon
│       ├── editor.html        muharrir (Alpine.js + HTMX)
│       └── landing.html       bosh sahifa
├── static/
│   ├── css/document.css       varaq stili (preview + PDF, @page A4)
│   ├── css/src/app.css        Tailwind manbasi -> css/app.css
│   ├── js/editor.js           Alpine komponenti (holat, localStorage, ro'yxatlar, rasm, eksport)
│   ├── fonts/                 Tinos (Times New Roman o'rnini bosuvchi, OFL)
│   └── vendor/                htmx, alpine, sortable, cropper (versiyalar: VERSIONS.txt)
├── tests/                     pytest
├── e2e/                       Playwright
├── scripts/                   gen_golden.py, js_reference.mjs, build_css.sh
├── deploy/                    gunicorn.conf.py, nginx.conf
├── Dockerfile, docker-compose.yml
```

### Ma'lumot oqimi

1. Forma holati (`S`) Alpine.js'da, har o'zgarishda `localStorage`'ga yoziladi.
2. Body'da `obv-changed` hodisasi chiqadi → HTMX (`hx-trigger="obv-changed from:body delay:300ms"`)
   holatni JSON qilib `POST /api/preview` ga yuboradi → server `document.html` dan HTML fragment
   qaytaradi → o'ng panel almashadi. Yozilgan maydon varaqda sariq bilan belgilanadi va
   ko'rinadigan joyga suriladi.
3. PDF/Word tugmasi `POST /api/export/pdf|docx` ga to'liq validatsiyadan o'tgan ma'lumotni yuboradi.
   Xato bo'lsa — 422 va maydonlar ro'yxati (forma o'sha maydonni ochib, fokus qiladi).

### API

| Endpoint | Kirish | Chiqish |
|---|---|---|
| `POST /api/preview` | JSON yoki form `payload=<json>` | HTML fragment; xatolar `HX-Trigger: {"obv-errors": {"errors": [...]}}` |
| `POST /api/export/pdf` | `{"data": {...}}` | `application/pdf` (422 — validatsiya xatolari) |
| `POST /api/export/docx` | `{"data": {...}}` | `.docx` |
| `POST /api/convert-script` | `{"data": {...}, "from": "lat", "to": "cyr"}` | `{"data": {...}, "toast": "tConv" \| "tLangOnly" \| null}` |
| `POST /api/photo` | multipart `photo`, ixtiyoriy `crop` (Cropper.js `getData`) | `{"photo": "data:image/jpeg;base64,..."}` |

Barcha POST'lar CSRF bilan himoyalangan (`X-CSRFToken`), rate limit bor (429).

### Sahifalar

`/` → brauzer tiliga qarab `/uzb/` yoki `/ru/`. `/<til>/` — landing, `/<til>/obyektivka/` — muharrir.
Prefikslar: `/uz/` (yangi lotin), `/uzb/` (lotin), `/kr/` (kirill), `/ru/`. Til almashtirilganda
saqlangan ma'lumot o'sha yozuvga o'giriladi va "Qaytarish" taklif qilinadi (prototipdagidek).

---

## Yangi til qo'shish

**A. O'zbek tilining yana bir yozuvi** (lotindan avtomatik hosil bo'ladigan):

1. `apps/obyektivka/translit.py` ga `lat2xxx` / `xxx2lat` funksiyalarini qo'shing va `to_lat` /
   `from_lat` ga ulang.
2. `apps/obyektivka/i18n/uz_xxx.py` yarating — `uz_new.py` dan nusxa ko'chirib, `"new"` o'rniga
   `"xxx"` yozing. Avtomatik o'girish xato chiqaradigan so'zlar uchun `uz_cyr.FIXUPS` kabi ro'yxat qo'shing.
3. `i18n/__init__.py` dagi `LANGS` ga yozuv qo'shing: kod, URL prefiksi, tugma nomi, `html_lang`,
   `hreflang`, `og_locale`, Word uchun `docx_lang`.
4. `schemas.LangCode` va `Obyektivka._lang` dagi ruxsat etilgan kodlar ro'yxatini, `static/js/editor.js`
   dagi `LANGS` ni yangilang.

**B. Butunlay boshqa til** (masalan, ingliz yoki qoraqalpoq):

1. `i18n/ru.py` dan nusxa olib `i18n/en.py` yarating va `TL`, `UI`, `SAMPLE`, `SITE` lug'atlarini
   tarjima qiling (kalitlar to'plami bir xil bo'lishi `tests/test_i18n.py` da tekshiriladi).
   2-sahifa sarlavhasi tartibi `Labels.rel_lines` da (rus tilida ism oxirida) — kerak bo'lsa moslang.
2. `LANGS` ga qo'shing. `is_uzbek()` — qaysi tillar orasida matn transliteratsiya qilinishini belgilaydi.
3. `uv run pytest` — kalitlar, sahifalar, sitemap va hreflang avtomatik tekshiriladi.

---

## Deploy

### Muhit o'zgaruvchilari

| O'zgaruvchi | Tavsif |
|---|---|
| `DJANGO_PRODUCTION=1` | production rejim (Dockerfile'da yoqilgan); `DJANGO_SECRET_KEY` majburiy bo'ladi |
| `DJANGO_SECRET_KEY` | uzun tasodifiy kalit: `python -c "import secrets;print(secrets.token_urlsafe(50))"` |
| `DJANGO_ALLOWED_HOSTS` | vergul bilan: `obyektivka.uz,www.obyektivka.uz` |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | `https://obyektivka.uz` |
| `SITE_URL` | canonical/hreflang/sitemap uchun to'liq manzil, `https://obyektivka.uz` |
| `REDIS_URL` | bir nechta worker uchun umumiy rate-limit hisoblagichi (ixtiyoriy) |
| `TRUST_PROXY_HEADERS=1` | proksi ortida mijoz IP'sini `X-Real-IP`/`X-Forwarded-For` dan olish |
| `DJANGO_SSL_REDIRECT`, `DJANGO_HSTS_SECONDS`, `DJANGO_SECURE_COOKIES` | HTTPS sozlamalari |
| `WEB_CONCURRENCY` | gunicorn worker'lar soni (standart: CPU×2+1, ko'pi bilan 4) |

### Railway

1. Railway'da yangi loyiha → **Deploy from GitHub repo** → shu repo.
2. Service → **Settings → Root Directory**: `obyektivka` (Dockerfile shu yerda, avtomatik topiladi).
3. **Variables**: `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS=<servis>.up.railway.app,obyektivka.uz`,
   `DJANGO_CSRF_TRUSTED_ORIGINS=https://<servis>.up.railway.app,https://obyektivka.uz`,
   `SITE_URL=https://obyektivka.uz`, `TRUST_PROXY_HEADERS=1`, `DJANGO_HSTS_SECONDS=31536000`.
   Railway `PORT` ni o'zi beradi — gunicorn uni o'qiydi.
4. (Ixtiyoriy) **+ New → Database → Redis** qo'shing va `REDIS_URL=${{Redis.REDIS_URL}}` deb bog'lang.
5. **Settings → Networking → Custom Domain** — domenni ulang, DNS'da CNAME yozing.
6. **Healthcheck Path**: `/healthz`.

SQLite faqat Django'ning ichki jadvallari uchun; volume shart emas (foydalanuvchi ma'lumoti yo'q).

### VPS (Ubuntu 24.04: Docker + gunicorn + nginx)

```bash
# 1. Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER && newgrp docker

# 2. Kod va sozlamalar
git clone <repo-url> && cd <repo>/obyektivka
cp .env.example .env && nano .env      # kalit, domen, SITE_URL

# 3. Ishga tushirish (web + redis + nginx)
docker compose --profile proxy up -d --build
docker compose ps && curl -fsS http://localhost:8080/healthz
```

`deploy/nginx.conf` 80-portda ishlaydi va so'rovlarni `web:8000` (gunicorn) ga uzatadi: body limiti
6 MB, `/api/` uchun qo'shimcha `limit_req`, log'da faqat metod/yo'l/status (query string va body yo'q).
`docker-compose.yml` dagi `8080:80` ni `80:80` ga o'zgartiring.

**HTTPS** (certbot, host'da):

```bash
sudo apt install -y nginx certbot python3-certbot-nginx
# host nginx -> 127.0.0.1:8080 (konteyner nginx) yoki to'g'ridan-to'g'ri 127.0.0.1:8000 (gunicorn)
sudo tee /etc/nginx/sites-available/obyektivka >/dev/null <<'NGINX'
server {
    server_name obyektivka.uz www.obyektivka.uz;
    client_max_body_size 6m;
    client_body_buffer_size 6m;
    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
NGINX
sudo ln -s /etc/nginx/sites-available/obyektivka /etc/nginx/sites-enabled/
sudo certbot --nginx -d obyektivka.uz -d www.obyektivka.uz
```

So'ng `.env` da `DJANGO_SECURE_COOKIES=1`, `DJANGO_HSTS_SECONDS=31536000` va
`docker compose --profile proxy up -d`. Konteyner nginx'i host nginx ortida bo'lsa, ikkala
qatlam ham `X-Real-IP` ni uzatadi; `TRUST_PROXY_HEADERS=1` faqat proksi ortida yoqilsin.

**Yangilash:** `git pull && docker compose --profile proxy up -d --build`.
**Loglar:** `docker compose logs -f web` (request body yozilmaydi).

---

## Keyingi bosqichlar uchun joy

Hozircha qurilmagan, lekin arxitektura ularni ko'zda tutadi:

- **Bitta render qatlami.** `render.py` HTTP'ga bog'liq emas: `render_pdf(Obyektivka)`,
  `render_docx(...)`, `render_preview_html(...)`. Telegram bot (aiogram), rezyume generatori va
  vakansiyaga ariza berish ham shu funksiyalarni chaqiradi (bot: `Obyektivka.model_validate(state)`
  → `render_pdf` → `send_document`).
- **Ma'lumot shartnomasi — `schemas.Obyektivka`.** Profillarni bazada saqlash uchun alohida
  `apps/profiles` ilovasi `JSONField`'da shu modelning `model_dump()` ini saqlaydi; muharrirdagi
  JSON eksport/import formati aynan shu.
- **Telegram orqali kirish** — `apps/accounts` (Telegram Login Widget imzosini tekshirish), hozirgi
  sahifalar anonim rejimda ishlashda davom etadi.
- **Click/Payme** — `apps/payments`; eksport endpointlari oldiga "to'langanmi" tekshiruvini qo'yish
  uchun `_export()` yagona nuqta.
- **Yangi hujjat turlari** (rezyume) — `templates/<tur>/document.html` + `static/css/<tur>.css`
  va `schemas` da yangi model; `render.py` dagi WeasyPrint/DOCX yordamchilari umumiy.
- Kesh: `REDIS_URL` allaqachon ulangan (rate limit), bot va navbatlar uchun ham ishlatiladi.
