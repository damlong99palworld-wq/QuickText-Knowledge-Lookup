from __future__ import annotations

import json
import shutil
from pathlib import Path

from models.snippet import AppData

APP_NAME = "QuickText"


def data_dir() -> Path:
    import os

    appdata = os.environ.get("APPDATA")
    root = Path(appdata) / APP_NAME if appdata else Path.home() / ".quicktext"
    (root / "backups").mkdir(parents=True, exist_ok=True)
    return root


def snippets_path() -> Path:
    return data_dir() / "snippets.json"


def settings_path() -> Path:
    return data_dir() / "settings.json"


def _rotate(path: Path) -> None:
    bdir = data_dir() / "backups"
    bdir.mkdir(parents=True, exist_ok=True)
    name = path.name
    slots = [bdir / f"{name}.{i}.bak" for i in (3, 2, 1)]
    a, b, c = slots[0], slots[1], slots[2]
    if b.exists():
        shutil.copy2(b, a)
    if c.exists():
        shutil.copy2(c, b)
    if path.exists():
        shutil.copy2(path, c)


def _read_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("root is not an object")
    return data


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    _rotate(path)
    tmp.replace(path)


def load_data(default_file: Path) -> AppData:
    snippets_raw: dict | None = None
    settings_raw: dict | None = None
    candidates = [
        snippets_path(),
        data_dir() / "backups" / "snippets.json.1.bak",
        data_dir() / "backups" / "snippets.json.2.bak",
        default_file,
    ]
    for cand in candidates:
        if not cand.exists():
            continue
        try:
            snippets_raw = _read_json(cand)
            if cand == snippets_path():
                break
        except Exception:
            if cand == snippets_path():
                try:
                    shutil.copy2(cand, data_dir() / "snippets.corrupted.json")
                except OSError:
                    pass
    try:
        if settings_path().exists():
            settings_raw = _read_json(settings_path())
    except Exception:
        settings_raw = None

    if snippets_raw is None:
        if default_file.exists():
            try:
                snippets_raw = _read_json(default_file)
            except Exception:
                snippets_raw = {}
        else:
            snippets_raw = {}

    if settings_raw:
        snippets_raw = {**snippets_raw, "settings": settings_raw}
    return AppData.from_dict(snippets_raw)


def save_data(data: AppData) -> None:
    blob = data.to_dict()
    settings = blob.pop("settings")
    _write_json(snippets_path(), blob)
    _write_json(settings_path(), settings)
