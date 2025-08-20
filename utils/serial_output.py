# utils/serial_output.py
# SPDX-License-Identifier: MIT

_seq = 0

def format_packet(source, type_, data):
    """Create a canonical packet with a monotonically increasing sequence number."""
    from datetime import datetime
    global _seq
    _seq += 1
    return {
        "source": source,                                # "journal" | "status" | "modules" | "loadout" | "app"
        "type": type_,                                   # e.g., "FSDJump", "StatusDelta", "ModulesSnapshot", "Loadout"
        "timestamp": datetime.utcnow().isoformat(timespec="milliseconds") + "Z",
        "seq": _seq,
        "data": data
    }

def send_to_serial(packet):
    """Stub: replace with real pyserial write in a later step."""
    import json
   # print("SERIAL OUT >>", json.dumps(packet))
