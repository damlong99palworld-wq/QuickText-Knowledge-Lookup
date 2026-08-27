from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from knowledge.models.knowledge import KnowledgeEntry
from knowledge.shared.appearance import WIDTH_PX, Appearance
from knowledge.shared.ui_helpers import apply_label_style, apply_textedit_style


class KnowledgeView(QWidget):
    create_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.entry: KnowledgeEntry | None = None
        self._unmatched_query = ""
        self.appearance = Appearance()
        self.zoom = 100

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(8)

        header = QHBoxLayout()
        titles = QVBoxLayout()
        self.name_label = QLabel("No entry selected")
        self.name_label.setObjectName("ViewName")
        self.name_label.setWordWrap(True)
        self.meta_label = QLabel("")
        self.meta_label.setObjectName("ViewCategory")
        self.meta_label.setWordWrap(True)
        titles.addWidget(self.name_label)
        titles.addWidget(self.meta_label)
        header.addLayout(titles, 1)

        self.copy_name_btn = QPushButton("Copy Name")
        self.copy_desc_btn = QPushButton("Copy Description")
        self.copy_all_btn = QPushButton("Copy All")
        self.edit_btn = QPushButton("Edit")
        self.edit_btn.setObjectName("PrimaryButton")
        for btn in (self.copy_name_btn, self.copy_desc_btn, self.copy_all_btn, self.edit_btn):
            btn.setCursor(Qt.PointingHandCursor)
            header.addWidget(btn, 0, Qt.AlignTop)
        root.addLayout(header)

        self.desc_label = QLabel("")
        self.desc_label.setWordWrap(True)
        self.desc_label.setObjectName("Muted")
        root.addWidget(self.desc_label)

        self.create_btn = QPushButton("+ Create Knowledge")
        self.create_btn.setObjectName("PrimaryButton")
        self.create_btn.setCursor(Qt.PointingHandCursor)
        self.create_btn.clicked.connect(self.create_requested.emit)
        self.create_btn.hide()
        root.addWidget(self.create_btn)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.body = QWidget()
        self.body_layout = QVBoxLayout(self.body)
        self.body_layout.setContentsMargins(0, 0, 0, 0)
        self.body_layout.setSpacing(10)
        self.body_layout.addStretch(1)
        self.scroll.setWidget(self.body)
        root.addWidget(self.scroll, 1)

        self.set_entry(None)

    def configure(self, appearance: Appearance, zoom: int = 100) -> None:
        self.appearance = appearance
        self.zoom = max(70, min(180, int(zoom)))
        if self._unmatched_query and self.entry is None:
            self.set_unmatched(self._unmatched_query)
        else:
            self.set_entry(self.entry)

    def set_entry(self, entry: KnowledgeEntry | None) -> None:
        self.entry = entry
        while self.body_layout.count() > 1:
            item = self.body_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        enabled = entry is not None
        for btn in (self.copy_name_btn, self.copy_desc_btn, self.copy_all_btn, self.edit_btn):
            btn.setEnabled(enabled)

        self.create_btn.hide()
        self._unmatched_query = ""
        if entry is None:
            self.name_label.setStyleSheet("")
            self.name_label.setText("No entry selected")
            self.meta_label.setText("Add a knowledge entry or pick one from the list.")
            self.desc_label.setText("")
            return

        app = self.appearance
        zoom = self.zoom
        name_style = app.entry_name
        apply_label_style(self.name_label, name_style, zoom, color_override=entry.color or "")
        self.name_label.setText(entry.name or "(unnamed)")
        bits = []
        if entry.category:
            bits.append(entry.category)
        if entry.aliases:
            bits.append("Aliases: " + ", ".join(entry.aliases))
        if entry.tags:
            bits.append("Tags: " + ", ".join(entry.tags))
        self.meta_label.setText("  ·  ".join(bits))
        apply_label_style(self.meta_label, app.category, zoom)
        self.desc_label.setText(entry.short_description)
        apply_label_style(self.desc_label, app.description, zoom)
        self.desc_label.setContentsMargins(0, 0, 0, app.paragraph_spacing)
        width = WIDTH_PX.get(app.reading_width, 720)
        self.scroll.setMaximumWidth(width if width else 16777215)

        for prop in entry.properties:
            block = QFrame()
            block.setObjectName("Card")
            layout = QVBoxLayout(block)
            layout.setContentsMargins(10, 8, 10, 10)
            layout.setSpacing(max(2, app.paragraph_spacing // 2))
            row = QHBoxLayout()
            title = QLabel(prop.name or "(property)")
            pname = app.property_name.overlay(prop.style)
            apply_label_style(title, pname, zoom, color_override=prop.style.color)
            copy_btn = QPushButton("Copy")
            copy_btn.setCursor(Qt.PointingHandCursor)
            copy_btn.clicked.connect(lambda _=False, text=prop.value: self._copy(text))
            row.addWidget(title, 1)
            row.addWidget(copy_btn, 0)
            layout.addLayout(row)
            value = QTextEdit()
            value.setReadOnly(True)
            value.setPlainText(prop.value)
            value.setMinimumHeight(70)
            value.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
            apply_textedit_style(value, app.property_value, app, zoom, color_override=prop.value_color)
            layout.addWidget(value)
            self.body_layout.insertWidget(self.body_layout.count() - 1, block)
            block.setMaximumWidth(width if width else 16777215)
            self.body_layout.setSpacing(app.property_spacing)

    def set_unmatched(self, query: str) -> None:
        self.entry = None
        self._unmatched_query = (query or "").strip()
        while self.body_layout.count() > 1:
            item = self.body_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        for btn in (self.copy_name_btn, self.copy_desc_btn, self.copy_all_btn, self.edit_btn):
            btn.setEnabled(False)
        self.name_label.setStyleSheet("")
        self.name_label.setText("No matching Knowledge Entry found.")
        self.meta_label.setText(f"Search: {self._unmatched_query}" if self._unmatched_query else "")
        self.desc_label.setText("Create a new entry from this text to grow your knowledge base.")
        self.create_btn.setVisible(bool(self._unmatched_query))

    def _copy(self, text: str) -> None:
        from PySide6.QtWidgets import QApplication

        QApplication.clipboard().setText(text or "")

    def copy_name(self) -> None:
        if self.entry:
            self._copy(self.entry.name)

    def copy_description(self) -> None:
        if self.entry:
            self._copy(self.entry.short_description)

    def copy_all(self) -> None:
        if not self.entry:
            return
        e = self.entry
        lines = [e.name, "", e.short_description]
        if e.aliases:
            lines += ["", "Aliases: " + ", ".join(e.aliases)]
        if e.category:
            lines += ["", "Category: " + e.category]
        if e.tags:
            lines += ["", "Tags: " + ", ".join(e.tags)]
        for prop in e.properties:
            lines += ["", prop.name, prop.value]
        self._copy("\n".join(lines).strip())
