from __future__ import annotations

import re

from knowledge.constants import MAX_SAVED_COLORS

# Same contract as QuickText: empty string = default UI color,
# stored values are #rrggbb (Qt QColor.name()).
HEX_RE = re.compile(r"^#([0-9a-fA-F]{6})$")


def normalize_hex(value: str | None) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    if raw.startswith("0x") and len(raw) == 8:
        raw = "#" + raw[2:]
    if not raw.startswith("#") and len(raw) == 6:
        raw = "#" + raw
    if not HEX_RE.match(raw):
        return ""
    return "#" + raw[1:].lower()


def push_saved_color(saved: list[str], color: str) -> list[str]:
    hex_color = normalize_hex(color)
    if not hex_color:
        return [normalize_hex(c) for c in saved if normalize_hex(c)][:MAX_SAVED_COLORS]
    cleaned: list[str] = []
    for item in saved:
        item_n = normalize_hex(item)
        if item_n and item_n != hex_color and item_n not in cleaned:
            cleaned.append(item_n)
    return [hex_color, *cleaned][:MAX_SAVED_COLORS]


def normalize_saved_colors(values) -> list[str]:
    out: list[str] = []
    if not values:
        return out
    for item in values:
        hex_color = normalize_hex(str(item))
        if hex_color and hex_color not in out:
            out.append(hex_color)
        if len(out) >= MAX_SAVED_COLORS:
            break
    return out
