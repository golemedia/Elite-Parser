# utils/command_router.py
# SPDX-License-Identifier: MIT
from __future__ import annotations

import time
from typing import Any

from utils.config import get
from utils.keymap import load_keymap
from utils.keymap import resolve as resolve_key
from utils.keys_win import press_key
from utils.win_focus import is_process_foreground

keymap = load_keymap()

_last_ts: dict[str, float] = {}


def _within_rate(topic: str, hz: float) -> bool:
    if hz <= 0:
        return True
    now = time.time()
    min_dt = 1.0 / hz
    last = _last_ts.get(topic, 0.0)
    if now - last < min_dt:
        return False
    _last_ts[topic] = now
    return True


def handle_inbound_command(topic: str, payload: Any) -> None:
    key = resolve_key(topic)
    if not key:
        print(f"[CMD] {topic} -> (no key mapping) payload={payload!r}")
        return

    # Strict safety — require Elite foreground; never force focus
    proc_name = get("general.process_name", "EliteDangerous64.exe")
    require_foreground = True  # strict only
    if require_foreground and not is_process_foreground(proc_name):
        print(f"[CMD] {topic} -> Elite not foreground; skipping")
        return

    # Rate limit
    hz = float(get("safety.rate_limit_hz", 5))
    if not _within_rate(topic, hz):
        print(f"[CMD] {topic} -> rate-limited")
        return

    # Optional action hint (we ignore for now; can use payload later)
    # action = payload.get("action","press") if isinstance(payload, dict) else "press"
    ok = press_key(key, hold_ms=80)
    print(f"[CMD] {topic} -> PRESS '{key}' status={'ok' if ok else 'fail'} (payload={payload!r})")
