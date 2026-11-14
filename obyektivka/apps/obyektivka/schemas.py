"""Obyektivka ma'lumotlari modeli (pydantic).

Bu — butun loyihaning "shartnomasi": brauzer (localStorage/JSON eksport), render.py
(preview/PDF/DOCX) va kelajakdagi iste'molchilar (Telegram bot, profillarni bazada saqlash,
rezyume generatori) shu modeldan foydalanadi. Maydon nomlari prototip bilan bir xil.
"""

from __future__ import annotations

import base64
import binascii
import io
import re
from datetime import date
from typing import Any, Literal, cast

from PIL import Image, UnidentifiedImageError
from pydantic import BaseModel, ConfigDict, Field, ValidationError, ValidationInfo, field_validator
from pydantic_core import PydanticCustomError

LangCode = Literal["new", "lat", "cyr", "ru"]

TEXT_FIELDS: tuple[str, ...] = (
    "fish", "lavozim", "tugSana", "tugJoy", "millati", "partiya", "malumoti", "tamomlagan",
    "mutaxassislik", "ilmiyDaraja", "ilmiyUnvon", "tillar", "mukofot", "deputat",
)  # fmt: skip

MAX_PHOTO_BYTES = 4 * 1024 * 1024  # dekodlangan rasm; base64 bilan so'rov 5 MB dan oshmaydi
ALLOWED_PHOTO_FORMATS = {"JPEG": "image/jpeg", "PNG": "image/png"}

_DATE_RE = re.compile(r"^(\d{2})\.(\d{2})\.(\d{4})$")
_YEAR_RE = re.compile(r"^\d{4}$")
_DATA_URL_RE = re.compile(r"^data:(image/(?:jpeg|png));base64,([A-Za-z0-9+/=\s]+)$")

SHORT, LONG = 300, 2000


def has(value: object) -> bool:
    """Prototipdagi ``has``: bo'sh bo'lmagan (bo'shliqlardan tashqari) satr."""
    return bool(value) and bool(str(value).strip())


def _check_year(v: str) -> str:
    s = v.strip()
    if s and (not _YEAR_RE.match(s) or not 1900 <= int(s) <= 2100):
        raise PydanticCustomError("year", "Yil 4 xonali bo'lishi kerak")
    return v


def parse_birth_date(v: str) -> date | None:
    """DD.MM.YYYY -> date. Bo'sh satr -> None. Noto'g'ri bo'lsa ValueError."""
    s = v.strip()
    if not s:
        return None
    m = _DATE_RE.match(s)
    if not m:
        raise ValueError("format")
    d, mo, y = (int(x) for x in m.groups())
    result = date(y, mo, d)  # noto'g'ri kun/oy -> ValueError
    if not 1900 <= y <= date.today().year:
        raise ValueError("range")
    return result


def decode_photo(data_url: str) -> tuple[bytes, str]:
    """data:image/...;base64,... -> (bytes, mime). Turi Pillow bilan tekshiriladi (faqat JPEG/PNG)."""
    m = _DATA_URL_RE.match(data_url)
    if not m:
        raise ValueError("photo-format")
    try:
        raw = base64.b64decode(m.group(2), validate=False)
    except (binascii.Error, ValueError) as e:
        raise ValueError("photo-base64") from e
    if len(raw) > MAX_PHOTO_BYTES:
        raise ValueError("photo-size")
    try:
        with Image.open(io.BytesIO(raw)) as im:
            fmt = im.format or ""
            im.verify()
    except (UnidentifiedImageError, OSError, SyntaxError) as e:
        raise ValueError("photo-invalid") from e
    if fmt not in ALLOWED_PHOTO_FORMATS:
        raise ValueError("photo-type")
    return raw, ALLOWED_PHOTO_FORMATS[fmt]


class _Base(BaseModel):
    model_config = ConfigDict(extra="ignore", str_max_length=2000, validate_default=True)

    @field_validator("*", mode="before")
    @classmethod
    def _none_to_empty(cls, v: Any, info: ValidationInfo) -> Any:
        # JSON importda null kelishi mumkin: satr maydonlari uchun bo'sh satrga aylantiramiz,
        # raqamlarni (masalan, yil 1976) satrga.
        if info.field_name and cls.model_fields[info.field_name].annotation is str:
            if v is None:
                return ""
            if isinstance(v, int | float) and not isinstance(v, bool):
                return str(v)
        return v


class MehnatDavr(_Base):
    """Mehnat faoliyatidagi bitta davr. ``gacha`` bo'sh bo'lsa — hozirgi vaqtgacha (h.v.)."""

    dan: str = Field(default="", max_length=10)
    gacha: str = Field(default="", max_length=10)
    matn: str = Field(default="", max_length=LONG)

    _year = field_validator("dan", "gacha")(_check_year)

    def is_filled(self) -> bool:
        return has(self.dan) or has(self.matn)


