import json
import os
#from edpit import ELITE_DIR
from utils.serial_output import format_packet, send_to_serial
from utils.mqtt_output import publish_packet, start as mqtt_start
from utils.config import get

mqtt_start()

ELITE_DIR = os.path.normpath(get("general.elite_dir"))
LOADOUT_FILE = os.path.join(ELITE_DIR, "JournalLoadoutCache.json")

_last_payload = None

def extract_module_summary(mod):
    summary = {
        "Slot": mod.get("Slot"),
        "Item": mod.get("Item"),
        "Health": mod.get("Health"),
        "Priority": mod.get("Priority"),
        "On": mod.get("On", False),
    }
    if "AmmoInClip" in mod or "AmmoInHopper" in mod:
        summary["AmmoInClip"] = mod.get("AmmoInClip", 0)
        summary["AmmoInHopper"] = mod.get("AmmoInHopper", 0)

    if "Engineering" in mod:
        eng = mod["Engineering"]
        summary["Engineering"] = {
            "Engineer": eng.get("Engineer"),
            "Blueprint": eng.get("BlueprintName"),
            "Level": eng.get("Level"),
            "Quality": eng.get("Quality"),
            "ExperimentalEffect": eng.get("ExperimentalEffect", None)
        }
    return summary

def process_loadout_event(event):
    global _last_payload
    if event.get("event") != "Loadout":
        return

    data = {
        "Ship": event.get("Ship"),
        "ShipID": event.get("ShipID"),
        "ShipName": event.get("ShipName", "").strip(),
        "ShipIdent": event.get("ShipIdent"),
        "HullHealth": event.get("HullHealth"),
        "MaxJumpRange": event.get("MaxJumpRange"),
        "Rebuy": event.get("Rebuy"),
        "CargoCapacity": event.get("CargoCapacity"),
        "Modules": [extract_module_summary(mod) for mod in event.get("Modules", [])]
    }

    if data != _last_payload:
        _last_payload = data
        print(f"[LOADOUT] Updated ship: {data['ShipIdent']} | Hull: {data['HullHealth']*100:.0f}%")
        packet = format_packet("loadout", "Loadout", data)
        send_to_serial(packet)
        publish_packet(packet)
    else:
        print("[LOADOUT] No change.")

