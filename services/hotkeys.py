from __future__ import annotations

import ctypes
import sys
from ctypes import wintypes

from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtWidgets import QWidget

from services.hotkey_parse import parse_hotkey
from models.snippet import format_hotkey_display

WM_HOTKEY = 0x0312


class _MsgWindow(QWidget):
    hotkey_id = Signal(int)

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("QuickTextHotkeys")
        self.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
        self.resize(1, 1)
        self.show()
        self.hide()
        self.createWinId()

    def nativeEvent(self, eventType, message):  # noqa: N802
        et = bytes(eventType) if not isinstance(eventType, (bytes, bytearray)) else eventType
        if et in (b"windows_generic_MSG", b"windows_dispatcher_MSG"):
            try:
                msg = ctypes.wintypes.MSG.from_address(int(message))
            except Exception:
                return False, 0
            if msg.message == WM_HOTKEY:
                self.hotkey_id.emit(int(msg.wParam))
                return True, 0
        return False, 0


class HotkeyBridge(QObject):
    open_menu = Signal()
    paste_snippet = Signal(str)


class HotkeyService:
    MENU_ID = 1
    SNIP_BASE = 100

    def __init__(self, bridge: HotkeyBridge) -> None:
        self.bridge = bridge
        self._hwnd = 0
        self._bound_ids: list[int] = []
        self._snip_by_id: dict[int, str] = {}
        self.last_hwnd = 0
        self._win: _MsgWindow | None = None
        if sys.platform == "win32":
            self._user32 = ctypes.WinDLL("user32", use_last_error=True)
            self._user32.RegisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int, wintypes.UINT, wintypes.UINT]
            self._user32.RegisterHotKey.restype = wintypes.BOOL
            self._user32.UnregisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int]
            self._user32.UnregisterHotKey.restype = wintypes.BOOL
            self._win = _MsgWindow()
            self._hwnd = int(self._win.winId())
            self._win.hotkey_id.connect(self._on_id)
        else:
            self._user32 = None

    def _on_id(self, hid: int) -> None:
        try:
            from services.win_focus import get_foreground_hwnd

            self.last_hwnd = get_foreground_hwnd()
        except Exception:
            self.last_hwnd = 0
        if hid == self.MENU_ID:
            self.bridge.open_menu.emit()
            return
        sid = self._snip_by_id.get(hid)
        if sid:
            self.bridge.paste_snippet.emit(sid)

    def clear(self) -> None:
        if not self._user32 or not self._hwnd:
            self._bound_ids.clear()
            return
        for hid in self._bound_ids:
            self._user32.UnregisterHotKey(self._hwnd, hid)
        self._bound_ids.clear()
        self._snip_by_id.clear()

    def bind(self, menu_hotkey: str, snippet_hotkeys: dict[str, str]) -> str | None:
        self.clear()
        if sys.platform != "win32":
            return None
        failed: list[str] = []
        parsed = parse_hotkey(menu_hotkey)
        if not parsed:
            return f"Invalid palette hotkey: {format_hotkey_display(menu_hotkey) or menu_hotkey}"
        mods, vk = parsed
        if not self._user32.RegisterHotKey(self._hwnd, self.MENU_ID, mods, vk):
            failed.append(format_hotkey_display(menu_hotkey) or menu_hotkey or "(palette)")
        else:
            self._bound_ids.append(self.MENU_ID)
        i = 0
        for combo, sid in snippet_hotkeys.items():
            if not combo:
                continue
            p = parse_hotkey(combo)
            if not p:
                failed.append(format_hotkey_display(combo) or combo)
                continue
            hid = self.SNIP_BASE + i
            i += 1
            mods, vk = p
            if not self._user32.RegisterHotKey(self._hwnd, hid, mods, vk):
                failed.append(format_hotkey_display(combo) or combo)
                continue
            self._bound_ids.append(hid)
            self._snip_by_id[hid] = sid
        if failed:
            return "Could not register (already in use): " + ", ".join(failed)
        return None
