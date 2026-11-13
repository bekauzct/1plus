import base64
import io

import pytest
from PIL import Image


@pytest.fixture
def photo_data_url() -> str:
    buf = io.BytesIO()
    Image.new("RGB", (450, 600), (200, 210, 220)).save(buf, "JPEG", quality=80)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()
