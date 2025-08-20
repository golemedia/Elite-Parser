# SPDX-License-Identifier: MIT
# Elite-Parser — System Tray Host & Settings
# Requires: PySide6, psutil (already in project), tomli/tomllib, optional tomli_w for saving TOML
# Run: python tray_app.py

from __future__ import annotations
import os
import sys
import subprocess
import signal
import time
from pathlib import Path
from typing import Optional
import psutil

from PySide6 import QtCore, QtGui, QtWidgets

# Project-local config helpers
try:
    from utils.config import load_config, reload_config, get
except Exception:
    # Allow running tray from other working dirs
    sys.path.append(str(Path(__file__).parent))
    from utils.config import load_config, reload_config, get  # type: ignore

# Optional dependency for saving TOML nicely
try:
    import tomli_w  # pip install tomli-w
except Exception:
    tomli_w = None

APP_NAME = "Elite-Parser Tray"
REPO_ROOT = Path(__file__).resolve().parent
CONFIG_PATH = REPO_ROOT / "config.toml"

class ParserProcess(QtCore.QObject):
    state_changed = QtCore.Signal(bool)  # running?

    def __init__(self, parent=None):
        super().__init__(parent)
        self._proc: Optional[subprocess.Popen] = None
        self._last_start = 0.0

    def start(self):
        if self.is_running():
            return
        # Ensure config exists
        if not CONFIG_PATH.exists():
            QtWidgets.QMessageBox.critical(None, APP_NAME, f"Missing config.toml at\n{CONFIG_PATH}")
            return
        # Launch edpit.py in unbuffered mode so logs stream
        cmd = [sys.executable, "-u", str(REPO_ROOT / "edpit.py")]
        try:
            self._proc = subprocess.Popen(cmd, cwd=str(REPO_ROOT))
            self._last_start = time.time()
            self.state_changed.emit(True)
        except Exception as e:
            QtWidgets.QMessageBox.critical(None, APP_NAME, f"Failed to start parser:\n{e}")
            self._proc = None
            self.state_changed.emit(False)

    def stop(self):
        if not self.is_running():
            return
        try:
            if os.name == "nt":
                self._proc.terminate()
            else:
                self._proc.terminate()
            self._proc.wait(timeout=3)
        except Exception:
            try:
                self._proc.kill()
            except Exception:
                pass
        
        self._proc = None
        self.state_changed.emit(False)

    def is_running(self) -> bool:
        return self._proc is not None and (self._proc.poll() is None)

    

class SettingsDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Elite-Parser Settings")
        self.setMinimumWidth(420)

        # Load current config
        cfg = load_config(str(CONFIG_PATH))

        # Widgets
        self.broker = QtWidgets.QLineEdit(str(get("outputs.mqtt.broker", "127.0.0.1")))
        self.port = QtWidgets.QSpinBox()
        self.port.setRange(1, 65535)
        self.port.setValue(int(get("outputs.mqtt.port", 1883)))

        self.base_topic = QtWidgets.QLineEdit(str(get("general.base_topic", "elite")))
        self.cmd_topic = QtWidgets.QLineEdit(str(get("inputs.mqtt.cmd_topic", f"{self.base_topic.text()}/cmd/#")))

        self.elite_dir = QtWidgets.QLineEdit(str(get("general.elite_dir", "")))
        self.require_fg = QtWidgets.QCheckBox("Require Elite foreground for commands (strict)")
        self.require_fg.setChecked(bool(get("safety.require_foreground", True)))
        self.rate_limit = QtWidgets.QSpinBox()
        self.rate_limit.setRange(0, 120)
        self.rate_limit.setValue(int(get("safety.rate_limit_hz", 5)))

        form = QtWidgets.QFormLayout()
        form.addRow("MQTT broker", self.broker)
        form.addRow("MQTT port", self.port)
        form.addRow("Base topic", self.base_topic)
        form.addRow("Command topic", self.cmd_topic)
        form.addRow("Elite logs dir", self.elite_dir)
        form.addRow(self.require_fg)
        form.addRow("Rate limit (Hz)", self.rate_limit)

        self.save_btn = QtWidgets.QPushButton("Save")
        self.cancel_btn = QtWidgets.QPushButton("Cancel")
        btns = QtWidgets.QHBoxLayout()
        btns.addStretch(1)
        btns.addWidget(self.cancel_btn)
        btns.addWidget(self.save_btn)

        lay = QtWidgets.QVBoxLayout(self)
        lay.addLayout(form)
        lay.addStretch(1)
        lay.addLayout(btns)

        self.cancel_btn.clicked.connect(self.reject)
        self.save_btn.clicked.connect(self._on_save)

    def _on_save(self):
        # Reload, mutate fields, write back
        if tomli_w is None:
            QtWidgets.QMessageBox.warning(self, APP_NAME, "Saving requires 'tomli-w' (pip install tomli-w).\nSettings not saved.")
            return
        cfg = load_config(str(CONFIG_PATH))
        # mutate
        cfg.setdefault("outputs", {}).setdefault("mqtt", {})
        cfg["outputs"]["mqtt"]["broker"] = self.broker.text().strip()
        cfg["outputs"]["mqtt"]["port"] = int(self.port.value())
        cfg.setdefault("general", {})
        cfg["general"]["base_topic"] = self.base_topic.text().strip()
        cfg.setdefault("inputs", {}).setdefault("mqtt", {})
        cfg["inputs"]["mqtt"]["cmd_topic"] = self.cmd_topic.text().strip()
        cfg["general"]["elite_dir"] = self.elite_dir.text().strip()
        cfg.setdefault("safety", {})
        cfg["safety"]["require_foreground"] = bool(self.require_fg.isChecked())
        cfg["safety"]["rate_limit_hz"] = int(self.rate_limit.value())

        # Write TOML
        try:
            with open(CONFIG_PATH, "wb") as f:
                f.write(tomli_w.dumps(cfg).encode("utf-8"))
            reload_config(str(CONFIG_PATH))
            QtWidgets.QMessageBox.information(self, APP_NAME, "Settings saved.")
            self.accept()
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, APP_NAME, f"Failed to save config:\n{e}")

