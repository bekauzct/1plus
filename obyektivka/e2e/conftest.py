"""Playwright e2e: haqiqiy brauzer + pytest-django live_server.

Ishga tushirish:  uv run pytest e2e -m e2e
Brauzer: Playwright'ning o'z chromium'i yoki PLAYWRIGHT_CHROMIUM_EXECUTABLE (yoki /opt/pw-browsers).
"""

import glob
import os
from collections.abc import Iterator

import pytest

os.environ.setdefault("DJANGO_ALLOW_ASYNC_UNSAFE", "true")


def _executable() -> str | None:
    env = os.environ.get("PLAYWRIGHT_CHROMIUM_EXECUTABLE")
    if env:
        return env
    for pattern in ("/opt/pw-browsers/chromium-*/chrome-linux*/chrome",):
        found = sorted(glob.glob(pattern))
        if found:
            return found[-1]
    return None


@pytest.fixture(scope="session")
def browser() -> Iterator[object]:
    sync_api = pytest.importorskip("playwright.sync_api")
    with sync_api.sync_playwright() as p:
        try:
            b = p.chromium.launch()
        except Exception:
            exe = _executable()
            if not exe:
                pytest.skip("Chromium topilmadi (playwright install chromium)")
            b = p.chromium.launch(executable_path=exe)
        yield b
        b.close()


@pytest.fixture
def page(browser, live_server, settings):  # type: ignore[no-untyped-def]
    settings.RATELIMIT_ENABLE = False
    ctx = browser.new_context(viewport={"width": 1366, "height": 900}, accept_downloads=True, locale="uz-UZ")
    pg = ctx.new_page()
    pg.base = live_server.url
    errors: list[str] = []
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.js_errors = errors
    yield pg
    ctx.close()
    assert not errors, errors
