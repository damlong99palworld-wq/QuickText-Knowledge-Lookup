from __future__ import annotations

import sys

from PySide6.QtCore import QAbstractNativeEventFilter, QObject, Signal

from knowledge.services.hotkey_spec import (
    HOTKEY_ID,
    MOD_NOREPEAT,
    WM_HOTKEY,
    parse_hotkey,
)


class _WindowsHotkeyFilter(QAbstractNativeEventFilter):
    def __init__(self, callback):
        super().__init__()
        self.callback = callback

    def nativeEventFilter(self, eventType, message):  # noqa: N802
        et = bytes(eventType) if not isinstance(eventType, (bytes, bytearray)) else eventType
        if et not in (b"windows_generic_MSG", b"windows_dispatcher_MSG"):
            return False
        try:
            import ctypes
            from ctypes import wintypes

            class MSG(ctypes.Structure):
                _fields_ = [
                    ("hwnd", wintypes.HWND),
                    ("message", wintypes.UINT),
                    ("wParam", wintypes.WPARAM),
                    ("lParam", wintypes.LPARAM),
                    ("time", wintypes.DWORD),
                    ("pt", wintypes.POINT),
                ]

            msg = MSG.from_address(int(message))
            if msg.message == WM_HOTKEY and int(msg.wParam) == HOTKEY_ID:
                self.callback()
        except Exception:
            return False
        return False


class HotkeyManager(QObject):
    triggered = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._hwnd = None
        self._filter = None
        self.last_error = ""
        self.registered_display = ""

    def bind_hwnd(self, hwnd) -> None:
        self._hwnd = int(hwnd) if hwnd else None

    def register(self, hotkey_text: str) -> bool:
        self.last_error = ""
        self.unregister()
        try:
            parsed = parse_hotkey(hotkey_text)
        except ValueError as exc:
            self.last_error = str(exc)
            return False
        if sys.platform != "win32":
            self.registered_display = parsed.display
            self.last_error = (
                "Global hotkeys use Windows RegisterHotKey. "
                "On this OS the hotkey is stored but not globally registered."
            )
            return False
        if not self._hwnd:
            self.last_error = "No window handle available for RegisterHotKey."
            return False
        import ctypes

        ok = ctypes.windll.user32.RegisterHotKey(
            self._hwnd,
            HOTKEY_ID,
            parsed.modifiers | MOD_NOREPEAT,
            parsed.vk,
        )
        if not ok:
            self.last_error = (
                f"Could not register {parsed.display}. "
                "This hotkey may already be in use."
            )
            return False
        if self._filter is None:
            from PySide6.QtWidgets import QApplication

            self._filter = _WindowsHotkeyFilter(self.triggered.emit)
            app = QApplication.instance()
            if app is not None:
                app.installNativeEventFilter(self._filter)
        self.registered_display = parsed.display
        return True

    def unregister(self) -> None:
        self.registered_display = ""
        if sys.platform != "win32" or not self._hwnd:
            return
        try:
            import ctypes

            ctypes.windll.user32.UnregisterHotKey(self._hwnd, HOTKEY_ID)
        except Exception:
            pass
