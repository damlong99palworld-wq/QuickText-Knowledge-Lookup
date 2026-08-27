from __future__ import annotations

import sys
import time
import uuid
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QApplication, QMenu, QMessageBox, QSystemTrayIcon

from models.snippet import AppData, Snippet
from services.autostart import set_start_with_windows
from services.hotkeys import HotkeyBridge, HotkeyService
from services.paste_service import paste_text
from services.selection_capture import try_capture_selected_text
from services.paths import resource_path
from services.storage import load_data, save_data
from services.win_focus import get_foreground_hwnd
from knowledge.models.settings import AppSettings as KnowledgeSettings
from knowledge.services.storage import KnowledgeStore, default_data_dir, migrate_legacy_knowledge
from knowledge.ui.main_window import MainWindow as KnowledgeWindow
from ui.quick_menu import QuickMenu
from ui.settings_window import SettingsWindow
from ui.snippet_editor import SnippetEditor
from ui.snippet_manager import SnippetManager
from ui.styles import QSS

ROOT = resource_path()


def make_icon() -> QIcon:
    pix = QPixmap(64, 64)
    pix.fill(QColor("#0b0c0e"))
    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setPen(QPen(QColor("#d7d2c8"), 4))
    p.drawLine(14, 22, 34, 22)
    p.drawLine(14, 32, 50, 32)
    p.drawLine(14, 42, 40, 42)
    p.end()
    return QIcon(pix)


