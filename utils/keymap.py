# utils/keymap.py
# SPDX-License-Identifier: MIT
from __future__ import annotations
import pathlib
from typing import Dict, Any
from utils.config import get
try:
    import tomllib  # py311+
except ModuleNotFoundError:
    import tomli as tomllib  # type: ignore

_CACHE: Dict[str, str] | None = None
_MTIME: float | None = None

def _read_bytes_strip_bom(p: pathlib.Path) -> bytes:
    data = p.read_bytes()
    if data.startswith(b"\xef\xbb\xbf"):
        data = data[3:]
    return data

def load_keymap(force: bool = False) -> Dict[str, str]:
    global _CACHE, _MTIME
    if not force and _CACHE is not None:
        return _CACHE
    path = pathlib.Path(get("general.keymap_file", "keymap.toml"))
    if not path.exists():
        _CACHE, _MTIME = {}, None
        return _CACHE
    mt = path.stat().st_mtime
    if not force and _MTIME == mt and _CACHE is not None:
        return _CACHE
    data = _read_bytes_strip_bom(path)
    doc: Dict[str, Any] = tomllib.loads(data.decode("utf-8"))
    # We store everything under [keymap]
    km = doc.get("keymap", {})
    # Filter out blank/unset entries
    result: Dict[str, str] = {topic: key for topic, key in km.items() if isinstance(key, str) and key}
    _CACHE, _MTIME = result, mt
    return result

def resolve(topic: str) -> str | None:
    return load_keymap().get(topic)
