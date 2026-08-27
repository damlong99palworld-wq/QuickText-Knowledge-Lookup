from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from models.snippet import AppData, format_hotkey_display
from ui.color_picker import ColorPickerDialog


class SnippetManager(QMainWindow):
    add_requested = Signal()
    edit_requested = Signal(str)
    delete_requested = Signal(str)
    duplicate_requested = Signal(str)
    settings_requested = Signal()
    export_requested = Signal()
    import_requested = Signal()
    save_profile_requested = Signal()
    load_profile_requested = Signal()
    knowledge_requested = Signal()
    order_changed = Signal()
    palette_visibility_changed = Signal()
    color_changed = Signal()
    favorite_changed = Signal()
    category_color_changed = Signal()

    COL_SHOW = 0
    COL_FAV = 1
    COL_NAME = 2
    COL_CAT = 3
    COL_HOTKEY = 4
    COL_COLOR = 5

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Quick Text — Snippet Manager")
        self.resize(1020, 600)
        self._data: AppData | None = None
        self._filter = "all"
        self._sort_col = self.COL_NAME
        self._sort_asc = True

        self.cats = QListWidget()
        self.cats.currentRowChanged.connect(self._on_cat)
        self.cats.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.cats.customContextMenuRequested.connect(self._cat_ctx)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Search…")
        self.search.textChanged.connect(self.refresh_list)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(
            ["Palette", "Favorites", "Name", "Category", "Hotkey", "Color"]
        )
        hdr = self.table.horizontalHeader()
        hdr.setSectionsMovable(True)
        hdr.setFirstSectionMovable(True)
        # All columns user-resizable by dragging header edges
        for col in range(6):
            hdr.setSectionResizeMode(col, QHeaderView.ResizeMode.Interactive)
        hdr.setStretchLastSection(False)
        self.table.setColumnWidth(self.COL_SHOW, 70)
        self.table.setColumnWidth(self.COL_FAV, 80)
        self.table.setColumnWidth(self.COL_NAME, 260)
        self.table.setColumnWidth(self.COL_CAT, 120)
        self.table.setColumnWidth(self.COL_HOTKEY, 120)
        self.table.setColumnWidth(self.COL_COLOR, 100)
        hdr.setSortIndicatorShown(True)
        hdr.setSortIndicator(self.COL_NAME, Qt.SortOrder.AscendingOrder)
        hdr.sectionClicked.connect(self._on_header_click)

        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.cellDoubleClicked.connect(self._on_cell_double)
        self.table.cellClicked.connect(self._on_cell_clicked)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._ctx)

        add_cat = QPushButton("Add Category")
        add_cat.clicked.connect(self._add_cat)
        del_cat = QPushButton("Delete Category")
        del_cat.clicked.connect(self._delete_cat)
        color_cat = QPushButton("Category Color")
        color_cat.clicked.connect(self._color_category)

        self.btn_add = QPushButton("Add")
        self.btn_add.clicked.connect(self._on_add_clicked)
        self.btn_edit = QPushButton("Edit")
        self.btn_edit.clicked.connect(self._on_edit_clicked)
        self.btn_color = QPushButton("Color")
        self.btn_color.clicked.connect(self._on_color_clicked)
        self.btn_dup = QPushButton("Duplicate")
        self.btn_dup.clicked.connect(self._on_dup_clicked)
        self.btn_del = QPushButton("Delete")
        self.btn_del.clicked.connect(self._on_del_clicked)
        self.btn_settings = QPushButton("Settings")
        self.btn_settings.clicked.connect(lambda: self.settings_requested.emit())
        self.btn_save_profile = QPushButton("Save Profile")
        self.btn_save_profile.clicked.connect(lambda: self.save_profile_requested.emit())
        self.btn_load_profile = QPushButton("Load Profile")
        self.btn_load_profile.clicked.connect(lambda: self.load_profile_requested.emit())
        self.btn_knowledge = QPushButton("Knowledge")
        self.btn_knowledge.clicked.connect(lambda: self.knowledge_requested.emit())

        left = QVBoxLayout()
        left.addWidget(QLabel("Categories"))
        left.addWidget(self.cats, 1)
        left.addWidget(add_cat)
        left.addWidget(del_cat)
        left.addWidget(color_cat)
        lw = QWidget()
        lw.setLayout(left)

        btns = QHBoxLayout()
        for b in (
            self.btn_add,
            self.btn_edit,
            self.btn_color,
            self.btn_dup,
            self.btn_del,
            self.btn_settings,
            self.btn_save_profile,
            self.btn_load_profile,
            self.btn_knowledge,
        ):
            btns.addWidget(b)
        btns.addStretch()

        right = QVBoxLayout()
        right.addWidget(self.search)
        right.addWidget(self.table, 1)
        right.addLayout(btns)
        rw = QWidget()
        rw.setLayout(right)

        split = QSplitter()
        split.addWidget(lw)
        split.addWidget(rw)
        split.setStretchFactor(1, 3)
        self.setCentralWidget(split)

    def _on_add_clicked(self) -> None:
        self.add_requested.emit()

    def _on_edit_clicked(self) -> None:
        sid = self._current_id()
        if not sid:
            QMessageBox.information(self, "Quick Text", "Select a row first.")
            return
        self.edit_requested.emit(sid)

    def _on_color_clicked(self) -> None:
        self._color_current()

    def _on_dup_clicked(self) -> None:
        sid = self._current_id()
        if not sid:
            QMessageBox.information(self, "Quick Text", "Select a row first.")
            return
        self.duplicate_requested.emit(sid)

    def _on_del_clicked(self) -> None:
        sid = self._current_id()
        if not sid:
            QMessageBox.information(self, "Quick Text", "Select a row first.")
            return
        self.delete_requested.emit(sid)

    def set_data(self, data: AppData) -> None:
        prev = self._filter
        self._data = data
        self._rebuild_cats(select_key=prev)
        self.refresh_list()

    def _cat_color(self, name: str) -> str:
        if not self._data:
            return ""
        return str((self._data.category_colors or {}).get(name) or "")

    def _rebuild_cats(self, select_key: str | None = None) -> None:
        self.cats.blockSignals(True)
        self.cats.clear()
        keys = [("All", "all"), ("Favorites", "favorites"), ("Recent", "recent")]
        if self._data:
            for c in self._data.categories:
                keys.append((c, c))
        select_row = 0
        for i, (label, key) in enumerate(keys):
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, key)
            if key not in ("all", "favorites", "recent"):
                col = self._cat_color(key)
                if col:
                    item.setForeground(QColor(col))
            self.cats.addItem(item)
            if select_key and key == select_key:
                select_row = i
        self.cats.setCurrentRow(select_row)
        self._filter = str(self.cats.item(select_row).data(Qt.ItemDataRole.UserRole))
        self.cats.blockSignals(False)

    def _on_cat(self) -> None:
        item = self.cats.currentItem()
        if item:
            self._filter = str(item.data(Qt.ItemDataRole.UserRole))
        self.refresh_list()

    def _filtered_snippets(self):
        if not self._data:
            return []
        q = self.search.text().strip().lower()
        items = list(self._data.snippets)
        if self._filter == "favorites":
            items = [s for s in items if s.favorite]
        elif self._filter == "recent":
            order = {sid: i for i, sid in enumerate(self._data.recent)}
            items = sorted([s for s in items if s.id in order], key=lambda s: order[s.id])
        elif self._filter not in ("all",):
            items = [s for s in items if s.category == self._filter]
        if q:
            items = [
                s
                for s in items
                if q in s.name.lower() or q in s.text.lower() or q in s.category.lower()
            ]
        if self._filter != "recent":
            key_fn = {
                self.COL_NAME: lambda s: s.name.lower(),
                self.COL_CAT: lambda s: s.category.lower(),
                self.COL_HOTKEY: lambda s: (s.hotkey or "").lower(),
                self.COL_FAV: lambda s: (0 if s.favorite else 1, s.name.lower()),
                self.COL_COLOR: lambda s: (getattr(s, "color", "") or "").lower(),
            }.get(self._sort_col, lambda s: s.name.lower())
            items = sorted(items, key=key_fn, reverse=not self._sort_asc)
        return items

    def refresh_list(self) -> None:
        self.table.setRowCount(0)
        if not self._data:
            return
        for s in self._filtered_snippets():
            row = self.table.rowCount()
            self.table.insertRow(row)

            chk = QCheckBox()
            chk.setChecked(bool(getattr(s, "show_in_palette", True)))
            chk.setToolTip("Show this snippet on the Palette (Ctrl+F1)")
            chk.stateChanged.connect(lambda state, sid=s.id: self._toggle_show(sid, state))
            wrap = QWidget()
            lay = QHBoxLayout(wrap)
            lay.setContentsMargins(4, 0, 4, 0)
            lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lay.addWidget(chk)
            self.table.setCellWidget(row, self.COL_SHOW, wrap)

            fav_item = QTableWidgetItem("★" if s.favorite else "")
            fav_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            fav_item.setData(Qt.ItemDataRole.UserRole, s.id)
            fav_item.setToolTip("Click to toggle Favorite")
            if s.favorite:
                fav_item.setForeground(QColor("#f5c542"))
            self.table.setItem(row, self.COL_FAV, fav_item)

            name_item = QTableWidgetItem(s.name)
            name_item.setData(Qt.ItemDataRole.UserRole, s.id)
            color = getattr(s, "color", "") or ""
            if color:
                name_item.setForeground(QColor(color))
            self.table.setItem(row, self.COL_NAME, name_item)

            cat_item = QTableWidgetItem(s.category)
            cat_item.setData(Qt.ItemDataRole.UserRole, s.id)
            cat_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            cc = self._cat_color(s.category)
            if cc:
                cat_item.setForeground(QColor(cc))
            self.table.setItem(row, self.COL_CAT, cat_item)

            hk_item = QTableWidgetItem(format_hotkey_display(s.hotkey))
            hk_item.setData(Qt.ItemDataRole.UserRole, s.id)
            hk_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, self.COL_HOTKEY, hk_item)

            color_text = color or ""
            color_item = QTableWidgetItem(color_text)
            color_item.setData(Qt.ItemDataRole.UserRole, s.id)
            color_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            color_item.setToolTip("Double-click or use Color button to change")
            if color:
                color_item.setForeground(QColor(color))
                color_item.setBackground(QBrush(QColor(color)))
                # readable text: light vs dark
                qc = QColor(color)
                if qc.lightness() < 128:
                    color_item.setForeground(QColor("#ffffff"))
                else:
                    color_item.setForeground(QColor("#111111"))
            self.table.setItem(row, self.COL_COLOR, color_item)

    def _toggle_show(self, sid: str, state: int) -> None:
        if not self._data:
            return
        sn = self._data.snippet_by_id(sid)
        if not sn:
            return
        try:
            sn.show_in_palette = Qt.CheckState(state) == Qt.CheckState.Checked
        except Exception:
            sn.show_in_palette = bool(state)
        self.palette_visibility_changed.emit()

    def _on_header_click(self, section: int) -> None:
        # section is visual index when columns moved — map to logical
        logical = self.table.horizontalHeader().logicalIndex(section)
        if logical == self.COL_SHOW:
            return
        if self._sort_col == logical:
            self._sort_asc = not self._sort_asc
        else:
            self._sort_col = logical
            self._sort_asc = True
        order = Qt.SortOrder.AscendingOrder if self._sort_asc else Qt.SortOrder.DescendingOrder
        self.table.horizontalHeader().setSortIndicator(logical, order)
        self.refresh_list()

    def _current_id(self) -> str | None:
        row = self.table.currentRow()
        if row < 0:
            return None
        for col in (self.COL_NAME, self.COL_FAV, self.COL_COLOR, self.COL_CAT, self.COL_HOTKEY):
            item = self.table.item(row, col)
            if item:
                sid = item.data(Qt.ItemDataRole.UserRole)
                if sid:
                    return str(sid)
        return None

    def _on_cell_clicked(self, row: int, col: int) -> None:
        if col != self.COL_FAV or not self._data:
            return
        item = self.table.item(row, self.COL_FAV)
        if not item:
            return
        sid = item.data(Qt.ItemDataRole.UserRole)
        sn = self._data.snippet_by_id(str(sid)) if sid else None
        if not sn:
            return
        sn.favorite = not sn.favorite
        self.favorite_changed.emit()
        self.refresh_list()
        for r in range(self.table.rowCount()):
            it = self.table.item(r, self.COL_NAME)
            if it and it.data(Qt.ItemDataRole.UserRole) == sid:
                self.table.selectRow(r)
                break

    def _on_cell_double(self, row: int, col: int) -> None:
        if col in (self.COL_SHOW, self.COL_FAV):
            return
        if col == self.COL_COLOR:
            self.table.selectRow(row)
            self._color_current()
            return
        item = self.table.item(row, self.COL_NAME)
        if item:
            sid = item.data(Qt.ItemDataRole.UserRole)
            if sid:
                self.edit_requested.emit(str(sid))

    def _color_current(self) -> None:
        if not self._data:
            return
        sid = self._current_id()
        if not sid:
            QMessageBox.information(self, "Quick Text", "Select a row first.")
            return
        sn = self._data.snippet_by_id(sid)
        if not sn:
            return
        dlg = ColorPickerDialog(sn.color or "", list(self._data.settings.saved_colors or []), self)
        if dlg.exec():
            sn.color = dlg.result_color
            self._data.settings.saved_colors = dlg.saved_colors()
            self.color_changed.emit()
            self.refresh_list()

    def _color_category(self) -> None:
        if not self._data:
            return
        item = self.cats.currentItem()
        if not item:
            QMessageBox.information(self, "Quick Text", "Select a category in the left list.")
            return
        key = str(item.data(Qt.ItemDataRole.UserRole))
        if key in ("all", "favorites", "recent"):
            QMessageBox.information(
                self, "Quick Text", "Pick a real category (not All / Favorites / Recent)."
            )
            return
        current = self._cat_color(key)
        dlg = ColorPickerDialog(current, list(self._data.settings.saved_colors or []), self)
        if dlg.exec():
            if not self._data.category_colors:
                self._data.category_colors = {}
            if dlg.result_color:
                self._data.category_colors[key] = dlg.result_color
            else:
                self._data.category_colors.pop(key, None)
            self._data.settings.saved_colors = dlg.saved_colors()
            self.category_color_changed.emit()
            self._rebuild_cats(select_key=key)
            self.refresh_list()

    def _add_cat(self) -> None:
        if not self._data:
            return
        name, ok = QInputDialog.getText(self, "Category", "Name")
        if ok and name.strip() and name.strip() not in self._data.categories:
            self._data.categories.append(name.strip())
            self._rebuild_cats(select_key=name.strip())
            self.order_changed.emit()

    def _delete_cat(self) -> None:
        if not self._data:
            return
        item = self.cats.currentItem()
        if not item:
            QMessageBox.information(self, "Quick Text", "Select a category in the left list.")
            return
        key = str(item.data(Qt.ItemDataRole.UserRole))
        if key in ("all", "favorites", "recent"):
            QMessageBox.information(self, "Quick Text", "Cannot delete All / Favorites / Recent.")
            return
        if key == "General":
            QMessageBox.information(self, "Quick Text", "Cannot delete the General category.")
            return
        n = sum(1 for s in self._data.snippets if s.category == key)
        msg = f'Delete category "{key}"?'
        if n:
            msg += f"\n{n} snippet(s) will move to General."
        if (
            QMessageBox.question(
                self,
                "Delete Category",
                msg,
                QMessageBox.StandardButton.Cancel | QMessageBox.StandardButton.Yes,
            )
            != QMessageBox.StandardButton.Yes
        ):
            return
        self._data.categories = [c for c in self._data.categories if c != key]
        if self._data.category_colors:
            self._data.category_colors.pop(key, None)
        for s in self._data.snippets:
            if s.category == key:
                s.category = "General"
        if "General" not in self._data.categories:
            self._data.categories.insert(0, "General")
        self._rebuild_cats(select_key="all")
        self.order_changed.emit()
        self.refresh_list()

    def _cat_ctx(self, pos) -> None:
        item = self.cats.itemAt(pos)
        if item:
            self.cats.setCurrentItem(item)
        menu = QMenu(self)
        menu.addAction("Add Category", self._add_cat)
        menu.addAction("Delete Category", self._delete_cat)
        menu.addAction("Category Color…", self._color_category)
        menu.exec(self.cats.mapToGlobal(pos))

    def _ctx(self, pos) -> None:
        index = self.table.indexAt(pos)
        if index.isValid():
            self.table.selectRow(index.row())
        sid = self._current_id()
        if not sid:
            return
        menu = QMenu(self)
        menu.addAction("Edit", self._on_edit_clicked)
        menu.addAction("Color", self._on_color_clicked)
        menu.addAction("Duplicate", self._on_dup_clicked)
        menu.addAction("Delete", self._on_del_clicked)
        menu.exec(self.table.mapToGlobal(pos))
