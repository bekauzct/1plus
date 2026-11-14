"""Editor formasi tuzilishi (prototipdagi 5 bo'lim). Shablon shu ro'yxat bo'yicha maydonlarni chizadi."""

from __future__ import annotations

from typing import Any

# (kalit, yorliq, placeholder kaliti yoki None, turi, chips manbasi, qo'shimcha)
SECTIONS: list[dict[str, Any]] = [
    {
        "n": 1,
        "title": "s1",
        "photo": True,
        "rows": [
            [{"key": "fish", "label": "fFish", "ph": "phFish"}],
            [{"key": "lavozim", "label": "fLav", "ph": "phLav", "type": "textarea", "hint": "hLav"}],
            [
                {
                    "key": "tugSana",
                    "label": "fTugSana",
                    "ph_raw": "12.03.2006",
                    "inputmode": "numeric",
                    "date": True,
                },
                {"key": "millati", "label": "fMillati", "ph": "phMillati"},
            ],
            [{"key": "tugJoy", "label": "fTugJoy", "ph": "phTugJoy"}],
            [{"key": "partiya", "label": "fPartiya", "ph": "no", "chips": "no"}],
        ],
    },
    {
        "n": 2,
        "title": "s2",
        "rows": [
            [{"key": "malumoti", "label": "fMal", "ph": "phMal", "chips": "malChips"}],
            [{"key": "tamomlagan", "label": "fTam", "ph": "phTam", "type": "textarea"}],
            [{"key": "mutaxassislik", "label": "fMut", "ph": "phMut"}],
            [
                {"key": "ilmiyDaraja", "label": "fIlD", "ph": "no", "chips": "no"},
                {"key": "ilmiyUnvon", "label": "fIlU", "ph": "no", "chips": "no"},
            ],
        ],
    },
    {
        "n": 3,
        "title": "s3",
        "rows": [
            [{"key": "tillar", "label": "fTil", "ph": "phTil", "chips": "tilChips", "append": True}],
            [{"key": "mukofot", "label": "fMuk", "ph": "no", "chips": "no"}],
            [{"key": "deputat", "label": "fDep", "ph": "no", "chips": "no"}],
        ],
    },
]


def resolve(ui: dict[str, Any]) -> list[dict[str, Any]]:
    """UI lug'atidagi matnlarni qo'yib, shablon uchun tayyor ro'yxat qaytaradi."""
    out = []
    for sec in SECTIONS:
        rows = []
        for row in sec["rows"]:
            fields = []
            for f in row:
                chips = ui[f["chips"]] if f.get("chips") else []
                fields.append(
                    {
                        **f,
                        "label_text": ui[f["label"]],
                        "placeholder": f.get("ph_raw") or (ui[f["ph"]] if f.get("ph") else ""),
                        "hint_text": ui[f["hint"]] if f.get("hint") else "",
                        "chip_list": chips if isinstance(chips, list) else [chips],
                        "type": f.get("type", "input"),
                    }
                )
            rows.append(fields)
        out.append({"n": sec["n"], "title": ui[sec["title"]], "photo": sec.get("photo", False), "rows": rows})
    return out
