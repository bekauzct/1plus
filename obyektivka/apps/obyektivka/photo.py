"""Rasmni qayta ishlash: tur tekshiruvi, EXIF burilishi, 3×4 kesish va JPEG siqish (Pillow).

Natija prototip bilan bir xil: 450×600 px, oq fon, JPEG sifati 0.88.
Rasm faqat xotirada ishlanadi, diskka yozilmaydi.
"""

from __future__ import annotations

import base64
import io
from dataclasses import dataclass

from PIL import Image, ImageOps, UnidentifiedImageError

OUT_W, OUT_H = 450, 600
JPEG_QUALITY = 88
MAX_INPUT_BYTES = 5 * 1024 * 1024
MAX_PIXELS = 40_000_000  # "decompression bomb" himoyasi
ALLOWED_INPUT = {"JPEG", "PNG", "WEBP"}


class PhotoError(ValueError):
    """``code`` — UI kaliti (tTooBig, tPhotoType, tPhotoErr)."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class Crop:
    x: float
    y: float
    width: float
    height: float
    rotate: float = 0.0


def process_photo(raw: bytes, crop: Crop | None = None) -> bytes:
    if len(raw) > MAX_INPUT_BYTES:
        raise PhotoError("tTooBig")
    try:
        with Image.open(io.BytesIO(raw)) as probe:
            fmt = probe.format
            w, h = probe.size
        if fmt not in ALLOWED_INPUT:
            raise PhotoError("tPhotoType")
        if w * h > MAX_PIXELS:
            raise PhotoError("tTooBig")
        im: Image.Image = Image.open(io.BytesIO(raw))
        im.load()
    except PhotoError:
        raise
    except (UnidentifiedImageError, OSError, SyntaxError, Image.DecompressionBombError) as e:
        raise PhotoError("tPhotoType") from e

    im = ImageOps.exif_transpose(im) or im
    # Shaffof fonni oq qilamiz (prototip: canvas oq bilan to'ldiriladi)
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA")
        bg = Image.new("RGB", im.size, (255, 255, 255))
        bg.paste(im, mask=im.split()[-1])
        im = bg
    else:
        im = im.convert("RGB")

    if crop is not None:
        if crop.rotate:
            # Cropper.js: musbat burchak — soat yo'nalishida; Pillow — teskari
            im = im.rotate(-crop.rotate, expand=True, fillcolor=(255, 255, 255))
        box = _clamp_box(crop, im.size)
        if box:
            im = im.crop(box)

    # "cover": 3×4 ga to'ldirib, markazdan kesish (prototipdagi canvas mantiqi)
    out = ImageOps.fit(im, (OUT_W, OUT_H), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
    buf = io.BytesIO()
    out.save(buf, "JPEG", quality=JPEG_QUALITY, optimize=True)  # EXIF/GPS saqlanmaydi
    return buf.getvalue()


def _clamp_box(c: Crop, size: tuple[int, int]) -> tuple[int, int, int, int] | None:
    w, h = size
    x0 = max(0, min(w, round(c.x)))
    y0 = max(0, min(h, round(c.y)))
    x1 = max(0, min(w, round(c.x + c.width)))
    y1 = max(0, min(h, round(c.y + c.height)))
    if x1 - x0 < 10 or y1 - y0 < 10:
        return None
    return (x0, y0, x1, y1)


def to_data_url(jpeg: bytes) -> str:
    return "data:image/jpeg;base64," + base64.b64encode(jpeg).decode("ascii")
