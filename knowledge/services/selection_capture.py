from __future__ import annotations

import sys
import time
from dataclasses import dataclass

from knowledge.services import clipboard as clip


@dataclass
class CaptureResult:
    text: str
    had_selection: bool
    error: str = ""


def send_copy_windows() -> str:
    try:
        import ctypes
        from ctypes import wintypes
    except Exception as exc:
        return f"ctypes unavailable: {exc}"

    KEYEVENTF_KEYUP = 0x0002
    INPUT_KEYBOARD = 1
    VK_CONTROL = 0x11
    VK_C = 0x43

    class KEYBDINPUT(ctypes.Structure):
        _fields_ = [
            ("wVk", wintypes.WORD),
            ("wScan", wintypes.WORD),
            ("dwFlags", wintypes.DWORD),
            ("time", wintypes.DWORD),
            ("dwExtraInfo", ctypes.c_size_t),
        ]

    class INPUT_UNION(ctypes.Union):
        _fields_ = [("ki", KEYBDINPUT)]

    class INPUT(ctypes.Structure):
        _fields_ = [("type", wintypes.DWORD), ("union", INPUT_UNION)]

    def make(vk: int, flags: int = 0) -> INPUT:
        inp = INPUT()
        inp.type = INPUT_KEYBOARD
        inp.union.ki = KEYBDINPUT(vk, 0, flags, 0, 0)
        return inp

    events = (INPUT * 4)(
        make(VK_CONTROL, 0),
        make(VK_C, 0),
        make(VK_C, KEYEVENTF_KEYUP),
        make(VK_CONTROL, KEYEVENTF_KEYUP),
    )
    sent = ctypes.windll.user32.SendInput(4, events, ctypes.sizeof(INPUT))
    if sent != 4:
        return "SendInput failed to send Ctrl+C."
    return ""


def send_copy() -> str:
    if sys.platform == "win32":
        return send_copy_windows()
    return "Selected-text capture via Ctrl+C is implemented for Windows only."


def capture_selected_text(restore_clipboard: bool = True, delay_ms: int = 120) -> CaptureResult:
    """Read current selection by sending Ctrl+C, then restore previous text clipboard.

    V1.1 restores Unicode text only. Rich formats (HTML, images, files) are not
    snapshotted. Some apps ignore synthetic Ctrl+C or delay longer than delay_ms.
    """
    original = clip.snapshot_text()
    sentinel = clip.new_sentinel()
    clip.set_text(sentinel)
    err = send_copy()
    if err and sys.platform != "win32":
        if restore_clipboard:
            clip.restore_text(original)
        return CaptureResult("", False, err)

    wait_s = max(0.04, delay_ms / 1000.0)
    time.sleep(wait_s)
    text = clip.current_text()
    if text == sentinel:
        time.sleep(wait_s)
        text = clip.current_text()

    if restore_clipboard:
        clip.restore_text(original)
    elif text == sentinel:
        clip.restore_text(original)

    if not text or text == sentinel:
        return CaptureResult("", False, err)
    if text == original.text and text != sentinel:
        # App ignored Ctrl+C; clipboard never changed from original after we set sentinel
        # then copied. If it copied the same string as original, treat as selection.
        return CaptureResult(text.strip(), True, err)
    cleaned = text.strip()
    if not cleaned:
        return CaptureResult("", False, err)
    return CaptureResult(cleaned, True, err)
