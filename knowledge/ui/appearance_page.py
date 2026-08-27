from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFontComboBox,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from knowledge.shared.appearance import (
    LINE_SPACING,
    PRESETS,
    STYLE_KEYS,
    THEMES,
    WIDTHS,
    Appearance,
    TextStyle,
    apply_preset,
)
from knowledge.ui.color_picker import ColorPickerDialog
from knowledge.shared.ui_helpers import apply_label_style, apply_textedit_style, contrast_warning


GROUP_LABELS = {
    "entry_name": "Entry Name",
    "description": "Short Description",
    "property_name": "Property Name",
    "property_value": "Property Value",
    "category": "Category",
    "tags": "Tags",
}


class AppearancePage(QWidget):
    changed = Signal()

    def __init__(self, appearance: Appearance, saved_colors: list[str], parent=None):
        super().__init__(parent)
        self.appearance = Appearance.from_dict(appearance.to_dict())
        self.saved_colors = list(saved_colors or [])
        self._loading = False

        root = QHBoxLayout(self)
        left = QVBoxLayout()
        right = QVBoxLayout()

        top = QHBoxLayout()
        top.addWidget(QLabel("Preset"))
        self.preset = QComboBox()
        for name in PRESETS:
            self.preset.addItem(name.title(), name)
        idx = max(0, self.preset.findData(self.appearance.preset if self.appearance.preset in PRESETS else "default"))
        self.preset.setCurrentIndex(idx)
        self.preset.currentIndexChanged.connect(self._apply_preset)
        top.addWidget(self.preset, 1)
        left.addLayout(top)

        theme_row = QHBoxLayout()
        theme_row.addWidget(QLabel("Theme"))
        self.theme = QComboBox()
        for name in THEMES:
            self.theme.addItem(name.title(), name)
        self.theme.setCurrentIndex(max(0, self.theme.findData(self.appearance.theme)))
        self.theme.currentIndexChanged.connect(self._on_change)
        theme_row.addWidget(self.theme, 1)
        left.addLayout(theme_row)

        self.group_box = QComboBox()
        for key in STYLE_KEYS:
            self.group_box.addItem(GROUP_LABELS[key], key)
        self.group_box.currentIndexChanged.connect(self._load_group)
        left.addWidget(self.group_box)

        form = QFormLayout()
        self.font_box = QFontComboBox()
        self.size_box = QSpinBox()
        self.size_box.setRange(8, 40)
        self.bold = QCheckBox("Bold")
        self.italic = QCheckBox("Italic")
        self.underline = QCheckBox("Underline")
        self.color_btn = QPushButton("Default")
        self.color_btn.clicked.connect(self._pick_color)
        flags = QHBoxLayout()
        flags.addWidget(self.bold)
        flags.addWidget(self.italic)
        flags.addWidget(self.underline)
        form.addRow("Font", self.font_box)
        form.addRow("Size", self.size_box)
        form.addRow("", flags)
        form.addRow("Color", self.color_btn)
        left.addLayout(form)

        space = QFormLayout()
        self.line_box = QComboBox()
        for val in LINE_SPACING:
            self.line_box.addItem(f"{val:.1f}", val)
        self.para_box = QSpinBox()
        self.para_box.setRange(0, 32)
        self.gap_box = QSpinBox()
        self.gap_box.setRange(0, 40)
        self.width_box = QComboBox()
        for w in WIDTHS:
            self.width_box.addItem(w.replace("_", " ").title(), w)
        space.addRow("Line spacing", self.line_box)
        space.addRow("Paragraph spacing", self.para_box)
        space.addRow("Property spacing", self.gap_box)
        space.addRow("Reading width", self.width_box)
        left.addLayout(space)
        left.addStretch(1)

        preview_box = QGroupBox("Preview")
        pv = QVBoxLayout(preview_box)
        self.preview_name = QLabel("Niagara Component")
        self.preview_meta = QLabel("UE5 / VFX   ·   Tags: UE5, Niagara")
        self.preview_desc = QLabel("Component used to attach and control a Niagara System on an Actor.")
        self.preview_desc.setWordWrap(True)
        self.preview_pname = QLabel("Where to Find")
        self.preview_pval = QTextEdit()
        self.preview_pval.setReadOnly(True)
        self.preview_pval.setPlainText("Blueprint → Add Component → Niagara")
        self.preview_pval.setFixedHeight(70)
        self.preview_p2 = QLabel("Performance Notes")
        self.preview_v2 = QTextEdit()
        self.preview_v2.setReadOnly(True)
        self.preview_v2.setPlainText("Do not keep too many Niagara Components active at once.")
        self.preview_v2.setFixedHeight(70)
        for w in (
            self.preview_name,
            self.preview_meta,
            self.preview_desc,
            self.preview_pname,
            self.preview_pval,
            self.preview_p2,
            self.preview_v2,
        ):
            pv.addWidget(w)
        right.addWidget(preview_box)

        root.addLayout(left, 1)
        root.addLayout(right, 1)

        for w in (self.font_box, self.size_box, self.bold, self.italic, self.underline, self.line_box, self.para_box, self.gap_box, self.width_box):
            if hasattr(w, "currentIndexChanged"):
                w.currentIndexChanged.connect(self._on_change)
            if hasattr(w, "valueChanged"):
                w.valueChanged.connect(self._on_change)
            if hasattr(w, "toggled"):
                w.toggled.connect(self._on_change)
            if hasattr(w, "currentFontChanged"):
                w.currentFontChanged.connect(lambda _f: self._on_change())

        self._sync_layout_controls()
        self._load_group()
        self._refresh_preview()

    def _current_key(self) -> str:
        return self.group_box.currentData() or "entry_name"

    def _current_style(self) -> TextStyle:
        return self.appearance.group(self._current_key())

    def _load_group(self) -> None:
        self._loading = True
        style = self._current_style()
        if style.font_family:
            self.font_box.setCurrentText(style.font_family)
        self.size_box.setValue(style.font_size or 13)
        self.bold.setChecked(bool(style.bold))
        self.italic.setChecked(bool(style.italic))
        self.underline.setChecked(bool(style.underline))
        self._refresh_color_btn()
        self._loading = False
        self._refresh_preview()

    def _sync_layout_controls(self) -> None:
        self._loading = True
        self.line_box.setCurrentIndex(max(0, self.line_box.findData(self.appearance.line_spacing)))
        self.para_box.setValue(self.appearance.paragraph_spacing)
        self.gap_box.setValue(self.appearance.property_spacing)
        self.width_box.setCurrentIndex(max(0, self.width_box.findData(self.appearance.reading_width)))
        self.theme.setCurrentIndex(max(0, self.theme.findData(self.appearance.theme)))
        self._loading = False

    def _refresh_color_btn(self) -> None:
        color = self._current_style().color
        self.color_btn.setText(color or "Default")
        self.color_btn.setStyleSheet(f"color: {color};" if color else "")

    def _pick_color(self) -> None:
        style = self._current_style()
        dlg = ColorPickerDialog(style.color, self.saved_colors, self)
        if dlg.exec() != ColorPickerDialog.Accepted:
            return
        self.saved_colors = dlg.saved_colors()
        style.color = dlg.result_color
        if style.color and contrast_warning(style.color, self.appearance.theme):
            QMessageBox.information(self, "Contrast", "Low contrast color for the current theme.")
        self._refresh_color_btn()
        self.appearance.preset = "custom"
        self._refresh_preview()
        self.changed.emit()

    def _apply_preset(self) -> None:
        if self._loading:
            return
        name = self.preset.currentData()
        theme = self.appearance.theme
        self.appearance = apply_preset(name)
        self.appearance.theme = theme
        self._sync_layout_controls()
        self._load_group()
        self.changed.emit()

    def _on_change(self) -> None:
        if self._loading:
            return
        key = self._current_key()
        style = TextStyle(
            font_family=self.font_box.currentFont().family(),
            font_size=self.size_box.value(),
            bold=self.bold.isChecked(),
            italic=self.italic.isChecked(),
            underline=self.underline.isChecked(),
            color=self.appearance.group(key).color,
        )
        setattr(self.appearance, key, style)
        self.appearance.line_spacing = float(self.line_box.currentData() or 1.2)
        self.appearance.paragraph_spacing = self.para_box.value()
        self.appearance.property_spacing = self.gap_box.value()
        self.appearance.reading_width = self.width_box.currentData() or "medium"
        self.appearance.theme = self.theme.currentData() or "dark"
        self.appearance.preset = "custom"
        self._refresh_preview()
        self.changed.emit()

    def _refresh_preview(self) -> None:
        a = self.appearance
        apply_label_style(self.preview_name, a.entry_name)
        apply_label_style(self.preview_meta, a.category)
        apply_label_style(self.preview_desc, a.description)
        apply_label_style(self.preview_pname, a.property_name)
        apply_label_style(self.preview_p2, a.property_name)
        apply_textedit_style(self.preview_pval, a.property_value, a)
        apply_textedit_style(self.preview_v2, a.property_value, a)
        self.preview_desc.setContentsMargins(0, 0, 0, a.paragraph_spacing)
        gap = a.property_spacing
        self.preview_p2.setContentsMargins(0, gap, 0, 0)

    def result_appearance(self) -> Appearance:
        return self.appearance
