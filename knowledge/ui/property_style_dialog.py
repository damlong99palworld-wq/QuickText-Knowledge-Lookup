from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFontComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from knowledge.shared.appearance import TextStyle
from knowledge.shared.color_system import normalize_hex
from knowledge.ui.color_picker import ColorPickerDialog
from knowledge.shared.ui_helpers import contrast_warning


class PropertyStyleDialog(QDialog):
    def __init__(
        self,
        style: TextStyle,
        value_color: str = "",
        saved_colors: list[str] | None = None,
        theme: str = "dark",
        parent=None,
    ):
        super().__init__(parent)
        self.setWindowTitle("Property Style")
        self.resize(420, 360)
        self._saved = list(saved_colors or [])
        self._theme = theme
        self.name_color = normalize_hex(style.color)
        self.value_color = normalize_hex(value_color)

        self.use_default = QCheckBox("Use Default Style")
        self.use_default.setChecked(style.is_empty_override() and not self.value_color)

        self.font_box = QFontComboBox()
        if style.font_family:
            self.font_box.setCurrentFont(self.font_box.currentFont())
            self.font_box.setCurrentText(style.font_family)
        self.size_box = QSpinBox()
        self.size_box.setRange(8, 40)
        self.size_box.setValue(style.font_size or 12)
        self.bold = QCheckBox("Bold")
        self.bold.setChecked(bool(style.bold))
        self.italic = QCheckBox("Italic")
        self.italic.setChecked(bool(style.italic))
        self.underline = QCheckBox("Underline")
        self.underline.setChecked(bool(style.underline))

        self.name_color_btn = QPushButton()
        self.value_color_btn = QPushButton()
        self._refresh_color_buttons()
        self.name_color_btn.clicked.connect(lambda: self._pick("name"))
        self.value_color_btn.clicked.connect(lambda: self._pick("value"))

        form = QFormLayout()
        form.addRow(self.use_default)
        form.addRow("Font", self.font_box)
        form.addRow("Size", self.size_box)
        flags = QHBoxLayout()
        flags.addWidget(self.bold)
        flags.addWidget(self.italic)
        flags.addWidget(self.underline)
        form.addRow("Flags", flags)
        form.addRow("Name Color", self.name_color_btn)
        form.addRow("Value Color", self.value_color_btn)

        hint = QLabel("Empty/default means this property follows Settings → Appearance.")
        hint.setObjectName("Muted")
        hint.setWordWrap(True)

        buttons = QDialogButtonBox(QDialogButtonBox.Reset | QDialogButtonBox.Cancel | QDialogButtonBox.Save)
        buttons.button(QDialogButtonBox.Reset).setText("Reset Style to Default")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        buttons.button(QDialogButtonBox.Reset).clicked.connect(self._reset)

        root = QVBoxLayout(self)
        root.addLayout(form)
        root.addWidget(hint)
        root.addWidget(buttons)
        self.use_default.toggled.connect(self._toggle_default)
        self._toggle_default(self.use_default.isChecked())

    def _toggle_default(self, on: bool) -> None:
        for w in (
            self.font_box,
            self.size_box,
            self.bold,
            self.italic,
            self.underline,
            self.name_color_btn,
            self.value_color_btn,
        ):
            w.setEnabled(not on)

    def _refresh_color_buttons(self) -> None:
        self.name_color_btn.setText(self.name_color or "Default")
        self.name_color_btn.setStyleSheet(f"color: {self.name_color};" if self.name_color else "")
        self.value_color_btn.setText(self.value_color or "Default")
        self.value_color_btn.setStyleSheet(f"color: {self.value_color};" if self.value_color else "")

    def _pick(self, which: str) -> None:
        current = self.name_color if which == "name" else self.value_color
        dlg = ColorPickerDialog(current, self._saved, self)
        if dlg.exec() != ColorPickerDialog.Accepted:
            return
        self._saved = dlg.saved_colors()
        color = dlg.result_color
        if color and contrast_warning(color, self._theme):
            QMessageBox.information(self, "Contrast", "Low contrast color for the current theme.")
        if which == "name":
            self.name_color = color
        else:
            self.value_color = color
        self._refresh_color_buttons()

    def _reset(self) -> None:
        self.use_default.setChecked(True)
        self.name_color = ""
        self.value_color = ""
        self._refresh_color_buttons()

    def saved_colors(self) -> list[str]:
        return list(self._saved)

    def result_style(self) -> tuple[TextStyle, str]:
        if self.use_default.isChecked():
            return TextStyle(), ""
        return (
            TextStyle(
                font_family=self.font_box.currentFont().family(),
                font_size=self.size_box.value(),
                bold=self.bold.isChecked(),
                italic=self.italic.isChecked(),
                underline=self.underline.isChecked(),
                color=self.name_color,
            ),
            self.value_color,
        )
