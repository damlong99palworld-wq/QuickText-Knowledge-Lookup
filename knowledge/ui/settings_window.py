from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeyEvent, QKeySequence
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from knowledge.services.hotkey_spec import parse_hotkey
from knowledge.models.settings import POPUP_CENTER, POPUP_NEAR_MOUSE, AppSettings
from knowledge.ui.appearance_page import AppearancePage


class HotkeyEdit(QLineEdit):
    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        self.setPlaceholderText("Press keys or type Ctrl+F2")

    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802
        key = event.key()
        if key in (Qt.Key_Control, Qt.Key_Shift, Qt.Key_Alt, Qt.Key_Meta, Qt.Key_unknown):
            return
        seq = QKeySequence(event.modifiers() | key)
        text = seq.toString(QKeySequence.PortableText)
        if text:
            self.setText(text.replace(" ", ""))
            return
        super().keyPressEvent(event)


class SettingsWindow(QDialog):
    def __init__(self, settings: AppSettings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.resize(880, 560)
        self._settings = settings

        root = QVBoxLayout(self)
        tabs = QTabWidget()
        general = QWidget()
        general_layout = QVBoxLayout(general)
        form = QFormLayout()

        self.hotkey_edit = HotkeyEdit(settings.hotkey)
        hint = QLabel("Examples: Ctrl+F2, Ctrl+Shift+F2, Alt+F2, Ctrl+Alt+K")
        hint.setObjectName("Muted")
        hotkey_row = QVBoxLayout()
        hotkey_row.addWidget(self.hotkey_edit)
        hotkey_row.addWidget(hint)
        form.addRow("Global Lookup Hotkey", hotkey_row)

        self.capture_cb = QCheckBox("Capture selected text when opened")
        self.capture_cb.setChecked(settings.capture_selected_text)
        self.restore_cb = QCheckBox("Restore clipboard after capture")
        self.restore_cb.setChecked(settings.restore_clipboard)
        self.focus_cb = QCheckBox("Focus search when no selected text")
        self.focus_cb.setChecked(settings.focus_search_when_empty)
        self.tray_cb = QCheckBox("Minimize to tray when closed")
        self.tray_cb.setChecked(settings.minimize_to_tray)
        self.start_cb = QCheckBox("Start minimized to tray")
        self.start_cb.setChecked(settings.start_minimized)

        for box in (self.capture_cb, self.restore_cb, self.focus_cb, self.tray_cb, self.start_cb):
            form.addRow("", box)

        self.near_radio = QRadioButton("Near mouse cursor")
        self.center_radio = QRadioButton("Screen center")
        if settings.popup_position == POPUP_CENTER:
            self.center_radio.setChecked(True)
        else:
            self.near_radio.setChecked(True)
        group = QButtonGroup(self)
        group.addButton(self.near_radio)
        group.addButton(self.center_radio)
        pos_row = QHBoxLayout()
        pos_row.addWidget(self.near_radio)
        pos_row.addWidget(self.center_radio)
        pos_row.addStretch(1)
        form.addRow("Popup position", pos_row)

        general_layout.addLayout(form)
        general_layout.addStretch(1)
        self.appearance_page = AppearancePage(settings.appearance, list(settings.saved_colors or []), self)
        tabs.addTab(general, "General")
        tabs.addTab(self.appearance_page, "Appearance")
        root.addWidget(tabs)
        buttons = QDialogButtonBox(QDialogButtonBox.Cancel | QDialogButtonBox.Save)
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    def _save(self) -> None:
        raw = self.hotkey_edit.text().strip()
        try:
            parsed = parse_hotkey(raw)
        except ValueError as exc:
            QMessageBox.warning(self, "Hotkey", str(exc))
            self.hotkey_edit.setFocus()
            return
        self.hotkey_edit.setText(parsed.display)
        self.accept()

    def result_settings(self) -> AppSettings:
        return AppSettings(
            hotkey=self.hotkey_edit.text().strip(),
            capture_selected_text=self.capture_cb.isChecked(),
            restore_clipboard=self.restore_cb.isChecked(),
            focus_search_when_empty=self.focus_cb.isChecked(),
            popup_position=POPUP_CENTER if self.center_radio.isChecked() else POPUP_NEAR_MOUSE,
            minimize_to_tray=self.tray_cb.isChecked(),
            start_minimized=self.start_cb.isChecked(),
            capture_delay_ms=self._settings.capture_delay_ms,
            saved_colors=list(self.appearance_page.saved_colors or self._settings.saved_colors or []),
            appearance=self.appearance_page.result_appearance(),
        )
