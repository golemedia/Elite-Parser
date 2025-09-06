import os
import sys
import threading
import time

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from journal import process_journal_file
from modules import process_modules_file
from status import process_status_file
from utils.command_router import handle_inbound_command
from utils.config import get, load_config
from utils.keymap import load_keymap
from utils.mqtt_output import set_command_handler
from utils.mqtt_output import start as mqtt_start

# === Paths ===
ELITE_DIR = get("general.elite_dir")
WATCH_DIR = ELITE_DIR

if not os.path.isdir(WATCH_DIR):
    print(f"[ELITEPARSER] ERROR: 'general.elite_dir' does not exist:\n  {WATCH_DIR}")
    print("        Fix this in config.toml, then rerun.")
    sys.exit(1)

TARGET_FILES = {
    "Status.json": process_status_file,
    "ModulesInfo.json": process_modules_file,
}


def _log_command(topic: str, payload):
    print(f"[CMD] {topic} -> {payload}")


load_config("config.toml")
load_keymap(force=True)
mqtt_start()
set_command_handler(handle_inbound_command)


# === Journal needs a timer/loop because of dynamic filenames ===
def journal_loop():
    interval = max(int(get("general.poll_interval_ms", 500)), 50) / 1000.0
    while True:
        process_journal_file()
        time.sleep(interval)


# === Watchdog Handler ===
class EDFileHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if not event.is_directory:
            filename = os.path.basename(event.src_path)
            if filename in TARGET_FILES:
                TARGET_FILES[filename]()


# === Launch ===
def main():
    print("[ELITEPARSER] Starting telemetry monitor...")

    # Start journal file polling thread
    journal_thread = threading.Thread(target=journal_loop, daemon=True)
    journal_thread.start()

    # Start watchdog for status and modules
    event_handler = EDFileHandler()
    observer = Observer()
    observer.schedule(event_handler, WATCH_DIR, recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()


if __name__ == "__main__":
    main()
