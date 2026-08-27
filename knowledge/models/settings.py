from __future__ import annotations

from dataclasses import asdict, dataclass, field

from knowledge.constants import DEFAULT_HOTKEY
from knowledge.shared.appearance import Appearance
from knowledge.shared.color_system import normalize_saved_colors
POPUP_NEAR_MOUSE = "near_mouse"
POPUP_CENTER = "center"


@dataclass
class AppSettings:
    hotkey: str = DEFAULT_HOTKEY
    capture_selected_text: bool = True
    restore_clipboard: bool = True
    focus_search_when_empty: bool = True
    popup_position: str = POPUP_NEAR_MOUSE
    minimize_to_tray: bool = True
    start_minimized: bool = False
    capture_delay_ms: int = 120
    saved_colors: list[str] = field(default_factory=list)
    appearance: Appearance = field(default_factory=Appearance)

    def to_dict(self) -> dict:
        data = asdict(self)
        data["appearance"] = self.appearance.to_dict()
        return data

    @classmethod
    def from_dict(cls, data: dict | None) -> AppSettings:
        data = data or {}
        popup = str(data.get("popup_position") or POPUP_NEAR_MOUSE)
        if popup not in (POPUP_NEAR_MOUSE, POPUP_CENTER):
            popup = POPUP_NEAR_MOUSE
        delay = data.get("capture_delay_ms", 120)
        try:
            delay_i = max(40, min(800, int(delay)))
        except (TypeError, ValueError):
            delay_i = 120
        return cls(
            hotkey=str(data.get("hotkey") or DEFAULT_HOTKEY),
            capture_selected_text=bool(data.get("capture_selected_text", True)),
            restore_clipboard=bool(data.get("restore_clipboard", True)),
            focus_search_when_empty=bool(data.get("focus_search_when_empty", True)),
            popup_position=popup,
            minimize_to_tray=bool(data.get("minimize_to_tray", True)),
            start_minimized=bool(data.get("start_minimized", False)),
            capture_delay_ms=delay_i,
            saved_colors=normalize_saved_colors(data.get("saved_colors")),
            appearance=Appearance.from_dict(data.get("appearance")),
        )
