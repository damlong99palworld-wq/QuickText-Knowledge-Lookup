from __future__ import annotations

import json
import logging
import os
import shutil
from pathlib import Path

from knowledge.constants import (
    APP_DIR_NAME,
    BACKUP_FILE,
    BACKUP_FILE_2,
    BACKUP_FILE_3,
    CORRUPTED_FILE,
    DATA_FILE,
    SETTINGS_FILE,
)
from knowledge.models.knowledge import KnowledgeEntry

log = logging.getLogger("KnowledgeLookup")


def default_data_dir() -> Path:
    override = os.environ.get("KNOWLEDGE_LOOKUP_DIR")
    if override:
        return Path(override).expanduser()

    if os.name == "nt":
        appdata = os.environ.get("APPDATA")
        if appdata:
            return Path(appdata) / APP_DIR_NAME
        return Path.home() / "AppData" / "Roaming" / APP_DIR_NAME

    xdg = os.environ.get("XDG_DATA_HOME")
    if xdg:
        return Path(xdg) / APP_DIR_NAME
    return Path.home() / ".local" / "share" / APP_DIR_NAME


class KnowledgeStore:
    """Loads and saves knowledge.json with rotating backups."""
    def __init__(self, data_dir: Path | None = None):
        self.data_dir = Path(data_dir) if data_dir else default_data_dir()
        self.data_path = self.data_dir / DATA_FILE
        self.settings_path = self.data_dir / SETTINGS_FILE
        self.entries: list[KnowledgeEntry] = []
        self.settings: dict = {}
        self.last_error: str = ""

    def ensure_dir(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def load(self) -> list[KnowledgeEntry]:
        self.last_error = ""
        self.ensure_dir()
        if not self.data_path.exists():
            self.entries = []
            self.settings = self._load_settings()
            return self.entries

        data, err = self._read_json(self.data_path)
        if err:
            backup_ok = self._try_load_backups()
            if not backup_ok:
                self._quarantine(self.data_path)
                self.entries = []
                self.last_error = err
            self.settings = self._load_settings()
            return self.entries

        self.entries = self._parse_entries(data)
        self.settings = self._load_settings()
        log.info("Loaded %s entries from %s", len(self.entries), self.data_path)
        return self.entries

    def save(self) -> None:
        self.ensure_dir()
        payload = {
            "version": 1,
            "entries": [e.to_dict() for e in self.entries],
        }
        if self.data_path.exists():
            self._rotate_backups()
        tmp = self.data_path.with_suffix(".json.tmp")
        with tmp.open("w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
        tmp.replace(self.data_path)
        log.info("Saved %s entries", len(self.entries))

    def save_settings(self) -> None:
        self.ensure_dir()
        tmp = self.settings_path.with_suffix(".json.tmp")
        with tmp.open("w", encoding="utf-8") as fh:
            json.dump(self.settings, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
        tmp.replace(self.settings_path)

    def add(self, entry: KnowledgeEntry) -> KnowledgeEntry:
        self.entries.append(entry)
        return entry

    def replace(self, entry: KnowledgeEntry) -> None:
        for i, existing in enumerate(self.entries):
            if existing.id == entry.id:
                self.entries[i] = entry
                return
        self.entries.append(entry)

    def remove(self, entry_id: str) -> bool:
        before = len(self.entries)
        self.entries = [e for e in self.entries if e.id != entry_id]
        return len(self.entries) != before

    def get(self, entry_id: str) -> KnowledgeEntry | None:
        for entry in self.entries:
            if entry.id == entry_id:
                return entry
        return None

    def categories(self) -> list[str]:
        seen: list[str] = []
        for entry in self.entries:
            cat = entry.category.strip()
            if cat and cat not in seen:
                seen.append(cat)
        return sorted(seen, key=str.lower)

    def export_json(self, path: Path) -> None:
        payload = {
            "version": 1,
            "entries": [e.to_dict() for e in self.entries],
        }
        with Path(path).open("w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=2)
            fh.write("\n")

    def import_json(self, path: Path, merge: bool = True) -> int:
        data, err = self._read_json(Path(path))
        if err:
            raise ValueError(err)
        incoming = self._parse_entries(data)
        if not merge:
            self.entries = incoming
            return len(incoming)
        existing_ids = {e.id for e in self.entries}
        added = 0
        for entry in incoming:
            if entry.id in existing_ids:
                entry.id = KnowledgeEntry().id
                existing_ids.add(entry.id)
            self.entries.append(entry)
            added += 1
        return added

    def _load_settings(self) -> dict:
        if not self.settings_path.exists():
            return {}
        data, _err = self._read_json(self.settings_path)
        return data if isinstance(data, dict) else {}

    def _parse_entries(self, data) -> list[KnowledgeEntry]:
        raw_list = []
        if isinstance(data, dict):
            raw_list = data.get("entries") or data.get("knowledge") or []
        elif isinstance(data, list):
            raw_list = data
        entries: list[KnowledgeEntry] = []
        if isinstance(raw_list, list):
            for item in raw_list:
                if isinstance(item, dict):
                    entries.append(KnowledgeEntry.from_dict(item))
        return entries

    def _read_json(self, path: Path) -> tuple[object | None, str]:
        try:
            text = path.read_text(encoding="utf-8")
            if not text.strip():
                return {"version": 1, "entries": []}, ""
            return json.loads(text), ""
        except json.JSONDecodeError as exc:
            return None, f"Invalid JSON in {path.name}: {exc}"
        except OSError as exc:
            return None, f"Cannot read {path.name}: {exc}"

    def _try_load_backups(self) -> bool:
        for name in (BACKUP_FILE, BACKUP_FILE_2, BACKUP_FILE_3):
            candidate = self.data_dir / name
            if not candidate.exists():
                continue
            data, err = self._read_json(candidate)
            if err:
                continue
            self._quarantine(self.data_path)
            self.entries = self._parse_entries(data)
            self.last_error = f"Loaded backup {name} because knowledge.json was invalid."
            return True
        return False

    def _quarantine(self, path: Path) -> None:
        if not path.exists():
            return
        dest = self.data_dir / CORRUPTED_FILE
        try:
            shutil.copy2(path, dest)
        except OSError:
            pass

    def _rotate_backups(self) -> None:
        b1 = self.data_dir / BACKUP_FILE
        b2 = self.data_dir / BACKUP_FILE_2
        b3 = self.data_dir / BACKUP_FILE_3
        try:
            if b2.exists():
                b2.replace(b3)
            if b1.exists():
                b1.replace(b2)
            shutil.copy2(self.data_path, b1)
        except OSError:
            pass


def migrate_legacy_knowledge(dest: Path) -> None:
    """Copy old %APPDATA%\\KnowledgeLookup files into QuickText folder. Never delete source."""
    import os
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    appdata = os.environ.get("APPDATA")
    if os.name == "nt" and appdata:
        src = Path(appdata) / "KnowledgeLookup"
    else:
        src = Path.home() / ".local" / "share" / "KnowledgeLookup"
    if not src.exists() or src.resolve() == dest.resolve():
        return
    mapping = {
        "knowledge.json": dest / "knowledge.json",
        "settings.json": dest / "knowledge-settings.json",
        "knowledge.backup.json": dest / "knowledge.backup.json",
    }
    for name, target in mapping.items():
        origin = src / name
        if origin.exists() and not target.exists():
            try:
                shutil.copy2(origin, target)
                log.info("Migrated %s -> %s", origin, target)
            except OSError as exc:
                log.warning("Migration skipped %s: %s", origin, exc)
