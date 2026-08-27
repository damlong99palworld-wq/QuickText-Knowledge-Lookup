from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QCursor, QKeyEvent
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from models.snippet import AppData, Snippet, format_hotkey_display


class QuickMenu(QWidget):
    picked = Signal(str)
    knowledge_requested = Signal(str)

    def __init__(self) -> None:
        super().__init__(
            None,
            Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint,
        )
        self.resize(420, 360)
        self._data: AppData | None = None
        self._flat: list[Snippet] = []
        self._expanded = {"Favorites", "Recent", "Results"}

        self.search = QLineEdit()
        self.search.setPlaceholderText("Search snippets…")
        self.search.textChanged.connect(self._rebuild)
        self.knowledge_btn = QPushButton("Knowledge")
        self.knowledge_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.knowledge_btn.setToolTip("Paste into Knowledge search")
        self.knowledge_btn.clicked.connect(self._open_knowledge)
        self.list = QListWidget()
        self.list.itemActivated.connect(self._activate)
        self.list.itemClicked.connect(self._activate)

        search_row = QHBoxLayout()
        search_row.setContentsMargins(0, 0, 0, 0)
        search_row.setSpacing(6)
        search_row.addWidget(self.knowledge_btn, 0)
        search_row.addWidget(self.search, 1)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.addLayout(search_row)
        layout.addWidget(self.list, 1)

    def _open_knowledge(self) -> None:
        typed = self.search.text().strip()
        self.hide()
        self.knowledge_requested.emit(typed)

    def popup(self, data: AppData) -> None:
        self._data = data
        self._expanded = {"Favorites", "Recent", "Results"}
        self.search.blockSignals(True)
        self.search.clear()
        self.search.blockSignals(False)
        self._rebuild()
        self.resize(420, 360)
        pos = QCursor.pos()
        if data.settings.popup_position == "center":
            self._place_center()
        else:
            self._place_near_cursor(pos)
        self.show()
        self.raise_()
        self.activateWindow()
        self.search.setFocus(Qt.FocusReason.ActiveWindowFocusReason)

    def _screen_geo_at(self, point):
        from PySide6.QtGui import QGuiApplication

        screen = QGuiApplication.screenAt(point) or QGuiApplication.primaryScreen()
        if screen is None:
            return None
        return screen.availableGeometry()

    def _place_center(self) -> None:
        from PySide6.QtGui import QGuiApplication

        screen = QGuiApplication.primaryScreen()
        if not screen:
            return
        geo = screen.availableGeometry()
        self.move(
            geo.center().x() - self.width() // 2,
            geo.center().y() - self.height() // 2,
        )

    def _place_near_cursor(self, cursor) -> None:
        """Keep palette fully on-screen: flip up near bottom, flip left near right edge."""
        geo = self._screen_geo_at(cursor)
        if geo is None:
            self.move(cursor.x() + 8, cursor.y() + 8)
            return
        margin = 10
        w, h = self.width(), self.height()
        # Default: open slightly below-right of cursor
        x = cursor.x() + margin
        y = cursor.y() + margin
        # Near right edge → open to the left of cursor
        if x + w > geo.right() - margin:
            x = cursor.x() - w - margin
        # Near bottom → open above cursor
        if y + h > geo.bottom() - margin:
            y = cursor.y() - h - margin
        # Near left / top: clamp into available geometry
        x = max(geo.left() + margin, min(x, geo.right() - w - margin))
        y = max(geo.top() + margin, min(y, geo.bottom() - h - margin))
        self.move(int(x), int(y))

    def _rebuild(self) -> None:
        self.list.clear()
        self._flat = []
        if not self._data:
            return
        q = self.search.text().strip().lower()
        snippets = [s for s in self._data.snippets if getattr(s, "show_in_palette", True)]
        if q:
            matched = [
                s
                for s in snippets
                if q in s.name.lower() or q in s.text.lower() or q in s.category.lower()
            ]
            groups = [("Results", matched)]
        else:
            by_id = {s.id: s for s in snippets}
            fav = [s for s in snippets if s.favorite]
            used = {s.id for s in fav}
            recent = [by_id[i] for i in self._data.recent if i in by_id and i not in used]
            limit = self._data.settings.recent_limit or 8
            groups = []
            if fav:
                groups.append(("Favorites", fav))
            if recent:
                groups.append(("Recent", recent[:limit]))
                used |= {s.id for s in recent[:limit]}
            for c in self._data.categories:
                items = [s for s in snippets if s.category == c and s.id not in used]
                if items:
                    groups.append((c, items))

        for title, items in groups:
            if not items:
                continue
            searching = bool(q)
            always = title in ("Favorites", "Recent", "Results") or searching
            open_g = always or title in self._expanded
            mark = "▾ " if open_g else "▸ "
            header = QListWidgetItem(mark + title)
            header.setFlags(Qt.ItemFlag.ItemIsEnabled)
            header.setForeground(Qt.GlobalColor.gray)
            if self._data and title not in ("Favorites", "Recent", "Results"):
                cc = (self._data.category_colors or {}).get(title) or ""
                if cc:
                    header.setForeground(QColor(cc))
            header.setData(Qt.ItemDataRole.UserRole + 1, title)
            self.list.addItem(header)
            if not open_g:
                continue
            for s in items:
                row = QListWidgetItem(("★ " if s.favorite else "  ") + s.name)
                if s.hotkey:
                    row.setToolTip(f"{s.hotkey}\n{s.text[:200]}")
                color = getattr(s, "color", "") or ""
                if color:
                    row.setForeground(QColor(color))
                row.setData(Qt.ItemDataRole.UserRole, s.id)
                self.list.addItem(row)
                self._flat.append(s)
        if self._flat:
            for i in range(self.list.count()):
                if self.list.item(i).data(Qt.ItemDataRole.UserRole):
                    self.list.setCurrentRow(i)
                    break

    def _activate(self, item: QListWidgetItem) -> None:
        sid = item.data(Qt.ItemDataRole.UserRole)
        if not sid:
            title = item.data(Qt.ItemDataRole.UserRole + 1)
            if title and title not in ("Favorites", "Recent", "Results"):
                if title in self._expanded:
                    self._expanded.discard(title)
                else:
                    self._expanded.add(title)
                self._rebuild()
            return
        self.picked.emit(str(sid))
        if not self._data or self._data.settings.close_after_select:
            self.hide()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.hide()
            return
        if event.key() in (Qt.Key.Key_Down, Qt.Key.Key_Up):
            event.accept()
            rows = [i for i in range(self.list.count()) if self.list.item(i).data(Qt.ItemDataRole.UserRole)]
            if not rows:
                return
            cur = self.list.currentRow()
            if cur not in rows:
                self.list.setCurrentRow(rows[0 if event.key() == Qt.Key.Key_Down else -1])
                return
            idx = rows.index(cur)
            idx = min(len(rows) - 1, idx + 1) if event.key() == Qt.Key.Key_Down else max(0, idx - 1)
            self.list.setCurrentRow(rows[idx])
            return
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            item = self.list.currentItem()
            if item:
                self._activate(item)
            return
        super().keyPressEvent(event)
