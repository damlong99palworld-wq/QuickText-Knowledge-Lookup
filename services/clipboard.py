from __future__ import annotations

import sys
import time
from dataclasses import dataclass

IS_WIN = sys.platform == "win32"
CF_UNICODETEXT = 13
GMEM_MOVEABLE = 0x0002

if IS_WIN:
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

    user32.OpenClipboard.argtypes = [wintypes.HWND]
    user32.OpenClipboard.restype = wintypes.BOOL
    user32.CloseClipboard.restype = wintypes.BOOL
    user32.EmptyClipboard.restype = wintypes.BOOL
    user32.GetClipboardData.argtypes = [wintypes.UINT]
    user32.GetClipboardData.restype = wintypes.HANDLE
    user32.SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
    user32.SetClipboardData.restype = wintypes.HANDLE
    user32.EnumClipboardFormats.argtypes = [wintypes.UINT]
    user32.EnumClipboardFormats.restype = wintypes.UINT
    kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
    kernel32.GlobalAlloc.restype = wintypes.HGLOBAL
    kernel32.GlobalLock.argtypes = [wintypes.HGLOBAL]
    kernel32.GlobalLock.restype = wintypes.LPVOID
    kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
    kernel32.GlobalSize.argtypes = [wintypes.HGLOBAL]
    kernel32.GlobalSize.restype = ctypes.c_size_t


@dataclass
class ClipSnapshot:
    unicode_text: str | None
    blobs: list[tuple[int, bytes]]


def _open() -> bool:
    for _ in range(20):
        if user32.OpenClipboard(None):
            return True
        time.sleep(0.02)
    return False


def save() -> ClipSnapshot:
    if not IS_WIN:
        return ClipSnapshot(unicode_text=None, blobs=[])
    if not _open():
        return ClipSnapshot(unicode_text=None, blobs=[])
    try:
        text = None
        blobs: list[tuple[int, bytes]] = []
        fmt = 0
        while True:
            fmt = user32.EnumClipboardFormats(fmt)
            if not fmt:
                break
            handle = user32.GetClipboardData(fmt)
            if not handle:
                continue
            if fmt == CF_UNICODETEXT:
                ptr = kernel32.GlobalLock(handle)
                if ptr:
                    try:
                        text = ctypes.wstring_at(ptr)
                    finally:
                        kernel32.GlobalUnlock(handle)
                continue
            size = kernel32.GlobalSize(handle)
            ptr = kernel32.GlobalLock(handle)
            if not ptr or not size:
                continue
            try:
                blobs.append((fmt, ctypes.string_at(ptr, size)))
            finally:
                kernel32.GlobalUnlock(handle)
        return ClipSnapshot(unicode_text=text, blobs=blobs)
    finally:
        user32.CloseClipboard()


def set_text(text: str) -> bool:
    if not IS_WIN:
        return False
    if not _open():
        return False
    try:
        user32.EmptyClipboard()
        data = text.encode("utf-16-le") + b"\x00\x00"
        h = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(data))
        if not h:
            return False
        ptr = kernel32.GlobalLock(h)
        ctypes.memmove(ptr, data, len(data))
        kernel32.GlobalUnlock(h)
        if not user32.SetClipboardData(CF_UNICODETEXT, h):
            return False
        return True
    finally:
        user32.CloseClipboard()


def restore(snap: ClipSnapshot) -> None:
    if not IS_WIN:
        return
    if snap.unicode_text is None and not snap.blobs:
        return
    if not _open():
        return
    try:
        user32.EmptyClipboard()
        if snap.unicode_text is not None:
            data = snap.unicode_text.encode("utf-16-le") + b"\x00\x00"
            h = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(data))
            ptr = kernel32.GlobalLock(h)
            ctypes.memmove(ptr, data, len(data))
            kernel32.GlobalUnlock(h)
            user32.SetClipboardData(CF_UNICODETEXT, h)
        for fmt, blob in snap.blobs:
            if fmt == CF_UNICODETEXT:
                continue
            try:
                h = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(blob))
                ptr = kernel32.GlobalLock(h)
                ctypes.memmove(ptr, blob, len(blob))
                kernel32.GlobalUnlock(h)
                user32.SetClipboardData(fmt, h)
            except Exception:
                continue
    finally:
        user32.CloseClipboard()
