"""Watch mouse drag-select and copy highlighted text. Windows has no copy-on-select."""

from __future__ import annotations

import sys

from PySide6.QtCore import QObject, QPoint, QTimer, Signal
from PySide6.QtGui import QCursor

VK_LBUTTON = 0x01


class SelectWatch(QObject):
    copied = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._down: QPoint | None = None
        self._busy = False
        self._ignore_hwnds: set[int] = set()
        self._timer = QTimer(self)
        self._timer.setInterval(25)
        self._timer.timeout.connect(self._tick)

    def add_ignore_hwnd(self, hwnd: int) -> None:
        if hwnd:
            self._ignore_hwnds.add(int(hwnd))

    def start(self) -> None:
        if sys.platform == "win32":
            self._timer.start()

    def stop(self) -> None:
        self._timer.stop()

    def _left_down(self) -> bool:
        import ctypes

        return bool(ctypes.windll.user32.GetAsyncKeyState(VK_LBUTTON) & 0x8000)

    def _tick(self) -> None:
        if self._busy:
            return
        from services.win_focus import get_foreground_hwnd

        down = self._left_down()
        pos = QCursor.pos()
        if down and self._down is None:
            hwnd = get_foreground_hwnd()
            if hwnd in self._ignore_hwnds:
                return
            self._down = pos
            return
        if down or self._down is None:
            return
        start = self._down
        self._down = None
        if abs(pos.x() - start.x()) + abs(pos.y() - start.y()) < 8:
            return
        hwnd = get_foreground_hwnd()
        if hwnd in self._ignore_hwnds:
            return
        self._busy = True
        QTimer.singleShot(40, self._copy)

    def _copy(self) -> None:
        try:
            from services.selection_capture import try_capture_selected_text
            from services import clipboard as winclip

            text = try_capture_selected_text(delay_ms=160) or ""
            if text:
                winclip.set_text(text)
                print(f"[QuickText] Auto-copied selection: {text!r}", flush=True)
                self.copied.emit(text)
        finally:
            self._busy = False
