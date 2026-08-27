from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtWidgets import QApplication


import uuid

SENTINEL = "\u2063KLSEL\u2063"


def new_sentinel() -> str:
    return f"__QUICKTEXT_SELECTION_SENTINEL_{uuid.uuid4().hex}__"


@dataclass
class TextClipboardSnapshot:
    text: str
    had_text: bool


def clipboard():
    app = QApplication.instance()
    if app is None:
        return None
    return app.clipboard()


def snapshot_text() -> TextClipboardSnapshot:
    cb = clipboard()
    if cb is None:
        return TextClipboardSnapshot("", False)
    text = cb.text()
    return TextClipboardSnapshot(text=text or "", had_text=bool(text))


def set_text(text: str) -> None:
    cb = clipboard()
    if cb is None:
        return
    cb.setText(text or "")


def current_text() -> str:
    cb = clipboard()
    if cb is None:
        return ""
    return cb.text() or ""


def restore_text(snap: TextClipboardSnapshot) -> None:
    cb = clipboard()
    if cb is None:
        return
    cb.setText(snap.text or "")
