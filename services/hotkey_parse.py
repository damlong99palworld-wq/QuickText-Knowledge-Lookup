from __future__ import annotations

MOD_ALT, MOD_CONTROL, MOD_SHIFT, MOD_WIN, MOD_NOREPEAT = 0x0001, 0x0002, 0x0004, 0x0008, 0x4000

VK_MAP = {**{str(i): 0x30 + i for i in range(10)}, **{chr(c): c for c in range(ord("a"), ord("z") + 1)}}
for i in range(1, 25):
    VK_MAP[f"f{i}"] = 0x6F + i
VK_MAP.update({
    "space": 0x20, "tab": 0x09, "enter": 0x0D, "esc": 0x1B, "escape": 0x1B,
    "insert": 0x2D, "delete": 0x2E, "home": 0x24, "end": 0x23,
    "pgup": 0x21, "pgdn": 0x22, "up": 0x26, "down": 0x28, "left": 0x25, "right": 0x27,
    "plus": 0xBB, "minus": 0xBD, "comma": 0xBC, "period": 0xBE,
})


def parse_hotkey(combo: str) -> tuple[int, int] | None:
    if not combo:
        return None
    parts = [p.strip().lower() for p in combo.replace(" ", "").split("+") if p.strip()]
    if not parts:
        return None
    mods = 0
    key = ""
    for p in parts:
        if p in ("ctrl", "control"):
            mods |= MOD_CONTROL
        elif p == "shift":
            mods |= MOD_SHIFT
        elif p == "alt":
            mods |= MOD_ALT
        elif p in ("win", "meta", "super"):
            mods |= MOD_WIN
        else:
            key = p
    vk = VK_MAP.get(key)
    if not vk:
        return None
    return mods | MOD_NOREPEAT, vk
