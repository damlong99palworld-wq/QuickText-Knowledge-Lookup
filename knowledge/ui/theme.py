DARK_QSS = """
QMainWindow, QDialog, QWidget {
    background-color: #1B1E24;
    color: #E6E8EC;
    font-family: "Segoe UI", "Inter", "Noto Sans", sans-serif;
    font-size: 13px;
}
QLabel { color: #E6E8EC; background: transparent; }
QLabel#AppTitle {
    color: #F3F4F6;
    font-size: 16px;
    font-weight: 600;
}
QLabel#SectionTitle {
    color: #9AA3B2;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.6px;
}
QLabel#ViewName {
    color: #F8FAFC;
    font-size: 20px;
    font-weight: 600;
}
QLabel#ViewCategory {
    color: #8B93A7;
    font-size: 12px;
}
QLabel#PropName {
    color: #A8B3C7;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.4px;
}
QLabel#Muted { color: #8B93A7; }
QLineEdit, QPlainTextEdit, QTextEdit, QComboBox {
    background-color: #12151A;
    color: #E6E8EC;
    border: 1px solid #2E3440;
    border-radius: 4px;
    padding: 5px 8px;
    selection-background-color: #2B4C7E;
}
QLineEdit:focus, QPlainTextEdit:focus, QComboBox:focus {
    border: 1px solid #4C78B8;
}
QComboBox QAbstractItemView {
    background-color: #12151A;
    color: #E6E8EC;
    border: 1px solid #2E3440;
    selection-background-color: #2B4C7E;
}
QPushButton {
    background-color: #2A303A;
    color: #E6E8EC;
    border: 1px solid #3A4150;
    border-radius: 4px;
    padding: 5px 10px;
}
QPushButton:hover { background-color: #343B47; }
QPushButton:pressed { background-color: #232831; }
QPushButton:disabled { color: #6B7280; }
QPushButton#PrimaryButton {
    background-color: #3B6EA8;
    border: 1px solid #4C7FBA;
}
QPushButton#PrimaryButton:hover { background-color: #4780C0; }
QPushButton#DangerButton {
    background-color: #6B2E33;
    border: 1px solid #8A3B42;
}
QListWidget, QTreeWidget {
    background-color: #14171C;
    color: #E6E8EC;
    border: 1px solid #2E3440;
    border-radius: 4px;
    outline: none;
}
QListWidget::item { padding: 6px 8px; }
QListWidget::item:selected, QTreeWidget::item:selected {
    background-color: #2B4C7E;
    color: #FFFFFF;
}
QListWidget::item:hover, QTreeWidget::item:hover {
    background-color: #232831;
}
QSplitter::handle { background-color: #2E3440; }
QScrollArea { border: none; background: transparent; }
QFrame#Card {
    background-color: #14171C;
    border: 1px solid #2E3440;
    border-radius: 4px;
}
QMenu {
    background-color: #1B1E24;
    color: #E6E8EC;
    border: 1px solid #2E3440;
}
QMenu::item:selected { background-color: #2B4C7E; }
QStatusBar {
    background-color: #15181E;
    color: #8B93A7;
    border-top: 1px solid #2E3440;
}
QToolTip {
    background-color: #12151A;
    color: #E6E8EC;
    border: 1px solid #2E3440;
}
"""

LIGHT_QSS = """
QMainWindow, QDialog, QWidget {
    background-color: #F3F4F6;
    color: #1F2937;
    font-family: "Segoe UI", "Inter", "Noto Sans", sans-serif;
    font-size: 13px;
}
QLabel { color: #1F2937; background: transparent; }
QLabel#AppTitle { color: #111827; font-size: 16px; font-weight: 600; }
QLabel#SectionTitle { color: #6B7280; font-size: 11px; font-weight: 700; letter-spacing: 0.6px; }
QLabel#ViewName { color: #111827; font-size: 20px; font-weight: 600; }
QLabel#ViewCategory { color: #6B7280; font-size: 12px; }
QLabel#PropName { color: #4B5563; font-size: 11px; font-weight: 700; letter-spacing: 0.4px; }
QLabel#Muted { color: #6B7280; }
QLineEdit, QPlainTextEdit, QTextEdit, QComboBox {
    background-color: #FFFFFF;
    color: #1F2937;
    border: 1px solid #D1D5DB;
    border-radius: 4px;
    padding: 5px 8px;
    selection-background-color: #DBEAFE;
}
QComboBox QAbstractItemView {
    background-color: #FFFFFF;
    color: #1F2937;
    border: 1px solid #D1D5DB;
    selection-background-color: #DBEAFE;
}
QPushButton {
    background-color: #EEF0F3;
    color: #1F2937;
    border: 1px solid #D1D5DB;
    border-radius: 4px;
    padding: 5px 10px;
}
QPushButton:hover { background-color: #E5E7EB; }
QPushButton#PrimaryButton { background-color: #3B6EA8; color: #FFFFFF; border: 1px solid #4C7FBA; }
QPushButton#DangerButton { background-color: #B91C1C; color: #FFFFFF; border: 1px solid #991B1B; }
QListWidget, QTreeWidget {
    background-color: #FFFFFF;
    color: #1F2937;
    border: 1px solid #D1D5DB;
    border-radius: 4px;
    outline: none;
}
QListWidget::item:selected { background-color: #DBEAFE; color: #111827; }
QFrame#Card {
    background-color: #FFFFFF;
    border: 1px solid #D1D5DB;
    border-radius: 4px;
}
QMenu { background-color: #FFFFFF; color: #1F2937; border: 1px solid #D1D5DB; }
QMenu::item:selected { background-color: #DBEAFE; }
QStatusBar { background-color: #E5E7EB; color: #4B5563; border-top: 1px solid #D1D5DB; }
QTabWidget::pane { border: 1px solid #D1D5DB; }
QTabBar::tab { background: #E5E7EB; padding: 6px 12px; }
QTabBar::tab:selected { background: #FFFFFF; }
"""


def qss_for_theme(theme: str) -> str:
    if theme == "light":
        return LIGHT_QSS
    if theme == "system":
        try:
            from PySide6.QtGui import QGuiApplication
            from PySide6.QtCore import Qt

            hints = QGuiApplication.styleHints()
            scheme = hints.colorScheme()
            if scheme == Qt.ColorScheme.Light:
                return LIGHT_QSS
        except Exception:
            pass
    return DARK_QSS

