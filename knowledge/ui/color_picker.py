from __future__ import annotations

from PySide6.QtCore import QTimer
from PySide6.QtGui import QColor, QCursor, QGuiApplication
from PySide6.QtWidgets import (
    QColorDialog,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from knowledge.shared.color_system import MAX_SAVED_COLORS, normalize_hex, normalize_saved_colors, push_saved_color


def parse_color(value: str) -> QColor:
    hex_color = normalize_hex(value)
    if not hex_color:
        return QColor()
    c = QColor(hex_color)
    return c if c.isValid() else QColor()


class ColorPickerDialog(QDialog):
    """Same UX as QuickText: mixer, preview, HEX, saved swatches, eyedropper, clear."""

    def __init__(self, initial: str = "", saved_colors: list[str] | None = None, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Entry name color")
        self.resize(420, 120)
        self._saved = normalize_saved_colors(saved_colors)
        self.result_color = normalize_hex(initial)
        self._picking = False

        self.preview = QLabel()
        self.preview.setFixedSize(48, 48)
        self.preview.setFrameStyle(QLabel.Shape.Box)
        self.hex_label = QLabel(self.result_color or "(Default)")
        self._set_preview(self.result_color)
        btn_mix = QPushButton("Color mixer…")
        btn_mix.clicked.connect(self._open_mixer)
        btn_pick = QPushButton("Eyedropper (screen)")
        btn_pick.clicked.connect(self._start_eyedropper)
        btn_save = QPushButton("Save swatch")
        btn_save.clicked.connect(self._save_swatch)
        btn_clear = QPushButton("Clear (Default)")
        btn_clear.clicked.connect(self._clear)

        self.swatch_row = QHBoxLayout()
        self._rebuild_swatches()

        top = QHBoxLayout()
        top.addWidget(self.preview)
        top.addWidget(self.hex_label, 1)

        row = QHBoxLayout()
        row.addWidget(btn_mix)
        row.addWidget(btn_pick)
        row.addWidget(btn_save)
        row.addWidget(btn_clear)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(top)
        layout.addLayout(row)
        layout.addWidget(QLabel("Saved swatches (click to use):"))
        layout.addLayout(self.swatch_row)
        layout.addWidget(buttons)

    def _set_preview(self, hex_color: str) -> None:
        self.result_color = normalize_hex(hex_color)
        if not hasattr(self, "preview") or not hasattr(self, "hex_label"):
            return
        if self.result_color:
            self.preview.setStyleSheet(f"background:{self.result_color}; border:1px solid #555;")
            self.hex_label.setText(self.result_color)
        else:
            self.preview.setStyleSheet("background:#1e2229; border:1px solid #555;")
            self.hex_label.setText("(Default)")

    def _rebuild_swatches(self) -> None:
        while self.swatch_row.count():
            item = self.swatch_row.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        for c in self._saved[:MAX_SAVED_COLORS]:
            b = QPushButton()
            b.setFixedSize(28, 28)
            b.setStyleSheet(f"background:{c}; border:1px solid #888;")
            b.setToolTip(c)
            b.clicked.connect(lambda _=False, col=c: self._set_preview(col))
            self.swatch_row.addWidget(b)
        self.swatch_row.addStretch()

    def _open_mixer(self) -> None:
        dlg = QColorDialog(self)
        dlg.setOption(QColorDialog.ColorDialogOption.ShowAlphaChannel, False)
        for i, c in enumerate(self._saved[:MAX_SAVED_COLORS]):
            QColorDialog.setCustomColor(i, parse_color(c).rgb())
        if self.result_color:
            dlg.setCurrentColor(parse_color(self.result_color))
        if dlg.exec():
            col = dlg.currentColor()
            if col.isValid():
                self._set_preview(col.name())

    def _save_swatch(self) -> None:
        if not self.result_color:
            QMessageBox.information(self, "Knowledge Lookup", "No color to save.")
            return
        self._saved = push_saved_color(self._saved, self.result_color)
        self._rebuild_swatches()

    def _clear(self) -> None:
        self._set_preview("")

    def _start_eyedropper(self) -> None:
        QMessageBox.information(
            self,
            "Eyedropper",
            "After OK, move the mouse to the pixel you want and wait ~1 second.",
        )
        self.hide()
        self._picking = True
        QTimer.singleShot(300, self._arm_pick)

    def _arm_pick(self) -> None:
        QTimer.singleShot(800, self._sample_cursor)

    def _sample_cursor(self) -> None:
        try:
            pos = QCursor.pos()
            screen = QGuiApplication.screenAt(pos) or QGuiApplication.primaryScreen()
            if not screen:
                return
            geo = screen.geometry()
            x = pos.x() - geo.x()
            y = pos.y() - geo.y()
            pix = screen.grabWindow(0, x, y, 1, 1)
            img = pix.toImage()
            if not img.isNull():
                qc = QColor(img.pixel(0, 0))
                self._set_preview(qc.name())
        finally:
            self._picking = False
            self.show()
            self.raise_()

    def saved_colors(self) -> list[str]:
        return list(self._saved)
