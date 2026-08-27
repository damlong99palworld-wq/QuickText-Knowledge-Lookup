from __future__ import annotations

from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QRadioButton,
    QSpinBox,
    QVBoxLayout,
)

from models.snippet import AppData, Settings, format_hotkey_display, _norm_hotkey


class SettingsWindow(QDialog):
    def __init__(self, data: AppData, parent=None) -> None:
        super().__init__(parent)
        self.data = data
        self.setWindowTitle("Settings")
        self.resize(420, 440)

        s = data.settings
        self.hotkey = QLineEdit(format_hotkey_display(s.open_menu_hotkey))
        self.hotkey.editingFinished.connect(self._format_hotkey_field)
        self.restore = QCheckBox("Restore Clipboard After Paste")
        self.restore.setChecked(s.restore_clipboard)
        self.minimized = QCheckBox("Start In Tray (Don't Open Manager)")
        self.minimized.setChecked(s.start_minimized)
        self.tray = QCheckBox("Show System Tray Icon")
        self.tray.setChecked(s.show_tray)
        self.autostart = QCheckBox("Start With Windows")
        self.autostart.setChecked(s.start_with_windows)
        self.close_after = QCheckBox("Close Popup After Selecting")
        self.close_after.setChecked(s.close_after_select)
        self.pos_mouse = QRadioButton("Mouse Cursor")
        self.pos_center = QRadioButton("Screen Center")
        if s.popup_position == "center":
            self.pos_center.setChecked(True)
        else:
            self.pos_mouse.setChecked(True)
        self.recent = QSpinBox()
        self.recent.setRange(5, 10)
        self.recent.setValue(int(s.recent_limit or 8))
        self.ins_paste = QRadioButton("Paste Immediately")
        self.ins_copy = QRadioButton("Copy Only")
        if s.insert_mode == "copy":
            self.ins_copy.setChecked(True)
        else:
            self.ins_paste.setChecked(True)
        pos_g = QButtonGroup(self)
        pos_g.addButton(self.pos_mouse)
        pos_g.addButton(self.pos_center)
        ins_g = QButtonGroup(self)
        ins_g.addButton(self.ins_paste)
        ins_g.addButton(self.ins_copy)

        form = QFormLayout()
        hint = QLabel(
            "No selected text: open QuickText Palette.\n"
            "Selected text: open Knowledge Lookup."
        )
        hint.setWordWrap(True)
        form.addRow("Open Menu Hotkey", self.hotkey)
        form.addRow(hint)
        form.addRow(self.restore)
        form.addRow(self.minimized)
        form.addRow(self.tray)
        form.addRow(self.autostart)
        form.addRow(self.close_after)
        form.addRow(QLabel("Popup Position"))
        form.addRow(self.pos_mouse)
        form.addRow(self.pos_center)
        form.addRow(QLabel("On Select"))
        form.addRow(self.ins_paste)
        form.addRow(self.ins_copy)
        form.addRow("Max Recent Items", self.recent)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(QLabel("Paste method: clipboard + Ctrl+V (Unicode)"))
        layout.addWidget(buttons)

    def _format_hotkey_field(self) -> None:
        text = self.hotkey.text().strip()
        if text:
            self.hotkey.setText(format_hotkey_display(text))

    def _save(self) -> None:
        hotkey = _norm_hotkey(self.hotkey.text().strip() or "ctrl+f1")
        conflict = self.data.hotkey_conflict(hotkey)
        if conflict and conflict.startswith("Open Menu"):
            old = self.data.settings.open_menu_hotkey
            self.data.settings.open_menu_hotkey = ""
            conflict = self.data.hotkey_conflict(hotkey)
            self.data.settings.open_menu_hotkey = old
        if conflict:
            QMessageBox.warning(self, "Hotkey in use", f'This hotkey is already assigned to:\n"{conflict}"')
            return
        self.data.settings = Settings(
            open_menu_hotkey=hotkey,
            restore_clipboard=self.restore.isChecked(),
            start_minimized=self.minimized.isChecked(),
            show_tray=self.tray.isChecked(),
            start_with_windows=self.autostart.isChecked(),
            popup_position="center" if self.pos_center.isChecked() else "mouse",
            close_after_select=self.close_after.isChecked(),
            insert_mode="copy" if self.ins_copy.isChecked() else "paste",
            recent_limit=int(self.recent.value()),
            saved_colors=list(self.data.settings.saved_colors or []),
        )
        self.accept()
