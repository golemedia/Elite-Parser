# utils/keys_win.py
# SPDX-License-Identifier: MIT
from __future__ import annotations

import ctypes
import time

user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

# ---- Win32 constants
INPUT_KEYBOARD = 1
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_SCANCODE = 0x0008
# KEYEVENTF_EXTENDEDKEY = 0x0001  # for arrows, numpad, etc.

# Basic VK map; extend as needed
VK = {
    "l": 0x4C,  # L
    "g": 0x47,  # G
    "u": 0x55,  # U
}

# ---- ctypes types (avoid wintypes.ULONG_PTR; use size_t instead)
ULONG_PTR = ctypes.c_size_t
DWORD = ctypes.c_uint32
WORD = ctypes.c_ushort

# MapVirtualKeyW setup
MapVirtualKeyW = user32.MapVirtualKeyW
MapVirtualKeyW.argtypes = (UINT := ctypes.c_uint, UINT)
MapVirtualKeyW.restype = UINT

# SendInput setup
SendInput = user32.SendInput
SendInput.argtypes = (UINT, ctypes.c_void_p, ctypes.c_int)
SendInput.restype = UINT

FormatMessageW = kernel32.FormatMessageW
FormatMessageW.argtypes = (
    DWORD,
    ctypes.c_void_p,
    DWORD,
    DWORD,
    ctypes.c_wchar_p,
    DWORD,
    ctypes.c_void_p,
)
FormatMessageW.restype = DWORD


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", WORD),
        ("wScan", WORD),
        ("dwFlags", DWORD),
        ("time", DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", DWORD),
        ("dy", DWORD),
        ("mouseData", DWORD),
        ("dwFlags", DWORD),
        ("time", DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [("uMsg", DWORD), ("wParamL", WORD), ("wParamH", WORD)]


class _INPUTUNION(ctypes.Union):
    _fields_ = [("ki", KEYBDINPUT), ("mi", MOUSEINPUT), ("hi", HARDWAREINPUT)]


class INPUT(ctypes.Structure):
    _anonymous_ = ("u",)
    _fields_ = [("type", DWORD), ("u", _INPUTUNION)]


def _last_error_msg() -> str:
    err = ctypes.get_last_error()
    if not err:
        return "GetLastError=0"
    buf = ctypes.create_unicode_buffer(512)
    #    FM_ALLOCATE_BUFFER   = 0x00000100
    FM_FROM_SYSTEM = 0x00001000
    # Use a stack buffer version to avoid LocalFree bookkeeping
    FormatMessageW(FM_FROM_SYSTEM, None, err, 0, buf, len(buf), None)
    return f"{err}: {buf.value.strip()}"


def _send_input(inputs: list[INPUT]) -> bool:
    n = len(inputs)
    arr = (INPUT * n)(*inputs)
    sent = SendInput(n, ctypes.byref(arr), ctypes.sizeof(INPUT))
    if sent != n:
        print(f"[KEYS] SendInput failed ({sent}/{n}) :: {_last_error_msg()}")
        return False
    return True


def press_key(letter: str, hold_ms: int = 60) -> bool:
    """Press and release a key using scan codes (preferred by games)."""
    vk = VK.get(letter.lower())
    if vk is None:
        print(f"[KEYS] Unknown key '{letter}'")
        return False

    # MAPVK_VK_TO_VSC = 0
    sc = MapVirtualKeyW(vk, 0)
    if sc == 0:
        print(f"[KEYS] MapVirtualKey failed for '{letter}' (vk={vk})")
        return False

    down = INPUT(type=INPUT_KEYBOARD, ki=KEYBDINPUT(0, sc, KEYEVENTF_SCANCODE, 0, 0))
    up = INPUT(
        type=INPUT_KEYBOARD, ki=KEYBDINPUT(0, sc, KEYEVENTF_SCANCODE | KEYEVENTF_KEYUP, 0, 0)
    )

    if not _send_input([down]):
        return False
    time.sleep(max(hold_ms, 1) / 1000.0)
    return _send_input([up])
