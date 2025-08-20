import json

def handle_receive_text(event):
    try:
        channel = event.get("Channel", "Unknown")
        sender = event.get("From_Localised", "Unknown")
        message = event.get("Message_Localised", "???")
        print(f"[{channel}]|[{sender}] : {message}")
    except Exception as e:
        print(f"[SHIPCOMMS] Error formatting ReceiveText event: {e}")
