from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from knowledge.models.knowledge import KnowledgeEntry
from knowledge.models.property import KnowledgeProperty, new_property_id
from knowledge.ui.property_editor import PropertyBlock


SUGGESTED_PROPERTIES = [
    "Where to Find",
    "When to Use",
    "Example",
    "Related Concepts",
    "Common Mistakes",
    "Performance Notes",
    "Project Notes",
    "Links",
    "ACF J Usage",
    "Blueprint Path",
    "Important Nodes",
]


def _csv_to_list(text: str) -> list[str]:
    parts = [p.strip() for p in text.replace(";", ",").split(",")]
    return [p for p in parts if p]


class KnowledgeEditor(QDialog):
    def __init__(
        self,
        entry: KnowledgeEntry | None = None,
        parent=None,
        initial_name: str = "",
        saved_colors: list[str] | None = None,
        theme: str = "dark",
    ):
        super().__init__(parent)
        self.setWindowTitle("Knowledge Editor")
        self.resize(720, 760)
        self._saved_colors = list(saved_colors or [])
        self._theme = theme
        if entry is None:
            self.working = KnowledgeEntry(name=(initial_name or "").strip())
        else:
            self.working = KnowledgeEntry.from_dict(entry.to_dict())

        root = QVBoxLayout(self)
        form = QFormLayout()
        self.name_edit = QLineEdit(self.working.name)
        self.aliases_edit = QLineEdit(", ".join(self.working.aliases))
        self.category_edit = QLineEdit(self.working.category)
        self.tags_edit = QLineEdit(", ".join(self.working.tags))
        self.desc_edit = QPlainTextEdit(self.working.short_description)
        self.desc_edit.setMinimumHeight(80)
        self.name_edit.setPlaceholderText("Niagara Component")
        self.aliases_edit.setPlaceholderText("NiagaraComponent, UNiagaraComponent")
        self.category_edit.setPlaceholderText("UE5 / VFX")
        self.tags_edit.setPlaceholderText("UE5, VFX, Niagara")
        self.desc_edit.setPlaceholderText("Short description")
        form.addRow("Name", self.name_edit)
        form.addRow("Aliases", self.aliases_edit)
        form.addRow("Category", self.category_edit)
        form.addRow("Tags", self.tags_edit)
        form.addRow("Short Description", self.desc_edit)
        self.color_btn = QPushButton("Color…")
        self.color_btn.setCursor(Qt.PointingHandCursor)
        self.color_btn.clicked.connect(self._pick_color)
        self._update_color_btn()
        form.addRow("Color", self.color_btn)
        root.addLayout(form)

        header = QHBoxLayout()
        header.addWidget(QLabel("Properties"))
        header.addStretch(1)
        self.add_prop_btn = QPushButton("+ Add Property")
        self.add_prop_btn.setObjectName("PrimaryButton")
        self.add_prop_btn.setCursor(Qt.PointingHandCursor)
        header.addWidget(self.add_prop_btn)
        root.addLayout(header)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.props_host = QWidget()
        self.props_layout = QVBoxLayout(self.props_host)
        self.props_layout.setContentsMargins(0, 0, 0, 0)
        self.props_layout.addStretch(1)
        self.scroll.setWidget(self.props_host)
        root.addWidget(self.scroll, 1)

        buttons = QDialogButtonBox(QDialogButtonBox.Cancel | QDialogButtonBox.Save)
        buttons.accepted.connect(self._on_save)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

        self.blocks: list[PropertyBlock] = []
        for prop in self.working.properties:
            self._add_block(prop)

        self.add_prop_btn.clicked.connect(self._show_add_menu)

    def _update_color_btn(self) -> None:
        hex_color = self.working.color or ""
        if hex_color:
            self.color_btn.setText(f"Color: {hex_color}")
            self.color_btn.setStyleSheet(f"color: {hex_color};")
        else:
            self.color_btn.setText("Color… (Default)")
            self.color_btn.setStyleSheet("")

    def _pick_color(self) -> None:
        from knowledge.ui.color_picker import ColorPickerDialog

        dlg = ColorPickerDialog(self.working.color or "", self._saved_colors, self)
        if dlg.exec() == ColorPickerDialog.Accepted:
            self.working.color = dlg.result_color
            self._saved_colors = dlg.saved_colors()
            self._update_color_btn()

    def saved_colors(self) -> list[str]:
        return list(self._saved_colors)

    def _on_colors(self, colors: list) -> None:
        self._saved_colors = list(colors or [])
        for block in self.blocks:
            block._saved_colors = self._saved_colors

    def _show_add_menu(self) -> None:
        menu = QMenu(self)
        existing = {b.prop.name for b in self.blocks}
        for name in SUGGESTED_PROPERTIES:
            action = menu.addAction(name)
            action.setEnabled(name not in existing)
            action.triggered.connect(lambda _=False, n=name: self._add_named(n))
        menu.addSeparator()
        custom = menu.addAction("Custom Property...")
        custom.triggered.connect(self._add_custom)
        menu.exec(self.add_prop_btn.mapToGlobal(self.add_prop_btn.rect().bottomLeft()))

    def _add_named(self, name: str) -> None:
        self._add_block(KnowledgeProperty(id=new_property_id(), name=name, value=""))

    def _add_custom(self) -> None:
        name, ok = QInputDialog.getText(self, "Custom Property", "Property Name:")
        if not ok:
            return
        name = name.strip()
        if not name:
            QMessageBox.warning(self, "Custom Property", "Property name cannot be empty.")
            return
        self._add_block(KnowledgeProperty(id=new_property_id(), name=name, value=""))

    def _add_block(self, prop: KnowledgeProperty) -> None:
        block = PropertyBlock(prop, self.props_host, self._saved_colors, self._theme)
        block.moved_up.connect(self._move_up)
        block.moved_down.connect(self._move_down)
        block.deleted.connect(self._delete_prop)
        block.colors_changed.connect(self._on_colors)
        self.props_layout.insertWidget(self.props_layout.count() - 1, block)
        self.blocks.append(block)

    def _index_of(self, prop_id: str) -> int:
        for i, block in enumerate(self.blocks):
            if block.prop.id == prop_id:
                return i
        return -1

    def _rebuild(self) -> None:
        for block in self.blocks:
            self.props_layout.removeWidget(block)
        for block in self.blocks:
            self.props_layout.insertWidget(self.props_layout.count() - 1, block)

    def _move_up(self, prop_id: str) -> None:
        idx = self._index_of(prop_id)
        if idx <= 0:
            return
        self.blocks[idx - 1], self.blocks[idx] = self.blocks[idx], self.blocks[idx - 1]
        self._rebuild()

    def _move_down(self, prop_id: str) -> None:
        idx = self._index_of(prop_id)
        if idx < 0 or idx >= len(self.blocks) - 1:
            return
        self.blocks[idx + 1], self.blocks[idx] = self.blocks[idx], self.blocks[idx + 1]
        self._rebuild()

    def _delete_prop(self, prop_id: str) -> None:
        idx = self._index_of(prop_id)
        if idx < 0:
            return
        block = self.blocks.pop(idx)
        self.props_layout.removeWidget(block)
        block.deleteLater()

    def _on_save(self) -> None:
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Save", "Name is required.")
            self.name_edit.setFocus()
            return
        self.accept()

    def result_entry(self) -> KnowledgeEntry:
        self.working.name = self.name_edit.text().strip()
        self.working.aliases = _csv_to_list(self.aliases_edit.text())
        self.working.category = self.category_edit.text().strip()
        self.working.tags = _csv_to_list(self.tags_edit.text())
        self.working.short_description = self.desc_edit.toPlainText().strip()
        self.working.properties = [block.collect() for block in self.blocks]
        return self.working