class Qarindosh(_Base):
    """Yaqin qarindosh (2-sahifadagi jadval qatori)."""

    rel: str = Field(default="", max_length=SHORT)
    fish: str = Field(default="", max_length=SHORT)
    yil: str = Field(default="", max_length=10)
    joy: str = Field(default="", max_length=SHORT)
    ish: str = Field(default="", max_length=LONG)
    turar: str = Field(default="", max_length=LONG)

    _year = field_validator("yil")(_check_year)

    def is_filled(self) -> bool:
        return has(self.rel) or has(self.fish)


class Obyektivka(_Base):
    lang: LangCode = "lat"
    fish: str = Field(default="", max_length=SHORT)
    lavozim: str = Field(default="", max_length=LONG)
    tugSana: str = Field(default="", max_length=20)
    tugJoy: str = Field(default="", max_length=SHORT)
    millati: str = Field(default="", max_length=SHORT)
    partiya: str = Field(default="", max_length=SHORT)
    malumoti: str = Field(default="", max_length=SHORT)
    tamomlagan: str = Field(default="", max_length=LONG)
    mutaxassislik: str = Field(default="", max_length=SHORT)
    ilmiyDaraja: str = Field(default="", max_length=SHORT)
    ilmiyUnvon: str = Field(default="", max_length=SHORT)
    tillar: str = Field(default="", max_length=SHORT)
    mukofot: str = Field(default="", max_length=LONG)
    deputat: str = Field(default="", max_length=LONG)
    photo: str = Field(default="", max_length=6 * 1024 * 1024)
    mehnat: list[MehnatDavr] = Field(default_factory=list, max_length=60)
    qarindosh: list[Qarindosh] = Field(default_factory=list, max_length=40)

    @field_validator("lang", mode="before")
    @classmethod
    def _lang(cls, v: Any) -> Any:
        return v if v in ("new", "lat", "cyr", "ru") else "lat"

    @field_validator("tugSana")
    @classmethod
    def _date(cls, v: str) -> str:
        try:
            parse_birth_date(v)
        except ValueError as e:
            raise PydanticCustomError("date", "Sana DD.MM.YYYY formatida bo'lishi kerak") from e
        return v

    @field_validator("photo")
    @classmethod
    def _photo(cls, v: str) -> str:
        if v:
            try:
                decode_photo(v)
            except ValueError as e:
                raise PydanticCustomError("photo", "Rasm noto'g'ri: {reason}", {"reason": str(e)}) from e
        return v

    # --- yordamchilar (prototipdagi filtrlar bilan bir xil) ---
    def filled_mehnat(self) -> list[MehnatDavr]:
        return [m for m in self.mehnat if m.is_filled()]

    def filled_qarindosh(self) -> list[Qarindosh]:
        return [r for r in self.qarindosh if r.is_filled()]

    def photo_bytes(self) -> bytes | None:
        return decode_photo(self.photo)[0] if self.photo else None


# --- xatolar ---
ERROR_UI_KEYS = {"date": "errDate", "year": "errYear", "photo": "tPhotoType"}


def errors_for_client(exc: ValidationError) -> list[dict[str, str]]:
    """Pydantic xatolari -> [{"loc": "mehnat.0.dan", "key": "errYear"}] (forma maydonini belgilash uchun)."""
    out = []
    for err in exc.errors():
        loc = ".".join(str(x) for x in err["loc"])
        out.append({"loc": loc, "key": ERROR_UI_KEYS.get(err["type"], "tInvalid")})
    return out


def lenient(data: Any) -> Obyektivka:
    """Jonli preview uchun: noto'g'ri maydonlarni tashlab yuborib, qolganini ko'rsatadi.

    Foydalanuvchi yil yoki sanani yozib bo'lmaguncha ham varaq yangilanib turishi kerak.
    Noto'g'ri qiymat matn sifatida qoladi (prototipdagidek), faqat rasm olib tashlanadi.
    """
    if not isinstance(data, dict):
        return Obyektivka()
    try:
        return Obyektivka.model_validate(data)
    except ValidationError as exc:
        bad = {tuple(e["loc"]) for e in exc.errors()}
    cleaned: dict[str, Any] = dict(data)
    model = Obyektivka.model_construct()
    # Matn maydonlari: uzunlik cheklovi bilan, validatsiyasiz
    for k in TEXT_FIELDS:
        v = cleaned.get(k, "")
        setattr(model, k, str(v)[:2000] if v is not None else "")
    lang = cleaned.get("lang")
    model.lang = cast(LangCode, lang if lang in ("new", "lat", "cyr", "ru") else "lat")
    model.photo = "" if any(loc and loc[0] == "photo" for loc in bad) else str(cleaned.get("photo") or "")

    def rows(key: str, cls: type[_Base], fields: tuple[str, ...]) -> list[Any]:
        src = cleaned.get(key)
        if not isinstance(src, list):
            return []
        result = []
        for item in src[:60]:
            if not isinstance(item, dict):
                continue
            values: dict[str, Any] = {f: str(item.get(f) or "")[:2000] for f in fields}
            result.append(cls.model_construct(None, **values))
        return result

    model.mehnat = rows("mehnat", MehnatDavr, ("dan", "gacha", "matn"))
    model.qarindosh = rows("qarindosh", Qarindosh, ("rel", "fish", "yil", "joy", "ish", "turar"))
    return model
