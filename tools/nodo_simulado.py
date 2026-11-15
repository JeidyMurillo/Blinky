"""Nodo ambiental falso: publica MQTT como si fuera el ESP32.

Uso:
    python tools/nodo_simulado.py --scenario normal --interval 2
    python tools/nodo_simulado.py --scenario low-light --count 30
    python tools/nodo_simulado.py --scenario hot --host 192.168.1.100

Respeta contracts/topics.md:
- fatiga/ambient: JSON cada 2 s, QoS 0, retain false.
- fatiga/ambient/status: online/offline, QoS 1, retain true.

Sirve para probar la app sin placa, sin broker real de sensores y sin tocar el
firmware. Con --no-status no registra LWT ni publica estado.
"""

import argparse
import json
import random
import sys
import threading
import time
import uuid
from datetime import datetime, timezone

try:
    import paho.mqtt.client as mqtt
except Exception:
    print("Falta paho-mqtt. Instala con: pip install paho-mqtt", file=sys.stderr)
    raise

try:
    from paho.mqtt.enums import CallbackAPIVersion
except Exception:
    CallbackAPIVersion = None

SCENARIOS = {
    "normal": {"lux": 420.0, "temperature": 23.4, "humidity": 48.0, "drop_rate": 0.0},
    "low-light": {"lux": 120.0, "temperature": 23.0, "humidity": 50.0, "drop_rate": 0.0},
    "hot": {"lux": 500.0, "temperature": 29.5, "humidity": 68.0, "drop_rate": 0.0},
    "unstable": {"lux": 380.0, "temperature": 24.0, "humidity": 52.0, "drop_rate": 0.15},
}


def _ok(reason_code):
    if hasattr(reason_code, "is_failure"):
        return not reason_code.is_failure
    return int(getattr(reason_code, "value", reason_code)) == 0


def make_client(client_id):
    if CallbackAPIVersion is not None:
        return mqtt.Client(CallbackAPIVersion.VERSION2, client_id=client_id)
    return mqtt.Client(client_id=client_id)


def build_reading(seq, base):
    return {
        "lux": round(max(0.0, random.gauss(base["lux"], base["lux"] * 0.05)), 1),
        "temperature": round(random.gauss(base["temperature"], 0.3), 2),
        "humidity": round(min(100.0, max(0.0, random.gauss(base["humidity"], 1.5))), 1),
        "seq": seq,
        "timestamp": int(datetime.now(timezone.utc).timestamp() * 1000),
    }


def main():
    parser = argparse.ArgumentParser(description="Publica lecturas ambientales falsas por MQTT.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=1883)
    parser.add_argument("--topic", default="fatiga/ambient")
    parser.add_argument("--status-topic", default="fatiga/ambient/status")
    parser.add_argument("--client-id", default=f"blinky-sim-{uuid.uuid4().hex[:6]}")
    parser.add_argument("--scenario", choices=sorted(SCENARIOS), default="normal")
    parser.add_argument("--interval", type=float, default=2.0)
    parser.add_argument("--count", type=int, default=0, help="0 = infinito")
    parser.add_argument("--once", action="store_true", help="Publica una sola lectura y sale.")
    parser.add_argument("--no-status", action="store_true", help="No publica online/offline ni LWT.")
    args = parser.parse_args()

    base = dict(SCENARIOS[args.scenario])
    count = 1 if args.once else args.count
    connected = threading.Event()

    def on_connect(client, userdata, flags, reason_code, properties=None):
        if _ok(reason_code):
            connected.set()

    client = make_client(args.client_id)
    client.on_connect = on_connect

    if not args.no_status:
        client.will_set(
            args.status_topic,
            payload="offline",
            qos=1,
            retain=True,
        )

    client.connect(args.host, args.port, keepalive=30)
    client.loop_start()

    if not connected.wait(timeout=5.0):
        print("No se pudo conectar al broker.", file=sys.stderr)
        client.loop_stop()
        return 1

    if not args.no_status:
        client.publish(args.status_topic, "online", qos=1, retain=True)

    print(
        f"nodo simulado '{args.scenario}' -> {args.host}:{args.port} "
        f"{args.topic} cada {args.interval}s"
    )

    seq = 0
    published = 0
    try:
        while count == 0 or published < count:
            reading = build_reading(seq, base)
            seq += 1
            if base["drop_rate"] and random.random() < base["drop_rate"]:
                print(f"[{seq}] descartado (escenario unstable)")
            else:
                info = client.publish(
                    args.topic,
                    json.dumps(reading, separators=(",", ":")),
                    qos=0,
                    retain=False,
                )
                info.wait_for_publish(timeout=2.0)
                published += 1
                print(
                    f"[{seq}] lux={reading['lux']:.0f} "
                    f"temp={reading['temperature']:.1f}C "
                    f"hum={reading['humidity']:.0f}%"
                )
            if count == 0 or published < count:
                time.sleep(max(0.05, args.interval))
    except KeyboardInterrupt:
        print("\nDeteniendo nodo simulado...")
    finally:
        if not args.no_status:
            try:
                client.publish(args.status_topic, "offline", qos=1, retain=True).wait_for_publish(
                    timeout=2.0
                )
            except Exception:
                pass
        client.loop_stop()
        client.disconnect()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
