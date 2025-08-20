# Elite-Parser

PC-side log/status parser for Elite Dangerous. Publishes events and telemetry to MQTT and/or Serial, and listens for inbound commands (e.g., toggle lights) with safe, foreground-only key injection.

## Features
- Parses `Journal*.log`, `Status.json`, `ModulesInfo.json`, `JournalLoadoutCache.json`
- MQTT out: `elite/events/<Type>` (e.g., `FSDJump`, `StatusDelta`)
- MQTT in: `elite/cmd/#` → mapped keys via `keymap.toml`
- Strict safety: requires Elite to be foreground before injecting
- Optional Windows tray app for start/stop + settings

## Quick Start
```bash
git clone https://github.com/<you>/Elite-Parser.git
cd Elite-Parser
python -m venv .venv && .venv\\Scripts\\activate
pip install -r requirements.txt
copy config.example.toml config.toml
copy keymap.example.toml keymap.toml
# edit config.toml → set elite_dir, broker, etc.

# Run parser
python edpit.py

# (Optional) Tray app
python tray_app.py
