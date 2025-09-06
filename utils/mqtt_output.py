# utils/mqtt_output.py
# SPDX-License-Identifier: MIT
"""
Minimal MQTT publisher + subscriber for Elite-Parser.
- Publishes packets to elite/events/<type> as JSON
- Subscribes to elite/cmd/# and forwards inbound messages to a handler
"""

import json
import queue
import threading
import time
from collections.abc import Callable
from typing import Optional

from utils.config import get

try:
    import paho.mqtt.client as mqtt
except Exception:
    mqtt = None

CLIENT_ID = "elite-parser"
BROKER = get("outputs.mqtt.broker")
PORT = get("outputs.mqtt.port")
BASE_TOPIC = get("general.base_topic")
QOS = get("outputs.mqtt.qos", 0)
RETAIN = get("outputs.mqtt.retain", False)
USERNAME = get("outputs.mqtt.username", "")
PASSWORD = get("outputs.mqtt.password", "")
CMD_TOPIC = get("inputs.mqtt.cmd_topic", f"{BASE_TOPIC}/cmd/#")

_client: Optional["mqtt.Client"] = None
_outbox: "queue.Queue[tuple[str,str]]" = queue.Queue(maxsize=1000)
_connected = threading.Event()
_stop = threading.Event()

# --- Inbound command handling ---
_command_handler: Callable[[str, object], None] | None = None


def set_command_handler(fn: Callable[[str, object], None]):
    """Register a function(topic, payload) for inbound command messages."""
    global _command_handler
    _command_handler = fn


def _on_connect(client, userdata, flags, reason_code, properties=None):
    if reason_code == 0:
        _connected.set()
        print("[MQTT] Connected")
        # Resubscribe on reconnect
        try:
            client.subscribe(f"{BASE_TOPIC}/cmd/#", qos=0)
            client.subscribe(CMD_TOPIC, qos=0)

            print(f"[MQTT] Subscribed to {BASE_TOPIC}/cmd/#")
        except Exception as e:
            print(f"[MQTT] Subscribe failed: {e}")
    else:
        print(f"[MQTT] Connect failed: {reason_code}")


def _on_disconnect(client, userdata, reason_code, properties=None):
    _connected.clear()
    print(f"[MQTT] Disconnected: {reason_code}")


def _on_message(client, userdata, msg):
    payload_raw = msg.payload.decode("utf-8", errors="ignore").strip()
    payload: object
    # Try JSON first; if that fails, pass string
    try:
        payload = json.loads(payload_raw)
    except Exception:
        payload = payload_raw

    if _command_handler:
        try:
            _command_handler(msg.topic, payload)
        except Exception as e:
            print(f"[MQTT] Command handler error: {e}")
    else:
        print(f"[MQTT] CMD {msg.topic} :: {payload}")


def _publisher_thread():
    while not _stop.is_set():
        try:
            payload, topic = _outbox.get(timeout=0.5)
        except queue.Empty:
            continue
        while not _connected.is_set() and not _stop.is_set():
            time.sleep(0.5)
        if _stop.is_set():
            break
        if _client:
            # Use configured QoS/retain (ensure you defined QOS/RETAIN earlier from config)
            res = _client.publish(topic, payload=payload, qos=QOS, retain=RETAIN)

            # Optional: if you want to block until the library hands it off to the socket:
            # res.wait_for_publish()

            # Optional: basic error logging
            if hasattr(res, "rc") and res.rc != mqtt.MQTT_ERR_SUCCESS:
                print(f"[MQTT] Publish failed rc={res.rc} topic={topic}")

    print("[MQTT] Publisher thread exit")


def start():
    """Start MQTT client and background publisher thread (idempotent)."""
    global _client
    if mqtt is None:
        print("[MQTT] paho-mqtt not installed. Skipping MQTT.")
        return
    if _client is not None:
        return

    _client = mqtt.Client(client_id=CLIENT_ID, protocol=mqtt.MQTTv5)
    _client.on_connect = _on_connect
    _client.on_disconnect = _on_disconnect
    _client.on_message = _on_message

    if USERNAME:
        _client.username_pw_set(USERNAME, PASSWORD)

    _client.connect_async(BROKER, PORT, keepalive=30)
    _client.loop_start()

    threading.Thread(target=_publisher_thread, name="mqtt-pub", daemon=True).start()


def stop():
    _stop.set()
    try:
        if _client:
            _client.loop_stop()
            _client.disconnect()
    except Exception:
        pass


def publish_packet(packet: dict):
    """Queue a packet for publish to elite/events/<type> as JSON."""
    t = packet.get("type", "Unknown")
    topic = f"{BASE_TOPIC}/events/{t}"
    payload = json.dumps(packet, separators=(",", ":"), ensure_ascii=False)
    try:
        _outbox.put_nowait((payload, topic))
    except queue.Full:
        _outbox.get_nowait()
        _outbox.put_nowait((payload, topic))
        print("[MQTT] Outbox full, dropped oldest")
