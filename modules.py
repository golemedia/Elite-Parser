import json
import os
from utils.serial_output import format_packet, send_to_serial
from utils.mqtt_output import publish_packet, start as mqtt_start
from utils.config import get

mqtt_start()

ELITE_DIR = os.path.normpath(get("general.elite_dir"))
MODULES_FILE = os.path.join(ELITE_DIR, "ModulesInfo.json")

_last_module_data = None

def process_modules_file():
    global _last_module_data

    try:
        with open(MODULES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"[MODULES] Error reading modules file: {e}")
        return

    simplified = []
    for mod in data.get("Modules", []):
        simplified.append({
            "Slot": mod.get("Slot", "Unknown"),
            "Power": mod.get("Power", "Unknown"),
            "Priority": mod.get("Priority", "Unknown")
        })

    if simplified != _last_module_data:
        _last_module_data = simplified
        print(f"[MODULES] Modules updated ({len(simplified)} total)")
        packet = format_packet("modules", "ModulesSnapshot", simplified)
        send_to_serial(packet)
        publish_packet(packet)
    else:
        print("[MODULES] No changes detected.")
