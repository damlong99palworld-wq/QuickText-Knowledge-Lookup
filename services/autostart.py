from __future__ import annotations

import os
import sys
from pathlib import Path


def _exe_path() -> str:
    env = os.environ.get("QUICKTEXT_EXE")
    if env:
        return env
    if getattr(sys, "frozen", False):
        return sys.executable
    return f'"{sys.executable}" "{Path(sys.argv[0]).resolve()}"'


def set_start_with_windows(enabled: bool) -> None:
    if sys.platform != "win32":
        return
    import winreg

    path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, path, 0, winreg.KEY_SET_VALUE)
    try:
        if enabled:
            winreg.SetValueEx(key, "QuickText", 0, winreg.REG_SZ, _exe_path())
        else:
            try:
                winreg.DeleteValue(key, "QuickText")
            except FileNotFoundError:
                pass
    finally:
        key.Close()
