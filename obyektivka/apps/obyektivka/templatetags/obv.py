"""Shablon filtrlari (builtins sifatida ulangan — {% load %} shart emas)."""

import json
from typing import Any

from django import template
from django.utils.safestring import SafeString, mark_safe

register = template.Library()


@register.filter
def trim(value: Any) -> str:
    """Bo'shliqlarni olib tashlaydi: prototipdagi has() tekshiruvi uchun ``{% if v|trim %}``."""
    return "" if value is None else str(value).strip()


@register.filter
def json_script_safe(value: Any) -> SafeString:
    """<script> ichiga xavfsiz JSON (</script> va HTML belgilari escape qilinadi)."""
    s = json.dumps(value, ensure_ascii=False)
    s = s.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    s = s.replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    return mark_safe(s)
