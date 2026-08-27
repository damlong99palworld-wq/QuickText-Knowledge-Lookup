from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from PySide6.QtCore import QObject, QTimer
from PySide6.QtWidgets import QApplication, QMessageBox, QWidget

from knowledge.services.hotkeys import HotkeyManager
from knowledge.services.search import KnowledgeSearch
from knowledge.services.selection_capture import capture_selected_text
from knowledge.models.settings import AppSettings
from knowledge.services.storage import KnowledgeStore, default_data_dir
from knowledge.ui.main_window import MainWindow


SAMPLE_PATH = Path(__file__).resolve().parent / "sample" / "knowledge.sample.json"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Knowledge Lookup")
    parser.add_argument("--query", default="", help="Initial search query (QuickText hook later)")
    parser.add_argument("--data-dir", default="", help="Override local data directory")
    parser.add_argument(
        "--seed-sample",
        action="store_true",
        help="Import sample UE5 entries if the store is empty",
    )
    return parser.parse_args(argv)


def seed_sample_if_empty(store: KnowledgeStore) -> None:
    if store.entries:
        return
    if not SAMPLE_PATH.exists():
        return
    try:
        store.import_json(SAMPLE_PATH, merge=False)
        store.save()
    except (OSError, ValueError):
        pass


def search_knowledge(entries, query: str):
    return KnowledgeSearch().search(entries, query)


class LookupApp(QObject):
    def __init__(self, store: KnowledgeStore, settings: AppSettings, initial_query: str = ""):
        super().__init__()
        self.store = store
        self.settings = settings
        self.window = MainWindow(store, settings, initial_query=initial_query)
        self.hotkeys = HotkeyManager(self)
        self._sink = QWidget()
        self._sink.setObjectName("HotkeySink")
        self._sink.resize(1, 1)
        self._sink.setWindowTitle("KnowledgeLookupHotkeySink")
        self.window.settings_changed.connect(self._on_settings_changed)
        self.hotkeys.triggered.connect(self.on_global_hotkey)

    def start(self, start_minimized: bool = False) -> None:
        self._sink.showMinimized()
        self._sink.hide()
        QTimer.singleShot(0, self._register_hotkey)
        if start_minimized and self.settings.minimize_to_tray:
            if self.window.tray:
                self.window.tray.show()
            print(f"[KnowledgeLookup] Running.\nGlobal hotkey: {self.settings.hotkey}", flush=True)
            return
        self.window.reveal()
        print(f"[KnowledgeLookup] Running.\nGlobal hotkey: {self.settings.hotkey}", flush=True)

    def _register_hotkey(self) -> None:
        hwnd = int(self.window.winId())
        self.hotkeys.bind_hwnd(hwnd)
        ok = self.hotkeys.register(self.settings.hotkey)
        if ok:
            self.window.status.showMessage(
                f"Global hotkey: {self.hotkeys.registered_display}",
                5000,
            )
            print(f"[KnowledgeLookup] Registered {self.hotkeys.registered_display}", flush=True)
            return
        print(f"[KnowledgeLookup] {self.hotkeys.last_error}", flush=True)
        if sys.platform == "win32":
            QMessageBox.warning(
                self.window,
                "Global Hotkey",
                self.hotkeys.last_error
                or f"Could not register {self.settings.hotkey}.\nThis hotkey may already be in use.",
            )

    def _on_settings_changed(self, settings: AppSettings) -> None:
        self.settings = settings
        self.window.settings = settings
        ok = self.hotkeys.register(settings.hotkey)
        if ok:
            self.window.status.showMessage(f"Global hotkey: {self.hotkeys.registered_display}", 4000)
            return
        QMessageBox.warning(
            self.window,
            "Global Hotkey",
            self.hotkeys.last_error
            or f"Could not register {settings.hotkey}.\nThis hotkey may already be in use.",
        )

    def on_global_hotkey(self) -> None:
        query = ""
        if self.settings.capture_selected_text:
            result = capture_selected_text(
                restore_clipboard=self.settings.restore_clipboard,
                delay_ms=self.settings.capture_delay_ms,
            )
            if result.had_selection:
                query = result.text
        self.window.reveal()
        self.window.apply_external_query(query, from_hotkey=True)


def _setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="[KnowledgeLookup] %(message)s",
    )


def run(argv: list[str] | None = None) -> int:
    _setup_logging()
    log = logging.getLogger("KnowledgeLookup")
    args = parse_args(argv)
    data_dir = Path(args.data_dir) if args.data_dir else default_data_dir()
    store = KnowledgeStore(data_dir)
    store.load()
    log.info("Loaded %s entries", len(store.entries))
    if args.seed_sample or not store.data_path.exists():
        seed_sample_if_empty(store)
    settings = AppSettings.from_dict(store.settings)
    if not store.settings:
        store.settings = settings.to_dict()
        store.save_settings()

    qt_app = QApplication.instance() or QApplication(sys.argv)
    qt_app.setApplicationName("Knowledge Lookup")
    qt_app.setOrganizationName("KnowledgeLookup")
    qt_app.setQuitOnLastWindowClosed(False)

    app = LookupApp(store, settings, initial_query=args.query)
    app.start(start_minimized=settings.start_minimized and not args.query)
    if args.query:
        app.window.apply_external_query(args.query)
    return qt_app.exec()
