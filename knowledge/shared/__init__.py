"""Reusable pieces intended for a later QuickText merge (colors, appearance)."""

from .color_system import MAX_SAVED_COLORS, normalize_hex, normalize_saved_colors, push_saved_color
from .appearance import Appearance, TextStyle

__all__ = [
    "MAX_SAVED_COLORS",
    "normalize_hex",
    "normalize_saved_colors",
    "push_saved_color",
    "Appearance",
    "TextStyle",
]
