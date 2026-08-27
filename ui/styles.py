QSS = """
QWidget { background: #0b0c0e; color: #e8e6e1; font-size: 13px; }
QLineEdit, QPlainTextEdit, QComboBox, QSpinBox {
  background: #16181c; border: 1px solid #2a2d33; border-radius: 6px; padding: 6px 8px;
}
QListWidget, QTableWidget { background: #121418; border: 1px solid #2a2d33; border-radius: 6px; }
QListWidget::item:selected, QTableWidget::item:selected { background: #2a3140; }
QHeaderView::section {
  background: #1a1d22; color: #c8c4bc; padding: 6px; border: none;
  border-right: 1px solid #2a2d33; border-bottom: 1px solid #2a2d33;
}
QTableWidget {
  gridline-color: #2a2d33; alternate-background-color: #0f1114;
}
QPushButton {
  background: #1e2229; border: 1px solid #333842; border-radius: 6px; padding: 6px 12px;
}
QPushButton:hover { background: #2a3140; }
QMenu { background: #16181c; border: 1px solid #2a2d33; }
"""