class QuickTextApp:
    def __init__(self) -> None:
        self.qt = QApplication.instance() or QApplication(sys.argv)
        self.qt.setQuitOnLastWindowClosed(False)
        self.qt.setApplicationName("Quick Text")
        self.qt.setStyleSheet(QSS)
        self.icon = make_icon()
        self.qt.setWindowIcon(self.icon)

        self.data: AppData = load_data(ROOT / "data" / "defaults.json")
        self._hwnd = 0
        self._hotkey_warned = False
        self._knowledge_win: KnowledgeWindow | None = None
        self._init_knowledge()

        self.bridge = HotkeyBridge()
        self.hotkeys = HotkeyService(self.bridge)
        self.bridge.open_menu.connect(self.open_menu)
        self.bridge.paste_snippet.connect(self.paste_id)

        self.menu = QuickMenu()
        self.menu.picked.connect(self.paste_id)
        self.menu.knowledge_requested.connect(self.paste_into_knowledge)

        self.manager = SnippetManager()
        self.manager.add_requested.connect(self.add_snippet)
        self.manager.edit_requested.connect(self.edit_id)
        self.manager.delete_requested.connect(self.delete_id)
        self.manager.duplicate_requested.connect(self.duplicate_id)
        self.manager.settings_requested.connect(self.open_settings)
        self.manager.export_requested.connect(self.export_library)
        self.manager.import_requested.connect(self.import_library)
        self.manager.save_profile_requested.connect(self.save_profile)
        self.manager.load_profile_requested.connect(self.load_profile)
        self.manager.knowledge_requested.connect(self.open_knowledge)
        self.manager.order_changed.connect(lambda: self.persist(rebind=False))
        self.manager.palette_visibility_changed.connect(lambda: self.persist(rebind=False))
        self.manager.color_changed.connect(lambda: self.persist(rebind=False))
        self.manager.favorite_changed.connect(lambda: self.persist(rebind=False))
        self.manager.category_color_changed.connect(lambda: self.persist(rebind=False))

        self.tray = QSystemTrayIcon(self.icon, self.qt)
        tray_menu = QMenu()
        tray_menu.addAction("Open Palette", self.open_menu)
        tray_menu.addAction("Open QuickText Manager", self.open_manager)
        tray_menu.addAction("Open Knowledge", self.open_knowledge)
        tray_menu.addAction("Add Text", self.add_snippet)
        tray_menu.addAction("Add Knowledge", self.add_knowledge)
        tray_menu.addAction("Settings", self.open_settings)
        tray_menu.addSeparator()
        tray_menu.addAction("Exit", self.quit)
        self.tray.setContextMenu(tray_menu)
        self.tray.setToolTip("Quick Text")
        self.tray.activated.connect(self._tray_activated)
        # Always show tray so the app is discoverable
        self.tray.show()
        try:
            self.tray.showMessage(
                "QuickText",
                "Dang chay o khay he thong.\nBam Ctrl+F1 de mo Palette.\nDouble-click icon de mo Manager.",
                QSystemTrayIcon.MessageIcon.Information,
                8000,
            )
        except Exception:
            pass

        err = self._rebind_hotkeys()
        if err:
            QMessageBox.warning(None, "Hotkey conflict", err)
        set_start_with_windows(self.data.settings.start_with_windows)

        # Always open Manager once so user sees the app (tray-only is easy to miss)
        self.open_manager()
        print("[QuickText] Running. Main hotkey: Ctrl+F1")
        print("[QuickText] No selection → Palette. Selected text → Knowledge Lookup.")

    def persist(self, rebind: bool = True) -> None:
        try:
            save_data(self.data)
        except OSError as exc:
            print(f"[QuickText] save failed: {exc}")
        if rebind:
            err = self._rebind_hotkeys()
            if err and not self._hotkey_warned:
                self._hotkey_warned = True
                QMessageBox.warning(None, "Hotkey conflict", err)
        self.manager.set_data(self.data)

    def _rebind_hotkeys(self) -> str | None:
        mapping = {s.hotkey: s.id for s in self.data.snippets if s.hotkey}
        err = self.hotkeys.bind(self.data.settings.open_menu_hotkey, mapping)
        if err:
            print(f"[QuickText] {err}")
        return err

    def _init_knowledge(self) -> None:
        kdir = default_data_dir()
        migrate_legacy_knowledge(kdir)
        sample = ROOT / "knowledge" / "sample" / "knowledge.sample.json"
        self.kstore = KnowledgeStore(kdir)
        self.kstore.load()
        if not self.kstore.entries and sample.exists():
            try:
                self.kstore.import_json(sample, merge=False)
                self.kstore.save()
            except (OSError, ValueError):
                pass
        ksettings = KnowledgeSettings.from_dict(self.kstore.settings)
        ksettings.saved_colors = list(self.data.settings.saved_colors or ksettings.saved_colors)
        self.ksettings = ksettings
        self._knowledge_win = KnowledgeWindow(self.kstore, ksettings, embedded=True)
        self._knowledge_win.settings_changed.connect(self._on_knowledge_settings)

    def _on_knowledge_settings(self, settings) -> None:
        self.ksettings = settings
        colors = list(getattr(settings, "saved_colors", None) or [])
        if colors:
            self.data.settings.saved_colors = colors
            self.persist(rebind=False)

    def open_knowledge(self, query: str = "") -> None:
        if self._knowledge_win is None:
            self._init_knowledge()
        win = self._knowledge_win
        assert win is not None
        win.settings.saved_colors = list(self.data.settings.saved_colors or [])
        win.reveal()
        if query:
            win.apply_external_query(query)
        else:
            win.search_box.setFocus()

    def add_knowledge(self) -> None:
        self.open_knowledge()
        if self._knowledge_win:
            self._knowledge_win.add_entry()

    def lookup_knowledge(self, text: str) -> None:
        self.open_knowledge(text)

    def paste_into_knowledge(self, typed: str = "") -> None:
        text = (typed or "").strip()
        if not text:
            try:
                from services import clipboard as winclip

                snap = winclip.save()
                text = (snap.unicode_text or "").strip()
            except Exception:
                text = ""
        self.open_knowledge()
        QTimer.singleShot(300, lambda t=text: self._paste_query(t))

    def _paste_query(self, query: str) -> None:
        win = self._knowledge_win
        if win is None:
            return
        win.apply_external_query(query or "")
        win.search_box.setFocus()
        win.raise_()

    def open_menu(self) -> None:
        self._hwnd = self.hotkeys.last_hwnd or get_foreground_hwnd()
        self.menu.popup(self.data)

    def open_manager(self) -> None:
        self.manager.set_data(self.data)
        self.manager.show()
        self.manager.raise_()
        self.manager.activateWindow()

    def open_settings(self) -> None:
        dlg = SettingsWindow(self.data)
        if dlg.exec():
            self._hotkey_warned = False
            self.persist()
            set_start_with_windows(self.data.settings.start_with_windows)
            if self.data.settings.show_tray:
                self.tray.show()
            else:
                self.tray.hide()

    def add_snippet(self) -> None:
        dlg = SnippetEditor(self.data)
        if dlg.exec() and dlg.result_values:
            now = time.time()
            vals = dlg.result_values
            if vals["category"] not in self.data.categories:
                self.data.categories.append(vals["category"])
            self.data.snippets.append(
                Snippet(
                    id="snip_" + uuid.uuid4().hex[:8],
                    name=vals["name"],
                    text=vals["text"],
                    category=vals["category"],
                    favorite=vals["favorite"],
                    hotkey=vals["hotkey"],
                    action=vals.get("action") or "default",
                    show_in_palette=bool(vals.get("show_in_palette", True)),
                    color=str(vals.get("color") or ""),
                    created_at=now,
                    updated_at=now,
                )
            )
            self.persist()

    def edit_id(self, sid: str) -> None:
        sn = self.data.snippet_by_id(sid)
        if not sn:
            return
        dlg = SnippetEditor(self.data, sn)
        if dlg.exec() and dlg.result_values:
            vals = dlg.result_values
            sn.name = vals["name"]
            sn.text = vals["text"]
            sn.category = vals["category"]
            sn.favorite = vals["favorite"]
            sn.hotkey = vals["hotkey"]
            sn.action = vals.get("action") or "default"
            sn.show_in_palette = bool(vals.get("show_in_palette", True))
            sn.color = str(vals.get("color") or "")
            sn.updated_at = time.time()
            if sn.category not in self.data.categories:
                self.data.categories.append(sn.category)
            self.persist()

    def export_library(self) -> None:
        import json

        from PySide6.QtWidgets import QFileDialog

        path, _ = QFileDialog.getSaveFileName(
            self.manager, "Export snippets", "quicktext-snippets.json", "JSON (*.json)"
        )
        if not path:
            return
        Path(path).write_text(json.dumps(self.data.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")

    def import_library(self) -> None:
        import json

        from PySide6.QtWidgets import QFileDialog

        from models.snippet import AppData as AD

        path, _ = QFileDialog.getOpenFileName(self.manager, "Import snippets", "", "JSON (*.json)")
        if not path:
            return
        try:
            raw = json.loads(Path(path).read_text(encoding="utf-8"))
            incoming = AD.from_dict(raw)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.warning(self.manager, "Import failed", str(exc))
            return
        ids = {s.id for s in self.data.snippets}
        for sn in incoming.snippets:
            if sn.id in ids:
                sn.id = "snip_" + uuid.uuid4().hex[:8]
            self.data.snippets.append(sn)
            ids.add(sn.id)
        for c in incoming.categories:
            if c not in self.data.categories:
                self.data.categories.append(c)
        self.persist()


    def save_profile(self) -> None:
        """Save full configuration (snippets + settings + categories) to a profile file."""
        import json
        from PySide6.QtWidgets import QFileDialog

        path, _ = QFileDialog.getSaveFileName(
            self.manager,
            "Save Profile",
            "quicktext-profile.json",
            "Quick Text Profile (*.json)",
        )
        if not path:
            return
        Path(path).write_text(
            json.dumps(self.data.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        QMessageBox.information(self.manager, "Quick Text", f"Profile saved:\n{path}")

    def load_profile(self) -> None:
        """Replace current configuration with a saved profile."""
        import json
        from PySide6.QtWidgets import QFileDialog

        from models.snippet import AppData as AD

        path, _ = QFileDialog.getOpenFileName(
            self.manager,
            "Load Profile",
            "",
            "Quick Text Profile (*.json)",
        )
        if not path:
            return
        if (
            QMessageBox.question(
                self.manager,
                "Load Profile",
                "Replace current snippets, categories, and settings with this profile?",
                QMessageBox.StandardButton.Cancel | QMessageBox.StandardButton.Yes,
            )
            != QMessageBox.StandardButton.Yes
        ):
            return
        try:
            raw = json.loads(Path(path).read_text(encoding="utf-8"))
            self.data = AD.from_dict(raw)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.warning(self.manager, "Load Profile failed", str(exc))
            return
        self._hotkey_warned = False
        self.persist()
        set_start_with_windows(self.data.settings.start_with_windows)
        if self.data.settings.show_tray:
            self.tray.show()
        QMessageBox.information(self.manager, "Quick Text", f"Profile loaded:\n{path}")

    def duplicate_id(self, sid: str) -> None:
        sn = self.data.snippet_by_id(sid)
        if not sn:
            return
        now = time.time()
        copy = Snippet(
            id="snip_" + uuid.uuid4().hex[:8],
            name=f"{sn.name} Copy",
            text=sn.text,
            category=sn.category,
            favorite=False,
            hotkey="",
            action=sn.action,
            show_in_palette=getattr(sn, "show_in_palette", True),
            color=getattr(sn, "color", "") or "",
            created_at=now,
            updated_at=now,
        )
        self.data.snippets.append(copy)
        self.persist()

    def delete_id(self, sid: str) -> None:
        sn = self.data.snippet_by_id(sid)
        if not sn:
            return
        if (
            QMessageBox.question(
                None,
                "Delete snippet",
                f'Delete "{sn.name}"?',
                QMessageBox.StandardButton.Cancel | QMessageBox.StandardButton.Yes,
            )
            != QMessageBox.StandardButton.Yes
        ):
            return
        self.data.snippets = [s for s in self.data.snippets if s.id != sid]
        self.data.recent = [x for x in self.data.recent if x != sid]
        self.persist()

    def paste_id(self, sid: str) -> None:
        sn = self.data.snippet_by_id(sid)
        if not sn:
            return
        hwnd = self.hotkeys.last_hwnd or self._hwnd or get_foreground_hwnd()
        self.menu.hide()
        sn.usage_count += 1
        sn.last_used = time.time()
        limit = self.data.settings.recent_limit or 8
        self.data.recent = [sid, *[x for x in self.data.recent if x != sid]][:limit]
        self.persist(rebind=False)

        def go() -> None:
            try:
                mode = sn.action if sn.action in ("paste", "copy") else self.data.settings.insert_mode
                # Always put Unicode text on clipboard so user can Ctrl+V manually.
                # Do not restore old clipboard after select (would erase the snippet).
                paste_text(
                    sn.text,
                    hwnd,
                    restore_clip=False,
                    copy_only=(mode == "copy"),
                )
            except Exception as exc:  # noqa: BLE001
                print(f"[QuickText] paste failed: {exc}")

        QTimer.singleShot(40, go)

    def _tray_activated(self, reason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.open_manager()
        elif reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.open_menu()

    def quit(self) -> None:
        self.hotkeys.clear()
        self.qt.quit()

    def run(self) -> int:
        return self.qt.exec()


def run() -> None:
    app = QuickTextApp()
    sys.exit(app.run())
