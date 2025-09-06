# utils/win_focus.py
# SPDX-License-Identifier: MIT
from __future__ import annotations

import ctypes
import ctypes.wintypes as wt

import psutil

user32 = ctypes.WinDLL("user32", use_last_error=True)
GetForegroundWindow = user32.GetForegroundWindow
GetWindowThreadProcessId = user32.GetWindowThreadProcessId
SetForegroundWindow = user32.SetForegroundWindow


def _pid_of_hwnd(hwnd: int) -> int | None:
    pid = wt.DWORD()
    GetWindowThreadProcessId(wt.HWND(hwnd), ctypes.byref(pid))
    return pid.value or None


def is_process_foreground(process_name: str) -> bool:
    """Return True if the foreground window belongs to process_name."""
    hwnd = GetForegroundWindow()
    if not hwnd:
        return False
    pid = _pid_of_hwnd(hwnd)
    if not pid:
        return False
    try:
        p = psutil.Process(pid)
        return p.name().lower() == process_name.lower()
    except psutil.Error:
        return False


def try_focus_process(process_name: str) -> bool:
    """
    Best-effort: find a top-level window for process_name and bring it to front.
    Very minimal (no enumeration) to keep scope tight; returns False if not found.
    """
    # Light-weight approach: scan processes with matching name and try their main window
    for p in psutil.process_iter(["name", "pid"]):
        if p.info.get("name", "").lower() == process_name.lower():
            try:
                # Return focus status directly; conservative: do not force focus
                return is_process_foreground(process_name)
            except psutil.Error:
                continue  # keep if this is inside a loop; otherwise, use `return False`

    return False
