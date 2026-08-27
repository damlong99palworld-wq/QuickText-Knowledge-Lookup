from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
)

from models.snippet import AppData, Snippet, format_hotkey_display, _norm_hotkey


class SnippetEditor(QDialog):
    def __init__(self, data: AppData, snippet: Snippet | None = None, parent=None) -> None:
        super().__init__(parent)
        self.data = data
        self.snippet = snippet
        self.setWindowTitle("Edit Snippet" if snippet else "Add Snippet")
        self.resize(560, 520)
        self.setMinimumSize(420, 360)
        # Allow maximize / minimize / resize
        self.setWindowFlags(
            self.windowFlags()
            | Qt.WindowType.WindowMinimizeButtonHint
            | Qt.WindowType.WindowMaximizeButtonHint
            | Qt.WindowType.WindowSystemMenuHint
        )
        self.setSizeGripEnabled(True)

        self.name = QLineEdit(snippet.name if snippet else "")
        self.text = QPlainTextEdit(snippet.text if snippet else "")
        self.text.setMinimumHeight(160)
        self.text.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.text.setPlaceholderText("Snippet text…")

        self.category = QComboBox()
        self.category.setEditable(True)
        self.category.addItems(data.categories or ["General"])
        if snippet:
            self.category.setCurrentText(snippet.category)

        self.hotkey = QLineEdit(
            format_hotkey_display(snippet.hotkey) if snippet and snippet.hotkey else ""
        )
        self.hotkey.setPlaceholderText("Ctrl+Shift+1  (optional)")
        self.hotkey.editingFinished.connect(self._format_hotkey_field)

        self.action = QComboBox()
        self.action.addItems(["Default", "Paste", "Copy"])
        act = (snippet.action if snippet and snippet.action else "default").lower()
        self.action.setCurrentText(
            {"default": "Default", "paste": "Paste", "copy": "Copy"}.get(act, "Default")
        )

        self.favorite = QCheckBox("Favorite")
        self.favorite.setChecked(bool(snippet.favorite) if snippet else False)
        self.show_in_palette = QCheckBox("Show On Palette")
        self.show_in_palette.setChecked(
            bool(getattr(snippet, "show_in_palette", True)) if snippet else True
        )
        self.color_hex = (snippet.color if snippet else "") or ""
        self.color_btn = QPushButton("Color…")
        self.color_btn.clicked.connect(self._pick_color)
        self._update_color_btn()

        top = QFormLayout()
        top.addRow("Name", self.name)

        mid = QVBoxLayout()
        mid.addWidget(QLabel("Text"))
        mid.addWidget(self.text, 1)

        bottom = QFormLayout()
        bottom.addRow("Category", self.category)
        bottom.addRow("Hotkey", self.hotkey)
        bottom.addRow("On Select", self.action)
        bottom.addRow("", self.favorite)
        bottom.addRow("", self.show_in_palette)
        bottom.addRow("Color", self.color_btn)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(top)
        layout.addLayout(mid, 1)  # Text grows when window is resized
        layout.addLayout(bottom)
        layout.addWidget(QLabel("Hotkey conflict is checked on Save."))
        layout.addWidget(buttons)
        self.result_values: dict | None = None

    def _format_hotkey_field(self) -> None:
        text = self.hotkey.text().strip()
        if text:
            self.hotkey.setText(format_hotkey_display(text))

    def _update_color_btn(self) -> None:
        if self.color_hex:
            self.color_btn.setText(f"Color: {self.color_hex}")
            self.color_btn.setStyleSheet(f"color: {self.color_hex};")
        else:
            self.color_btn.setText("Color… (Default)")
            self.color_btn.setStyleSheet("")

    def _pick_color(self) -> None:
        from ui.color_picker import ColorPickerDialog

        saved = list(getattr(self.data.settings, "saved_colors", None) or [])
        dlg = ColorPickerDialog(self.color_hex, saved, self)
        if dlg.exec():
            self.color_hex = dlg.result_color
            self.data.settings.saved_colors = dlg.saved_colors()
            self._update_color_btn()

    def _save(self) -> None:
        name = self.name.text().strip()
        text = self.text.toPlainText()
        if not name:
            QMessageBox.warning(self, "Quick Text", "Name is required.")
            return
        if not text.strip():
            QMessageBox.warning(self, "Quick Text", "Text is required.")
            return
        hotkey = _norm_hotkey(self.hotkey.text().strip())
        conflict = self.data.hotkey_conflict(hotkey, self.snippet.id if self.snippet else None)
        if conflict:
            QMessageBox.warning(
                self, "Hotkey in use", f'This hotkey is already assigned to:\n"{conflict}"'
            )
            return
        self.result_values = {
            "name": name,
            "text": text,
            "category": self.category.currentText().strip() or "General",
            "hotkey": hotkey,
            "favorite": self.favorite.isChecked(),
            "action": self.action.currentText().strip().lower(),
            "show_in_palette": self.show_in_palette.isChecked(),
            "color": self.color_hex,
        }
        self.accept()
