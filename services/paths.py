"""Resolve bundled files in source mode and PyInstaller onefile (_MEIPASS)."""

from __future__ import annotations

import sys
from pathlib import Path


def resource_dir() -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent.parent


def resource_path(*parts: str) -> Path:
    path = resource_dir()
    for part in parts:
        path = path / part
    return path
