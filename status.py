import json
import os
from utils.serial_output import format_packet, send_to_serial
from utils.mqtt_output import publish_packet, start as mqtt_start
from utils.config import get


mqtt_start()


ELITE_DIR = os.path.normpath(get("general.elite_dir"))
STATUS_FILE = os.path.join(ELITE_DIR, "Status.json")

# Keep last state for delta tracking
_last_flags = {}

def decode_flags(flags):
    return {
        "Docked":           bool(flags & (1 << 0)),
        "Landed":           bool(flags & (1 << 1)),
        "LandingGearDown":  bool(flags & (1 << 2)),
        "ShieldsUp":        bool(flags & (1 << 3)),
        "Supercruise":      bool(flags & (1 << 4)),
        "FlightAssistOff":  bool(flags & (1 << 5)),
        "HardpointsOut":    bool(flags & (1 << 6)),
        "InWing":           bool(flags & (1 << 7)),
        "LightsOn":         bool(flags & (1 << 8)),
        "CargoScoopOut":    bool(flags & (1 << 9)),
        "SilentRunning":    bool(flags & (1 << 10)),
        "ScoopingFuel":     bool(flags & (1 << 11)),
        "SrvHandbrake":     bool(flags & (1 << 12)),
        "SrvUsingTurretView":bool(flags & (1 << 13)),
        "SrvTurretRetracted":bool(flags & (1 << 14)),
        "SrvDriveAssist":   bool(flags & (1 << 15)),
        "FsdMassLocked":    bool(flags & (1 << 16)),
        "FsdCharging":      bool(flags & (1 << 17)),
        "FsdCooldown":      bool(flags & (1 << 18)),
        "LowFuel":          bool(flags & (1 << 19)),
        "Overheating":      bool(flags & (1 << 20)),
        "HasLatLong":       bool(flags & (1 << 21)),
        "IsInDanger":       bool(flags & (1 << 22)),
        "BeingInterdicted": bool(flags & (1 << 23)),
        "InMainShip":       bool(flags & (1 << 24)),
        "InFighter":        bool(flags & (1 << 25)),
        "InSRV":            bool(flags & (1 << 26)),
        "HudInAnalysisMode":bool(flags & (1 << 27)),
        "NightVision":      bool(flags & (1 << 28)),
        "AltControls":      bool(flags & (1 << 29)),
        "SrvHighBeam":      bool(flags & (1 << 30)),
    }

def process_status_file():
    global _last_flags
    try:
        with open(STATUS_FILE, "r") as f:
            data = json.load(f)
    except Exception as e:
        print(f"[STATUS] Error reading status file: {e}")
        return

    decoded_flags = decode_flags(data.get("Flags", 0))

    # Check for deltas
    if _last_flags:
        for key in decoded_flags:
            if decoded_flags[key] != _last_flags.get(key):
                print(f"[STATUS] Change Detected: {key} = {decoded_flags[key]}")
    else:
        print("[STATUS] Initial load.")

    _last_flags = decoded_flags.copy()

    # Send full payload to serial
    packet = format_packet("status", "StatusDelta", decoded_flags)
    send_to_serial(packet)
    publish_packet(packet)
