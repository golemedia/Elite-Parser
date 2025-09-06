# utils/config.py
# SPDX-License-Identifier: MIT
from __future__ import annotations

import os
import pathlib
from typing import Any

# Python 3.11+ has tomllib in stdlib; fallback to tomli if needed
try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore

DEFAULTS: dict[str, Any] = {
    "general": {
        "elite_dir": r"C:\Users\Public\Saved Games\Frontier Developments\Elite Dangerous",
        "only_when_game_running": True,
        "process_name": "EliteDangerous64.exe",
        "poll_interval_ms": 500,
        "base_topic": "elite",
    },
    "outputs": {
        "mqtt": {
            "enabled": True,
            "broker": "127.0.0.1",
            "port": 1883,
            "username": "",
            "password": "",
            "qos": 0,
            "retain": False,
        },
        "serial": {
            "enabled": False,
            "port": "COM6",
            "baud": 115200,
            "newline_delimited_json": True,
        },
    },
    "inputs": {
        "mqtt": {
            "enabled": True,
            "cmd_topic": "elite/cmd/#",
        },
        "serial": {
            "enabled": False,
            "port": "COM6",
            "baud": 115200,
        },
    },
    "keymap": {},
}

_cfg: dict[str, Any] | None = None


def _deep_merge(dst: dict[str, Any], src: dict[str, Any]) -> dict[str, Any]:
    for k, v in src.items():
        if isinstance(v, dict) and isinstance(dst.get(k), dict):
            _deep_merge(dst[k], v)  # type: ignore
        else:
            dst[k] = v
    return dst


def load_config(path: str | os.PathLike = "config.toml") -> dict[str, Any]:
    """Load TOML config and merge with defaults. Idempotent."""
    global _cfg
    if _cfg is not None:
        return _cfg
    cfg = {k: (v.copy() if isinstance(v, dict) else v) for k, v in DEFAULTS.items()}

    # utils/config.py (inside load_config)
    p = pathlib.Path(path)
    if p.exists():
        data = p.read_bytes()
        # Strip UTF-8 BOM if present
        if data.startswith(b"\xef\xbb\xbf"):
            data = data[3:]
        try:
            file_cfg = tomllib.loads(data.decode("utf-8"))
        except Exception as e:
            # Helpful diagnostics: show first bytes
            preview = data[:40]
            raise RuntimeError(
                f"TOML parse failed for {p}.\n"
                f"Tip: ensure UTF-8 (no BOM). First bytes: {preview!r}\n"
                f"Original error: {e}"
            ) from e
        _deep_merge(cfg, file_cfg)

    # ENV overrides (useful for secrets/CI)
    # ELITE_MQTT_HOST, ELITE_MQTT_PORT, ELITE_MQTT_USER, ELITE_MQTT_PASS, ELITE_BASE_TOPIC
    mqtt_out = cfg["outputs"]["mqtt"]
    mqtt_out["broker"] = os.getenv("ELITE_MQTT_HOST", mqtt_out["broker"])
    mqtt_out["port"] = int(os.getenv("ELITE_MQTT_PORT", mqtt_out["port"]))
    mqtt_out["username"] = os.getenv("ELITE_MQTT_USER", mqtt_out["username"])
    mqtt_out["password"] = os.getenv("ELITE_MQTT_PASS", mqtt_out["password"])

    cfg["general"]["base_topic"] = os.getenv("ELITE_BASE_TOPIC", cfg["general"]["base_topic"])

    _cfg = cfg
    return cfg


def get(path: str, default: Any = None) -> Any:
    """
    Dot-path getter, e.g. get('outputs.mqtt.broker')
    """
    cfg = load_config()
    node: Any = cfg
    for part in path.split("."):
        if not isinstance(node, dict):
            return default
        node = node.get(part, default)
    return node


def reload_config(path: str | os.PathLike = "config.toml") -> dict[str, Any]:
    """Clear cache and reload (for future GUI hot-reload)."""
    global _cfg
    _cfg = None
    return load_config(path)
