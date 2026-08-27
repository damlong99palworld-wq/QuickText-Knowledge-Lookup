from __future__ import annotations

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QAction, QColor, QCursor, QGuiApplication, QIcon, QKeySequence, QPixmap, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QSplitter,
    QStatusBar,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)

from knowledge.models.knowledge import KnowledgeEntry
from knowledge.services.search import KnowledgeSearch
from knowledge.models.settings import POPUP_CENTER, AppSettings
from knowledge.services.storage import KnowledgeStore
from knowledge.ui.knowledge_editor import KnowledgeEditor
from knowledge.ui.knowledge_view import KnowledgeView
from knowledge.ui.settings_window import SettingsWindow
from knowledge.shared.ui_helpers import qfont_from_style
from knowledge.ui.theme import qss_for_theme


ALL_CATEGORY = "All"


def make_tray_icon() -> QIcon:
    pix = QPixmap(32, 32)
    pix.fill(Qt.transparent)
    pix.fill(Qt.GlobalColor.darkCyan)
    return QIcon(pix)


class MainWindow(QMainWindow):
    settings_changed = Signal(object)
    exit_requested = Signal()

    def __init__(self, store: KnowledgeStore, settings: AppSettings, initial_query: str = "", embedded: bool = False):
        super().__init__()
        self.store = store
        self.settings = settings
        self.searcher = KnowledgeSearch()
        self._really_quit = False
        self.embedded = embedded
        self.zoom = 100
        self.setWindowTitle("Knowledge Lookup")
        self.resize(1100, 720)
        self.setStyleSheet(qss_for_theme(settings.appearance.theme))

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(10, 10, 10, 8)
        root.setSpacing(8)

        top = QHBoxLayout()
        title = QLabel("Knowledge Lookup")
        title.setObjectName("AppTitle")
        top.addWidget(title)
        top.addStretch(1)
        self.add_btn = QPushButton("+ Add Knowledge")
        self.add_btn.setObjectName("PrimaryButton")
        self.dup_btn = QPushButton("Duplicate")
        self.del_btn = QPushButton("Delete")
        self.del_btn.setObjectName("DangerButton")
        self.settings_btn = QPushButton("Settings")
        for btn in (self.add_btn, self.dup_btn, self.del_btn, self.settings_btn):
            btn.setCursor(Qt.PointingHandCursor)
            top.addWidget(btn)
        root.addLayout(top)

        search_row = QHBoxLayout()
        search_row.addWidget(QLabel("Search:"))
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("niagara, game ability, motion warp...")
        self.search_box.setClearButtonEnabled(True)
        if initial_query:
            self.search_box.setText(initial_query)
        search_row.addWidget(self.search_box, 1)
        root.addLayout(search_row)

        splitter = QSplitter(Qt.Horizontal)
        left = QFrame()
        left.setObjectName("Card")
        left_layout = QVBoxLayout(left)
        cat_title = QLabel("CATEGORIES")
        cat_title.setObjectName("SectionTitle")
        left_layout.addWidget(cat_title)
        self.category_list = QListWidget()
        left_layout.addWidget(self.category_list, 1)
        list_title = QLabel("ENTRIES")
        list_title.setObjectName("SectionTitle")
        left_layout.addWidget(list_title)
        self.entry_list = QListWidget()
        left_layout.addWidget(self.entry_list, 2)

        self.view = KnowledgeView()
        splitter.addWidget(left)
        splitter.addWidget(self.view)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([280, 820])
        root.addWidget(splitter, 1)

        self.status = QStatusBar()
        self.setStatusBar(self.status)

        self.tray: QSystemTrayIcon | None = None
        self._build_menu()
        if not self.embedded:
            self._build_tray()
        self._connect()
        self._install_shortcuts()
        self.refresh_all()
        self.apply_appearance()
        QTimer.singleShot(0, self.search_box.setFocus)

    def _build_menu(self) -> None:
        file_menu = self.menuBar().addMenu("&File")
        export_act = QAction("Export JSON...", self)
        import_act = QAction("Import JSON...", self)
        settings_act = QAction("Settings...", self)
        hide_act = QAction("Hide to Tray", self)
        quit_act = QAction("Exit", self)
        quit_act.setShortcut(QKeySequence.Quit)
        export_act.triggered.connect(self._export)
        import_act.triggered.connect(self._import)
        settings_act.triggered.connect(self.open_settings)
        hide_act.triggered.connect(self.hide)
        quit_act.triggered.connect(self.quit_app)
        file_menu.addAction(export_act)
        file_menu.addAction(import_act)
        file_menu.addSeparator()
        file_menu.addAction(settings_act)
        file_menu.addAction(hide_act)
        file_menu.addSeparator()
        file_menu.addAction(quit_act)

        entry_menu = self.menuBar().addMenu("&Entry")
        add_act = QAction("Add Knowledge", self)
        add_act.setShortcut("Ctrl+N")
        edit_act = QAction("Edit", self)
        edit_act.setShortcut("Ctrl+E")
        dup_act = QAction("Duplicate", self)
        dup_act.setShortcut("Ctrl+D")
        del_act = QAction("Delete", self)
        del_act.setShortcut("Delete")
        add_act.triggered.connect(self.add_entry)
        edit_act.triggered.connect(self.edit_entry)
        dup_act.triggered.connect(self.duplicate_entry)
        del_act.triggered.connect(self.delete_entry)
        entry_menu.addAction(add_act)
        entry_menu.addAction(edit_act)
        entry_menu.addAction(dup_act)
        entry_menu.addAction(del_act)

    def _build_tray(self) -> None:
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        self.tray = QSystemTrayIcon(make_tray_icon(), self)
        self.tray.setToolTip("Knowledge Lookup")
        menu = QMenu()
        open_act = menu.addAction("Open Knowledge Lookup")
        add_act = menu.addAction("Add Knowledge")
        settings_act = menu.addAction("Settings")
        menu.addSeparator()
        exit_act = menu.addAction("Exit")
        open_act.triggered.connect(self.reveal)
        add_act.triggered.connect(self._tray_add)
        settings_act.triggered.connect(self.open_settings)
        exit_act.triggered.connect(self.quit_app)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._tray_activated)
        self.tray.show()

    def _tray_activated(self, reason) -> None:
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            self.reveal()

    def _tray_add(self) -> None:
        self.reveal()
        self.add_entry()

    def _connect(self) -> None:
        self.search_box.textChanged.connect(self.refresh_entries)
        self.category_list.currentTextChanged.connect(self.refresh_entries)
        self.entry_list.currentItemChanged.connect(self._on_select)
        self.entry_list.itemDoubleClicked.connect(lambda _i: self.edit_entry())
        self.add_btn.clicked.connect(self.add_entry)
        self.dup_btn.clicked.connect(self.duplicate_entry)
        self.del_btn.clicked.connect(self.delete_entry)
        self.settings_btn.clicked.connect(self.open_settings)
        self.view.edit_btn.clicked.connect(self.edit_entry)
        self.view.copy_name_btn.clicked.connect(self.view.copy_name)
        self.view.copy_desc_btn.clicked.connect(self.view.copy_description)
        self.view.copy_all_btn.clicked.connect(self.view.copy_all)
        self.view.create_requested.connect(self.create_from_search)

    def _install_shortcuts(self) -> None:
        QShortcut(QKeySequence("Escape"), self, activated=self._on_escape)
        QShortcut(QKeySequence("Return"), self.search_box, activated=self._focus_first)
        QShortcut(QKeySequence("Enter"), self.search_box, activated=self._focus_first)
        QShortcut(QKeySequence("Down"), self.search_box, activated=self._focus_list)
        QShortcut(QKeySequence("Ctrl+F"), self, activated=self.search_box.setFocus)
        QShortcut(QKeySequence("Ctrl+L"), self, activated=self.search_box.setFocus)
        QShortcut(QKeySequence("Ctrl+,"), self, activated=self.open_settings)
        QShortcut(QKeySequence("Ctrl++"), self, activated=lambda: self.adjust_zoom(10))
        QShortcut(QKeySequence("Ctrl+="), self, activated=lambda: self.adjust_zoom(10))
        QShortcut(QKeySequence("Ctrl+-"), self, activated=lambda: self.adjust_zoom(-10))
        QShortcut(QKeySequence("Ctrl+0"), self, activated=lambda: self.adjust_zoom(0, reset=True))

    def _on_escape(self) -> None:
        if self.search_box.hasFocus() and self.search_box.text():
            self.search_box.clear()
            return
        self.search_box.setFocus()

    def _focus_list(self) -> None:
        if self.entry_list.count():
            self.entry_list.setFocus()
            if self.entry_list.currentRow() < 0:
                self.entry_list.setCurrentRow(0)

    def _focus_first(self) -> None:
        if self.entry_list.count():
            self.entry_list.setCurrentRow(0)
            self.entry_list.setFocus()

    def refresh_all(self) -> None:
        self._refresh_categories()
        self.refresh_entries()
        if self.store.last_error:
            self.status.showMessage(self.store.last_error, 8000)

    def _refresh_categories(self) -> None:
        current = self._selected_category()
        self.category_list.blockSignals(True)
        self.category_list.clear()
        self.category_list.addItem(ALL_CATEGORY)
        for cat in self.store.categories():
            self.category_list.addItem(cat)
        self.category_list.blockSignals(False)
        match = self.category_list.findItems(current, Qt.MatchExactly)
        self.category_list.setCurrentItem(match[0] if match else self.category_list.item(0))

    def _selected_category(self) -> str:
        item = self.category_list.currentItem()
        return item.text() if item else ALL_CATEGORY

    def _visible_hits(self):
        query = self.search_box.text()
        hits = self.searcher.search(self.store.entries, query)
        category = self._selected_category()
        if category != ALL_CATEGORY:
            hits = [h for h in hits if h.entry.category == category]
        return hits

    def refresh_entries(self) -> None:
        selected_id = self._selected_entry_id()
        hits = self._visible_hits()
        self.entry_list.blockSignals(True)
        self.entry_list.clear()
        restore = None
        exact = None
        query = self.search_box.text().strip().lower()
        for hit in hits:
            entry = hit.entry
            item = QListWidgetItem(entry.name or "(unnamed)")
            item.setData(Qt.UserRole, entry.id)
            item.setToolTip(entry.short_description)
            item.setFont(qfont_from_style(self.settings.appearance.entry_name, self.zoom))
            if entry.color:
                item.setForeground(QColor(entry.color))
            elif self.settings.appearance.entry_name.color:
                item.setForeground(QColor(self.settings.appearance.entry_name.color))
            self.entry_list.addItem(item)
            if entry.id == selected_id:
                restore = item
            names = [entry.name.lower(), *[a.lower() for a in entry.aliases]]
            if query and query in names and exact is None:
                exact = item
        self.entry_list.blockSignals(False)
        if restore:
            self.entry_list.setCurrentItem(restore)
        elif exact:
            self.entry_list.setCurrentItem(exact)
        elif self.entry_list.count():
            self.entry_list.setCurrentRow(0)
        else:
            if query:
                self.view.set_unmatched(self.search_box.text().strip())
            else:
                self.view.set_entry(None)
        total = len(self.store.entries)
        shown = self.entry_list.count()
        self.status.showMessage(f"{shown} shown  ·  {total} total  ·  {self.store.data_dir}")

    def _selected_entry_id(self) -> str | None:
        item = self.entry_list.currentItem()
        if not item:
            return None
        return item.data(Qt.UserRole)

    def _selected_entry(self) -> KnowledgeEntry | None:
        entry_id = self._selected_entry_id()
        if not entry_id:
            return None
        return self.store.get(entry_id)

    def _on_select(self, current: QListWidgetItem | None, _prev=None) -> None:
        if current is None:
            query = self.search_box.text().strip()
            if query:
                self.view.set_unmatched(query)
            else:
                self.view.set_entry(None)
            return
        self.view.set_entry(self.store.get(current.data(Qt.UserRole)))

    def add_entry(self) -> None:
        self._open_editor(None, initial_name="")

    def create_from_search(self) -> None:
        name = self.search_box.text().strip()
        self._open_editor(None, initial_name=name)

    def edit_entry(self) -> None:
        entry = self._selected_entry()
        if not entry:
            return
        self._open_editor(entry)

    def _open_editor(self, entry: KnowledgeEntry | None, initial_name: str = "") -> None:
        editor = KnowledgeEditor(
            entry,
            self,
            initial_name=initial_name,
            saved_colors=list(self.settings.saved_colors or []),
            theme=self.settings.appearance.theme,
        )
        if editor.exec() != KnowledgeEditor.Accepted:
            return
        result = editor.result_entry()
        self.settings.saved_colors = editor.saved_colors()
        self.save_settings()
        if entry is None:
            self.store.add(result)
        else:
            self.store.replace(result)
        self._persist()
        self.refresh_all()
        self._select_id(result.id)

    def duplicate_entry(self) -> None:
        entry = self._selected_entry()
        if not entry:
            return
        copy = entry.duplicate()
        self.store.add(copy)
        self._persist()
        self.refresh_all()
        self._select_id(copy.id)

    def delete_entry(self) -> None:
        entry = self._selected_entry()
        if not entry:
            return
        result = QMessageBox.question(
            self,
            "Delete Knowledge",
            f'Delete "{entry.name}"?',
            QMessageBox.Cancel | QMessageBox.Yes,
            QMessageBox.Cancel,
        )
        if result != QMessageBox.Yes:
            return
        self.store.remove(entry.id)
        self._persist()
        self.refresh_all()

    def _select_id(self, entry_id: str) -> None:
        for i in range(self.entry_list.count()):
            item = self.entry_list.item(i)
            if item.data(Qt.UserRole) == entry_id:
                self.entry_list.setCurrentItem(item)
                return

    def apply_appearance(self) -> None:
        self.setStyleSheet(qss_for_theme(self.settings.appearance.theme))
        self.view.configure(self.settings.appearance, self.zoom)
        self.refresh_entries()

    def adjust_zoom(self, delta: int, reset: bool = False) -> None:
        if reset:
            self.zoom = 100
        else:
            self.zoom = max(70, min(180, self.zoom + delta))
        self.view.configure(self.settings.appearance, self.zoom)
        self.refresh_entries()
        self.status.showMessage(f"Zoom {self.zoom}%", 2000)

    def _persist(self) -> None:
        try:
            self.store.save()
        except OSError as exc:
            QMessageBox.critical(self, "Save failed", str(exc))

    def save_settings(self) -> None:
        self.store.settings = self.settings.to_dict()
        try:
            self.store.save_settings()
        except OSError as exc:
            QMessageBox.critical(self, "Save settings failed", str(exc))
        self.settings_changed.emit(self.settings)

    def open_settings(self) -> None:
        dlg = SettingsWindow(self.settings, self)
        if dlg.exec() != SettingsWindow.Accepted:
            return
        self.settings = dlg.result_settings()
        self.save_settings()
        self.apply_appearance()
        self.settings_changed.emit(self.settings)

    def apply_external_query(self, query: str, from_hotkey: bool = False) -> None:
        self.search_box.blockSignals(True)
        self.search_box.setText(query or "")
        self.search_box.blockSignals(False)
        self.refresh_entries()
        if query.strip():
            hits = self._visible_hits()
            if len(hits) == 1:
                self._select_id(hits[0].entry.id)
            elif hits:
                q = query.strip().lower()
                for hit in hits:
                    names = [hit.entry.name.lower(), *[a.lower() for a in hit.entry.aliases]]
                    if q in names:
                        self._select_id(hit.entry.id)
                        break
        if not query.strip() and self.settings.focus_search_when_empty:
            self.search_box.setFocus()
            self.search_box.selectAll()
        elif query.strip():
            self.search_box.setFocus()

    def position_popup(self) -> None:
        screen = QGuiApplication.screenAt(QCursor.pos()) or QGuiApplication.primaryScreen()
        if screen is None:
            return
        geo = screen.availableGeometry()
        frame = self.frameGeometry()
        if self.settings.popup_position == POPUP_CENTER:
            frame.moveCenter(geo.center())
            self.move(frame.topLeft())
            return
        pos = QCursor.pos()
        x = min(max(pos.x() + 12, geo.left()), geo.right() - self.width())
        y = min(max(pos.y() + 12, geo.top()), geo.bottom() - self.height())
        self.move(x, y)

    def reveal(self) -> None:
        self.position_popup()
        self.show()
        self.raise_()
        self.activateWindow()

    def quit_app(self) -> None:
        self._really_quit = True
        self.exit_requested.emit()
        QApplication.instance().quit()

    def closeEvent(self, event) -> None:  # noqa: N802
        if self.embedded:
            event.ignore()
            self.hide()
            return
        if self._really_quit or not self.settings.minimize_to_tray:
            event.accept()
            return
        event.ignore()
        self.hide()
        if self.tray:
            self.tray.showMessage(
                "Knowledge Lookup",
                "Still running in the tray. Use Exit to quit.",
                QSystemTrayIcon.Information,
                2500,
            )

    def _export(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Export Knowledge", "knowledge-export.json", "JSON (*.json)")
        if not path:
            return
        try:
            self.store.export_json(path)
            self.status.showMessage(f"Exported to {path}", 4000)
        except OSError as exc:
            QMessageBox.critical(self, "Export failed", str(exc))

    def _import(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Import Knowledge", "", "JSON (*.json)")
        if not path:
            return
        try:
            added = self.store.import_json(path, merge=True)
            self._persist()
            self.refresh_all()
            self.status.showMessage(f"Imported {added} entries", 4000)
        except (OSError, ValueError) as exc:
            QMessageBox.critical(self, "Import failed", str(exc))
