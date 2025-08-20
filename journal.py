import json
import os
from utils.serial_output import format_packet, send_to_serial
from loadout import process_loadout_event
from utils.mqtt_output import publish_packet, start as mqtt_start
from utils.config import get

mqtt_start()

WATCHED_EVENTS = {
    "Fileheader", "LoadGame", "Shutdown", "Location", "StartJump", "FSDJump",
    "SupercruiseEntry", "SupercruiseExit", "Docked", "Undocked", "ApproachBody",
    "Touchdown", "Liftoff", "HullDamage", "HeatWarning", "ShieldState", "FuelScoop",
    "ReceiveText"  # handled by shipcomms.py but included in watch filter
}

ELITE_DIR = os.path.normpath(get("general.elite_dir"))
JOURNAL_DIR = ELITE_DIR


_last_journal_file = None
_last_position = 0

def get_latest_journal_file():
    try:
        files = [f for f in os.listdir(JOURNAL_DIR) if f.startswith("Journal") and f.endswith(".log")]
    except OSError as e:
        print(f"[JOURNAL] Cannot list dir '{JOURNAL_DIR}': {e}")
        return None
    if not files:
        return None
    files.sort(reverse=True)
    return os.path.join(JOURNAL_DIR, files[0])

def process_journal_file():
    global _last_journal_file, _last_position
    journal_file = get_latest_journal_file()
    if not journal_file:
        print("[JOURNAL] No journal file found.")
        return

    if journal_file != _last_journal_file:
        print(f"[JOURNAL] Switching to new journal file: {journal_file}")
        _last_journal_file = journal_file
        _last_position = 0

    try:
        with open(journal_file, "r", encoding="utf-8") as f:
            f.seek(_last_position)
            lines = f.readlines()
            _last_position = f.tell()
    except Exception as e:
        print(f"[JOURNAL] Failed to read journal file: {e}")
        return

    for line in lines:
        try:
            entry = json.loads(line)  # parse ONCE
        except json.JSONDecodeError:
            print(f"[JOURNAL] Failed to parse JSON: {line.strip()}")
            continue

        # loadout handling
        process_loadout_event(entry)

        event_type = entry.get("event")
        if event_type in WATCHED_EVENTS:
            if event_type == "ReceiveText":
                continue  # shipcomms handles it
            print(f"WATCH[{event_type}]")
            packet = format_packet("journal", event_type, entry)
            send_to_serial(packet)
            publish_packet(packet)
        else:
            print(f"RAW >> {line.strip()}")