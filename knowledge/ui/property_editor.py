from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from knowledge.models.property import KnowledgeProperty


class PropertyBlock(QFrame):
    moved_up = Signal(str)
    moved_down = Signal(str)
    deleted = Signal(str)
    changed = Signal()
    colors_changed = Signal(list)

    def __init__(self, prop: KnowledgeProperty, parent=None, saved_colors=None, theme: str = "dark"):
        super().__init__(parent)
        self.prop = prop
        self._saved_colors = list(saved_colors or [])
        self._theme = theme
        self.setObjectName("Card")
        self.setFrameShape(QFrame.StyledPanel)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        header = QHBoxLayout()
        self.name_edit = QLineEdit(prop.name)
        self.name_edit.setPlaceholderText("Property name")
        header.addWidget(self.name_edit, 1)

        self.style_btn = QPushButton("Style...")
        self.up_btn = QPushButton("Up")
        self.down_btn = QPushButton("Down")
        self.del_btn = QPushButton("Delete")
        self.del_btn.setObjectName("DangerButton")
        for btn in (self.style_btn, self.up_btn, self.down_btn, self.del_btn):
            btn.setCursor(Qt.PointingHandCursor)
        header.addWidget(self.style_btn)
        header.addWidget(self.up_btn)
        header.addWidget(self.down_btn)
        header.addWidget(self.del_btn)
        layout.addLayout(header)

        self.value_edit = QPlainTextEdit(prop.value)
        self.value_edit.setPlaceholderText("Property value (multiline)")
        self.value_edit.setMinimumHeight(80)
        self.value_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding)
        layout.addWidget(self.value_edit)

        self.name_edit.textChanged.connect(self._on_changed)
        self.value_edit.textChanged.connect(self._on_changed)
        self.style_btn.clicked.connect(self._edit_style)
        self.up_btn.clicked.connect(lambda: self.moved_up.emit(self.prop.id))
        self.down_btn.clicked.connect(lambda: self.moved_down.emit(self.prop.id))
        self.del_btn.clicked.connect(self._confirm_delete)

    def _on_changed(self) -> None:
        self.prop.name = self.name_edit.text().strip()
        self.prop.value = self.value_edit.toPlainText()
        self.changed.emit()

    def _confirm_delete(self) -> None:
        name = self.prop.name or "this property"
        result = QMessageBox.question(
            self,
            "Delete Property",
            f'Delete "{name}"?',
            QMessageBox.Cancel | QMessageBox.Yes,
            QMessageBox.Cancel,
        )
        if result == QMessageBox.Yes:
            self.deleted.emit(self.prop.id)

    def _edit_style(self) -> None:
        from knowledge.ui.property_style_dialog import PropertyStyleDialog

        dlg = PropertyStyleDialog(self.prop.style, self.prop.value_color, self._saved_colors, self._theme, self)
        if dlg.exec() != PropertyStyleDialog.Accepted:
            return
        style, value_color = dlg.result_style()
        self.prop.style = style
        self.prop.value_color = value_color
        self._saved_colors = dlg.saved_colors()
        self.colors_changed.emit(self._saved_colors)
        self.changed.emit()

    def collect(self) -> KnowledgeProperty:
        self.prop.name = self.name_edit.text().strip()
        self.prop.value = self.value_edit.toPlainText()
        return self.prop
