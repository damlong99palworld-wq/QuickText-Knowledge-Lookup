from __future__ import annotations

from dataclasses import dataclass


MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008
MOD_NOREPEAT = 0x4000
WM_HOTKEY = 0x0312
HOTKEY_ID = 0x4B4C01


@dataclass
class ParsedHotkey:
    display: str
    modifiers: int
    vk: int
    qt_sequence: str


_VK_MAP = {f"F{i}": 0x6F + i for i in range(1, 25)}
_VK_MAP.update(
    {
        "TAB": 0x09,
        "SPACE": 0x20,
        "ENTER": 0x0D,
        "RETURN": 0x0D,
        "ESC": 0x1B,
        "ESCAPE": 0x1B,
        "INSERT": 0x2D,
        "DELETE": 0x2E,
        "HOME": 0x24,
        "END": 0x23,
        "PGUP": 0x21,
        "PGDN": 0x22,
        "UP": 0x26,
        "DOWN": 0x28,
        "LEFT": 0x25,
        "RIGHT": 0x27,
    }
)


def parse_hotkey(text: str) -> ParsedHotkey:
    raw = (text or "").strip()
    if not raw:
        raise ValueError("Hotkey is empty.")
    parts = [p.strip() for p in raw.replace("-", "+").split("+") if p.strip()]
    mods = 0
    key = ""
    qt_mods: list[str] = []
    for part in parts:
        token = part.upper()
        if token in {"CTRL", "CONTROL"}:
            mods |= MOD_CONTROL
            qt_mods.append("Ctrl")
        elif token in {"SHIFT"}:
            mods |= MOD_SHIFT
            qt_mods.append("Shift")
        elif token in {"ALT"}:
            mods |= MOD_ALT
            qt_mods.append("Alt")
        elif token in {"WIN", "WINDOWS", "META", "SUPER"}:
            mods |= MOD_WIN
            qt_mods.append("Meta")
        else:
            if key:
                raise ValueError(f"Too many keys in hotkey: {text}")
            key = token
    if not key:
        raise ValueError(f"No key in hotkey: {text}")
    if key in _VK_MAP:
        vk = _VK_MAP[key]
        qt_key = key if key.startswith("F") else key.title()
    elif len(key) == 1 and ("A" <= key <= "Z" or "0" <= key <= "9"):
        vk = ord(key)
        qt_key = key
    else:
        raise ValueError(f"Unsupported hotkey key: {key}")
    if mods == 0:
        raise ValueError("Use at least one modifier (Ctrl, Alt, Shift).")
    display_parts = []
    if mods & MOD_CONTROL:
        display_parts.append("Ctrl")
    if mods & MOD_SHIFT:
        display_parts.append("Shift")
    if mods & MOD_ALT:
        display_parts.append("Alt")
    if mods & MOD_WIN:
        display_parts.append("Win")
    display_parts.append(key if key.startswith("F") else key)
    display = "+".join(display_parts)
    qt_seq = "+".join(qt_mods + [qt_key])
    return ParsedHotkey(display=display, modifiers=mods, vk=vk, qt_sequence=qt_seq)
