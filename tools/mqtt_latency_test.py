"""Mide la latencia de ida y vuelta contra el broker MQTT.

Uso:
    python tools/mqtt_latency_test.py --host 127.0.0.1 --topic fatiga/test --count 20
    python tools/mqtt_latency_test.py --qos 1 --interval 0.2

Correcciones respecto a la versión anterior:
- Compatible con paho-mqtt 2.x (CallbackAPIVersion.VERSION2) y 1.x.
- Espera CONNACK y SUBACK antes de publicar, así no se pierden mensajes.
- Usa un tópico único por ejecución para no medir mensajes retenidos o viejos.
- Calcula media, mediana, p95, mínimo, máximo y pérdidas.
- Sale con código 1 si no recibe nada.

La latencia incluye app -> broker -> app y sirve para validar el enlace antes
de la demo. No mide el tiempo del ESP32.
"""

import argparse
import json
import statistics
import sys
import threading
import time
import uuid

try:
    import paho.mqtt.client as mqtt
except Exception:
    print("Falta paho-mqtt. Instala con: pip install paho-mqtt", file=sys.stderr)
    raise

try:
    from paho.mqtt.enums import CallbackAPIVersion
except Exception:
    CallbackAPIVersion = None


def _ok(reason_code):
    if hasattr(reason_code, "is_failure"):
        return not reason_code.is_failure
    return int(getattr(reason_code, "value", reason_code)) == 0


def make_client(client_id):
    if CallbackAPIVersion is not None:
        return mqtt.Client(CallbackAPIVersion.VERSION2, client_id=client_id)
    return mqtt.Client(client_id=client_id)


def main():
    parser = argparse.ArgumentParser(description="Latencia de ida y vuelta contra Mosquitto.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=1883)
    parser.add_argument("--topic", default="fatiga/test")
    parser.add_argument("--count", type=int, default=20)
    parser.add_argument("--interval", type=float, default=0.1)
    parser.add_argument("--qos", type=int, choices=(0, 1), default=0)
    parser.add_argument("--timeout", type=float, default=5.0)
    args = parser.parse_args()

    run_id = uuid.uuid4().hex[:8]
    run_topic = f"{args.topic}/{run_id}"
    connected = threading.Event()
    subscribed = threading.Event()
    latencies = []

    def on_connect(client, userdata, flags, reason_code, properties=None):
        if not _ok(reason_code):
            return
        client.subscribe(run_topic, qos=args.qos)
        connected.set()

    def on_subscribe(client, userdata, mid, *args):
        subscribed.set()

    def on_message(client, userdata, message):
        try:
            payload = json.loads(message.payload.decode("utf-8"))
            received = time.perf_counter()
            latencies.append((received - float(payload["sent"])) * 1000.0)
        except Exception:
            return

    client = make_client(f"blinky-latency-{run_id}")
    client.on_connect = on_connect
    client.on_subscribe = on_subscribe
    client.on_message = on_message

    try:
        client.connect(args.host, args.port, keepalive=30)
    except Exception as exc:
        print(f"No se pudo conectar a {args.host}:{args.port}: {exc}", file=sys.stderr)
        return 1

    client.loop_start()
    if not connected.wait(timeout=5.0):
        print("Sin CONNACK del broker.", file=sys.stderr)
        client.loop_stop()
        return 1
    if not subscribed.wait(timeout=5.0):
        print("Sin SUBACK del broker.", file=sys.stderr)
        client.loop_stop()
        client.disconnect()
        return 1

    # Pequeña pausa para que el broker propague la suscripción.
    time.sleep(0.1)

    for index in range(args.count):
        payload = {"sent": time.perf_counter(), "index": index, "run": run_id}
        info = client.publish(
            run_topic,
            json.dumps(payload, separators=(",", ":")),
            qos=args.qos,
            retain=False,
        )
        if args.qos:
            info.wait_for_publish(timeout=2.0)
        if index < args.count - 1:
            time.sleep(max(0.0, args.interval))

    deadline = time.time() + args.timeout
    while len(latencies) < args.count and time.time() < deadline:
        time.sleep(0.02)

    client.loop_stop()
    client.disconnect()

    received = len(latencies)
    lost = args.count - received
    if not latencies:
        print("No se recibieron mensajes. Revisa el broker y el tópico.")
        return 1

    ordered = sorted(latencies)
    p95_index = min(received - 1, int(round(received * 0.95)) - 1)
    print(f"tópico:   {run_topic}")
    print(f"mensajes: {received}/{args.count} (perdidos: {lost})")
    print(f"media:    {statistics.fmean(latencies):.2f} ms")
    print(f"mediana:  {statistics.median(latencies):.2f} ms")
    print(f"p95:      {ordered[max(0, p95_index)]:.2f} ms")
    print(f"mínima:   {min(latencies):.2f} ms")
    print(f"máxima:   {max(latencies):.2f} ms")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
