import os
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


def _load_runtime_config(path: str = "config.toml"):
    """Load configuration and validate required paths. Raise on problems."""
    # Ensure config is loaded before using `get(...)`
    load_config(path)
    elite_dir = get("general.elite_dir")
    if not os.path.isdir(elite_dir):
        msg = (
            "[ELITEPARSER] ERROR: 'general.elite_dir' does not exist:\n"
            f"  {elite_dir}\n"
            "        Fix this in config.toml, then rerun."
        )
        raise RuntimeError(msg)
    return elite_dir


TARGET_FILES = {
    "Status.json": process_status_file,
    "ModulesInfo.json": process_modules_file,
}


def _log_command(topic: str, payload):
    print(f"[CMD] {topic} -> {payload}")


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
def main(argv=None) -> int:
    print("[ELITEPARSER] Starting telemetry monitor...")

    try:
        watch_dir = _load_runtime_config("config.toml")
    except RuntimeError as e:
        print(e)
        return 1

    # Now that config is validated, do runtime setup
    load_keymap(force=True)
    mqtt_start()
    set_command_handler(handle_inbound_command)

    # Start journal file polling thread
    journal_thread = threading.Thread(target=journal_loop, daemon=True)
    journal_thread.start()

    # Start watchdog for status and modules
    event_handler = EDFileHandler()
    observer = Observer()
    observer.schedule(event_handler, watch_dir, recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()
    return 0


if __name__ == "__main__":
    main()
