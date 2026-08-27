from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


def _norm_hotkey(value: str | None) -> str:
    if not value:
        return ""
    parts = [p.strip().lower() for p in value.replace(" ", "").split("+") if p.strip()]
    order = ["ctrl", "shift", "alt", "win"]
    mods = [m for m in order if m in parts]
    key = next((p for p in parts if p not in order), "")
    return "+".join([*mods, key]) if key else "+".join(mods)


def format_hotkey_display(value: str | None) -> str:
    """ctrl+shift+f1 -> Ctrl+Shift+F1"""
    if not value:
        return ""
    parts = [p.strip().lower() for p in value.replace(" ", "").split("+") if p.strip()]
    out: list[str] = []
    for p in parts:
        if p in ("ctrl", "control"):
            out.append("Ctrl")
        elif p == "shift":
            out.append("Shift")
        elif p == "alt":
            out.append("Alt")
        elif p in ("win", "meta", "super"):
            out.append("Win")
        elif p.startswith("f") and p[1:].isdigit():
            out.append("F" + p[1:])
        elif len(p) == 1:
            out.append(p.upper())
        else:
            out.append(p.capitalize())
    return "+".join(out)


@dataclass
class Snippet:
    id: str
    name: str
    text: str
    category: str = "General"
    favorite: bool = False
    hotkey: str = ""
    action: str = "default"
    show_in_palette: bool = True
    color: str = ""
    usage_count: int = 0
    last_used: float | None = None
    created_at: float = 0.0
    updated_at: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["hotkey"] = _norm_hotkey(self.hotkey)
        return d

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> Snippet:
        return cls(
            id=str(raw.get("id") or ""),
            name=str(raw.get("name") or ""),
            text=str(raw.get("text") or ""),
            category=str(raw.get("category") or "General"),
            favorite=bool(raw.get("favorite")),
            hotkey=_norm_hotkey(str(raw.get("hotkey") or "")),
            action=str(raw.get("action") or "default"),
            show_in_palette=bool(raw.get("show_in_palette", True)),
            color=str(raw.get("color") or ""),
            usage_count=int(raw.get("usage_count") or 0),
            last_used=raw.get("last_used"),
            created_at=float(raw.get("created_at") or 0),
            updated_at=float(raw.get("updated_at") or 0),
        )


@dataclass
class Settings:
    open_menu_hotkey: str = "ctrl+f1"
    restore_clipboard: bool = True
    start_minimized: bool = True
    show_tray: bool = True
    start_with_windows: bool = False
    popup_position: str = "mouse"
    close_after_select: bool = True
    insert_mode: str = "paste"
    recent_limit: int = 8
    saved_colors: list = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["open_menu_hotkey"] = _norm_hotkey(self.open_menu_hotkey)
        return d

    @classmethod
    def from_dict(cls, raw: dict[str, Any] | None) -> Settings:
        raw = raw or {}
        return cls(
            open_menu_hotkey=_norm_hotkey(str(raw.get("open_menu_hotkey") or "ctrl+f1")),
            restore_clipboard=bool(raw.get("restore_clipboard", True)),
            start_minimized=bool(raw.get("start_minimized", True)),
            show_tray=bool(raw.get("show_tray", True)),
            start_with_windows=bool(raw.get("start_with_windows", False)),
            popup_position=str(raw.get("popup_position") or "mouse"),
            close_after_select=bool(raw.get("close_after_select", True)),
            insert_mode=str(raw.get("insert_mode") or "paste"),
            recent_limit=int(raw.get("recent_limit") or 8),
            saved_colors=[str(c) for c in (raw.get("saved_colors") or []) if c],
        )


@dataclass
class AppData:
    settings: Settings = field(default_factory=Settings)
    categories: list[str] = field(default_factory=lambda: ["General"])
    category_colors: dict = field(default_factory=dict)
    snippets: list[Snippet] = field(default_factory=list)
    recent: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "settings": self.settings.to_dict(),
            "categories": self.categories,
            "category_colors": dict(self.category_colors or {}),
            "snippets": [s.to_dict() for s in self.snippets],
            "recent": self.recent,
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> AppData:
        cats = raw.get("categories") or ["General"]
        if "General" not in cats:
            cats = ["General", *cats]
        snippets = [Snippet.from_dict(x) for x in raw.get("snippets") or [] if isinstance(x, dict)]
        cc_raw = raw.get("category_colors") or {}
        category_colors = {str(k): str(v) for k, v in cc_raw.items()} if isinstance(cc_raw, dict) else {}
        return cls(
            settings=Settings.from_dict(raw.get("settings") if isinstance(raw.get("settings"), dict) else {}),
            categories=list(cats),
            category_colors=category_colors,
            snippets=snippets,
            recent=[str(x) for x in raw.get("recent") or []],
        )

    def snippet_by_id(self, sid: str) -> Snippet | None:
        return next((s for s in self.snippets if s.id == sid), None)

    def hotkey_conflict(self, hotkey: str, except_id: str | None = None) -> str | None:
        h = _norm_hotkey(hotkey)
        if not h:
            return None
        if h == _norm_hotkey(self.settings.open_menu_hotkey):
            return f"Open Menu ({format_hotkey_display(self.settings.open_menu_hotkey)})"
        for s in self.snippets:
            if s.id != except_id and _norm_hotkey(s.hotkey) == h:
                return s.name
        return None
