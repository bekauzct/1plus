import base64
import io

import pytest
from PIL import Image


@pytest.fixture
def photo_data_url() -> str:
    buf = io.BytesIO()
    Image.new("RGB", (450, 600), (200, 210, 220)).save(buf, "JPEG", quality=80)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


@pytest.fixture(autouse=True)
def _no_ratelimit(settings, request):  # type: ignore[no-untyped-def]
    """Rate limit faqat o'ziga atalgan testda yoqiladi."""
    if "ratelimit" not in request.keywords:
        settings.RATELIMIT_ENABLE = False
    from django.core.cache import cache

    cache.clear()
