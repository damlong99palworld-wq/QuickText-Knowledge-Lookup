from __future__ import annotations

import time

from . import clipboard
from .win_focus import restore_foreground, send_ctrl_v


def paste_text(text: str, hwnd: int, restore_clip: bool = True, copy_only: bool = False) -> None:
    snap = None
    if restore_clip and not copy_only:
        snap = clipboard.save()
    try:
        ok = clipboard.set_text(text)
        if not ok:
            return
        if copy_only:
            return
        restore_foreground(hwnd)
        time.sleep(0.08)
        send_ctrl_v()
        time.sleep(0.12)
    finally:
        if restore_clip and snap is not None and not copy_only:
            time.sleep(0.05)
            try:
                clipboard.restore(snap)
            except Exception:
                pass
