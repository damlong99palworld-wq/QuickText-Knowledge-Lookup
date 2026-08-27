from __future__ import annotations

import sys
import time

IS_WIN = sys.platform == "win32"

if IS_WIN:
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

    user32.GetForegroundWindow.restype = wintypes.HWND
    user32.SetForegroundWindow.argtypes = [wintypes.HWND]
    user32.SetForegroundWindow.restype = wintypes.BOOL
    user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
    user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    user32.GetWindowThreadProcessId.restype = wintypes.DWORD
    user32.AttachThreadInput.argtypes = [wintypes.DWORD, wintypes.DWORD, wintypes.BOOL]
    user32.AttachThreadInput.restype = wintypes.BOOL
    kernel32.GetCurrentThreadId.restype = wintypes.DWORD
    user32.BringWindowToTop.argtypes = [wintypes.HWND]
    user32.IsIconic.argtypes = [wintypes.HWND]
    user32.IsIconic.restype = wintypes.BOOL
    SW_RESTORE = 9
else:
    user32 = None  # type: ignore


def get_foreground_hwnd() -> int:
    if not IS_WIN:
        return 0
    return int(user32.GetForegroundWindow() or 0)


def restore_foreground(hwnd: int, retries: int = 8) -> bool:
    if not IS_WIN or not hwnd:
        return False
    pid = wintypes.DWORD()
    fg = user32.GetForegroundWindow()
    fg_thread = user32.GetWindowThreadProcessId(fg, ctypes.byref(pid))
    target_thread = user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    cur = kernel32.GetCurrentThreadId()
    attached_fg = False
    attached_tg = False
    try:
        if fg_thread and fg_thread != cur:
            attached_fg = bool(user32.AttachThreadInput(cur, fg_thread, True))
        if target_thread and target_thread != cur:
            attached_tg = bool(user32.AttachThreadInput(cur, target_thread, True))
        if user32.IsIconic(hwnd):
            user32.ShowWindow(hwnd, SW_RESTORE)
        user32.BringWindowToTop(hwnd)
        for _ in range(retries):
            if user32.SetForegroundWindow(hwnd):
                if int(user32.GetForegroundWindow() or 0) == hwnd:
                    return True
            time.sleep(0.03)
        return int(user32.GetForegroundWindow() or 0) == hwnd
    finally:
        if attached_tg:
            user32.AttachThreadInput(cur, target_thread, False)
        if attached_fg:
            user32.AttachThreadInput(cur, fg_thread, False)


def send_ctrl_v() -> None:
    if not IS_WIN:
        return
    KEYEVENTF_KEYUP = 0x0002
    VK_CONTROL = 0x11
    VK_V = 0x56
    user32.keybd_event(VK_CONTROL, 0, 0, 0)
    user32.keybd_event(VK_V, 0, 0, 0)
    time.sleep(0.01)
    user32.keybd_event(VK_V, 0, KEYEVENTF_KEYUP, 0)
    user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)