class TrayApp(QtWidgets.QSystemTrayIcon):
    def __init__(self):
        super().__init__()
        self.setToolTip(APP_NAME)
        self.proc = ParserProcess()
        self.proc.state_changed.connect(self._on_state)

        # Build menu
        menu = QtWidgets.QMenu()
        self.action_start = menu.addAction("Start Parser")
        self.action_stop = menu.addAction("Stop Parser")
        menu.addSeparator()
        self.action_settings = menu.addAction("Settings…")
        self.action_open_cfg = menu.addAction("Open config folder…")
        menu.addSeparator()
        self.action_quit = menu.addAction("Quit")
        self.setContextMenu(menu)

        self.action_start.triggered.connect(self.proc.start)
        self.action_stop.triggered.connect(self.proc.stop)
        self.action_settings.triggered.connect(self.open_settings)
        self.action_open_cfg.triggered.connect(lambda: QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(str(REPO_ROOT))))
        self.action_quit.triggered.connect(self._quit)

        # Status timer to update icon + optional log tail
        self._timer = QtCore.QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(500)

        self._set_icon_running(False)
        self.show()

    # --- Icons ---
    def _make_dot(self, color: QtGui.QColor) -> QtGui.QIcon:
        pix = QtGui.QPixmap(22, 22)
        pix.fill(QtCore.Qt.transparent)
        p = QtGui.QPainter(pix)
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        p.setBrush(QtGui.QBrush(color))
        p.setPen(QtCore.Qt.NoPen)
        p.drawEllipse(3, 3, 16, 16)
        p.end()
        return QtGui.QIcon(pix)

    def _set_icon_running(self, running: bool):
        self.setIcon(self._make_dot(QtGui.QColor("#2ecc71" if running else "#95a5a6")))

    # --- Slots ---
    def _on_state(self, running: bool):
        self._set_icon_running(running)

    def _tick(self):
        auto = bool(get("general.auto_activate", True))
        game_up = self._game_running()
        running = self.proc.is_running()

        if auto:
            if game_up and not running:
                self.proc.start()
            elif not game_up and running:
                self.proc.stop()

        # keep icon in sync regardless
        self._set_icon_running(self.proc.is_running())
        

    def open_settings(self):
        was_running = self.proc.is_running()
        if was_running:
            # Stop while editing to avoid races
            self.proc.stop()
        dlg = SettingsDialog()
        if dlg.exec() == QtWidgets.QDialog.Accepted:
            # After saving, user may want to restart
            pass
        if was_running:
            self.proc.start()

    def _quit(self):
        self.proc.stop()
        QtWidgets.QApplication.quit()

    def _game_running(self) -> bool:
        target = get("general.process_name", "EliteDangerous64.exe").lower()
        for p in psutil.process_iter(["name"]):
            try:
                if p.info.get("name", "").lower() == target:
                    return True
            except psutil.Error:
                continue
        return False

def main():
    app = QtWidgets.QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    tray = TrayApp()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
