"""Shared selected-text detection for the main QuickText hotkey."""

from __future__ import annotations

from knowledge.constants import MAX_SELECTION_LEN
from knowledge.services.selection_capture import capture_selected_text


def try_capture_selected_text(max_len: int = MAX_SELECTION_LEN, delay_ms: int = 120) -> str | None:
    """Return trimmed selected text, or None if there is no usable selection."""
    result = capture_selected_text(restore_clipboard=True, delay_ms=delay_ms)
    if not result.had_selection:
        return None
    text = (result.text or "").strip()
    if not text:
        return None
    if len(text) > max_len:
        text = text[:max_len].strip()
    return text or None
