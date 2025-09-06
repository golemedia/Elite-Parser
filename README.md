<!-- CI on main -->
![CI](https://github.com/golemedia/Elite-Parser/actions/workflows/ci.yml/badge.svg?branch=main)
<!-- License (reads your LICENSE file) -->
[![License](https://img.shields.io/github/license/golemedia/Elite-Parser)](LICENSE)
<!-- Python versions you test in CI (static) -->
![Python](https://img.shields.io/badge/python-3.10%20|%203.11%20|%203.12-blue?logo=python)
<!-- Code style + linter you actually use -->
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
![Linter: ruff](https://img.shields.io/badge/linter-ruff-46a?logo=python)
<!-- Platform reality -->
![Platform](https://img.shields.io/badge/platform-Windows-0078D6?logo=windows)

# Elite-Parser

### *Real-time Telemetry + Control for Elite Dangerous (MQTT + Tray App, Python)*

### **Why I built it -** 
I wanted cockpit-level immersion without hacks. **Elite Dangerous** exposes rich local logs, so I built a tiny Python service that turns those files into structured events I can wire into hardware and bots. 

### **What it does (today) -** 

- Watches Elite logs/status for state changes (landing gear, shields, location, comms).

- Publishes outbound events to `elite/events/<Type>` and accepts inbound commands via MQTT/serial to trigger keymaps.

- Optional system tray app for start/stop + config. [](https://github.com/golemedia/Elite-Parser)


### Features - 

- Parses `Journal*.log`, `Status.json`, `ModulesInfo.json`, `JournalLoadoutCache.json`
- MQTT out: `elite/events/<Type>` (e.g., `FSDJump`, `StatusDelta`)
- MQTT in: `elite/cmd/#` → mapped keys via `keymap.toml`
- Strict safety: requires Elite to be foreground before injecting
- Optional Windows tray app for start/stop + settings

### Quick Start - 

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
```

### **Where this goes next -** 

- Integrate **Home Assistant** and an embedded MQTT broker.
- Expand GUI config; harden PBKAC by default (safe focus checks).
- Tie into my **GLaDOS** assistant for voice commands and status callouts. (Yes, with attitude.) [](https://www.golemedia.net/blog/2025/08/elite-parser/)
