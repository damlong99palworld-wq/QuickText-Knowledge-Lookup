from __future__ import annotations

from PySide6.QtGui import QColor, QFont, QTextOption
from PySide6.QtWidgets import QLabel, QTextEdit

from knowledge.shared.appearance import Appearance, TextStyle, scale_size


def qfont_from_style(style: TextStyle, zoom: int = 100) -> QFont:
    family = style.font_family or "Segoe UI"
    size = scale_size(style.font_size or 13, zoom)
    font = QFont(family, size)
    font.setBold(bool(style.bold))
    font.setItalic(bool(style.italic))
    font.setUnderline(bool(style.underline))
    return font


def apply_label_style(label: QLabel, style: TextStyle, zoom: int = 100, color_override: str = "") -> None:
    label.setFont(qfont_from_style(style, zoom))
    color = color_override or style.color
    if color:
        label.setStyleSheet(f"color: {color}; background: transparent;")
    else:
        label.setStyleSheet("background: transparent;")


def apply_textedit_style(
    widget: QTextEdit,
    style: TextStyle,
    appearance: Appearance,
    zoom: int = 100,
    color_override: str = "",
) -> None:
    widget.setFont(qfont_from_style(style, zoom))
    color = color_override or style.color
    widget.setStyleSheet(
        "QTextEdit { background: transparent; border: none; padding: 0; "
        + (f"color: {color}; " if color else "")
        + f" line-height: {int(appearance.line_spacing * 100)}%; }}"
    )
    opt = widget.document().defaultTextOption()
    opt.setWrapMode(QTextOption.WrapMode.WrapAtWordBoundaryOrAnywhere)
    widget.document().setDefaultTextOption(opt)
    widget.document().setDefaultFont(qfont_from_style(style, zoom))
    widget.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
    widget.document().setDocumentMargin(2)


def contrast_warning(hex_color: str, theme: str) -> bool:
    if not hex_color:
        return False
    c = QColor(hex_color)
    if not c.isValid():
        return False
    luma = (0.299 * c.red() + 0.587 * c.green() + 0.114 * c.blue()) / 255.0
    if theme == "light":
        return luma > 0.82
    return luma < 0.22
