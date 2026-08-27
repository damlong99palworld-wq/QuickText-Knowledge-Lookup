from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QCursor, QGuiApplication, QPainter, QPen
from PySide6.QtWidgets import (
    QColorDialog,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


def parse_color(value: str) -> QColor:
    if not value:
        return QColor()
    c = QColor(value)
    return c if c.isValid() else QColor()


class ColorPickerDialog(QDialog):
    """Custom color dialog: mixer + custom swatches + screen eyedropper."""

    def __init__(self, initial: str = "", saved_colors: list[str] | None = None, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Snippet name color")
        self.resize(420, 120)
        self._saved = list(saved_colors or [])
        self.result_color = initial or ""
        self._picking = False

        self.preview = QLabel()
        self.preview.setFixedSize(48, 48)
        self.preview.setFrameStyle(QLabel.Shape.Box)
        self.hex_label = QLabel(initial or "(Default)")
        self._set_preview(initial)
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
        self.result_color = hex_color or ""
        if not hasattr(self, "preview") or not hasattr(self, "hex_label"):
            return
        if hex_color:
            self.preview.setStyleSheet(f"background:{hex_color}; border:1px solid #555;")
            self.hex_label.setText(hex_color)
        else:
            self.preview.setStyleSheet("background:#1e2229; border:1px solid #555;")
            self.hex_label.setText("(Default)")

    def _rebuild_swatches(self) -> None:
        while self.swatch_row.count():
            item = self.swatch_row.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        for c in self._saved[:16]:
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
        for i, c in enumerate(self._saved[:16]):
            QColorDialog.setCustomColor(i, parse_color(c).rgb())
        if self.result_color:
            dlg.setCurrentColor(parse_color(self.result_color))
        if dlg.exec():
            col = dlg.currentColor()
            if col.isValid():
                self._set_preview(col.name())

    def _save_swatch(self) -> None:
        if not self.result_color:
            QMessageBox.information(self, "Quick Text", "No color to save.")
            return
        if self.result_color not in self._saved:
            self._saved.insert(0, self.result_color)
            self._saved = self._saved[:16]
            self._rebuild_swatches()

    def _clear(self) -> None:
        self._set_preview("")

    def _start_eyedropper(self) -> None:
        QMessageBox.information(
            self,
            "Kim lấy màu",
            "Sau khi bấm OK, di chuyển chuột tới điểm cần lấy màu và bấm chuột trái trong ~5 giây.",
        )
        self.hide()
        self._picking = True
        QTimer.singleShot(300, self._arm_pick)

    def _arm_pick(self) -> None:
        # Poll cursor position on next left-ish delay: grab pixel under cursor after short wait
        # User clicks anywhere — we sample once after 0.8s at current cursor (simple UX)
        QTimer.singleShot(800, self._sample_cursor)

    def _sample_cursor(self) -> None:
        try:
            pos = QCursor.pos()
            screen = QGuiApplication.screenAt(pos) or QGuiApplication.primaryScreen()
            if not screen:
                return
            # Grab 1x1 at global coords relative to screen
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
