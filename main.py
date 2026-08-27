"""QuickText entry point. Double-click or: python main.py"""
from __future__ import annotations

import sys
import traceback
from pathlib import Path


def _log_crash(exc: BaseException) -> None:
    text = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    print(text, file=sys.stderr)
    try:
        log = Path(__file__).resolve().parent / "quicktext_error.log"
        log.write_text(text, encoding="utf-8")
        print(f"[QuickText] Error written to: {log}", file=sys.stderr)
    except Exception:
        pass
    try:
        from PySide6.QtWidgets import QApplication, QMessageBox

        app = QApplication.instance() or QApplication(sys.argv)
        QMessageBox.critical(None, "QuickText error", text[:2000])
    except Exception:
        pass


if __name__ == "__main__":
    try:
        from app import run

        run()
    except Exception as e:
        _log_crash(e)
        sys.exit(1)
