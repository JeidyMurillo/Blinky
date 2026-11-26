"""Cliente MQTT para las lecturas del ESP32.

Contrato: contracts/topics.md y contracts/ambient.schema.json.

Qué hace:
- Escucha fatiga/ambient y valida el JSON contra el contrato.
- Escucha fatiga/ambient/status (online/offline) y publica "ambient.status".
- Publica "ambient.reading" en el EventBus; nunca toca la UI directamente.

Si un mensaje no cumple el esquema se descarta sin romper la aplicación.
"""

import json
import math
import os
import threading
from datetime import datetime

from fatiga_visual.core.models import AmbientReading

try:
    import paho.mqtt.client as mqtt
except Exception:
    mqtt = None

try:
    from paho.mqtt.enums import CallbackAPIVersion
except Exception:
    CallbackAPIVersion = None

ALLOWED_FIELDS = {"lux", "temperature", "humidity", "seq", "timestamp", "firmware"}
REQUIRED_FIELDS = {"lux", "temperature", "humidity"}
STATUS_TOPIC_DEFAULT = "fatiga/ambient/status"


def _number(data, key):
    value = data[key]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{key} debe ser numérico")
    value = float(value)
    if not math.isfinite(value):
        raise ValueError(f"{key} debe ser finito")
    return value


def reading_from_mapping(data):
    """Valida un diccionario según ambient.schema.json."""
    if not isinstance(data, dict):
        raise ValueError("El payload ambiental debe ser un objeto JSON")

    unknown = set(data) - ALLOWED_FIELDS
    if unknown:
        raise ValueError(f"Campos no permitidos: {sorted(unknown)}")
    missing = REQUIRED_FIELDS - set(data)
    if missing:
        raise ValueError(f"Faltan campos obligatorios: {sorted(missing)}")

    lux = _number(data, "lux")
    temperature = _number(data, "temperature")
    humidity = _number(data, "humidity")

    if not 0 <= lux <= 200000:
        raise ValueError("lux fuera de rango")
    if not -40 <= temperature <= 85:
        raise ValueError("temperature fuera de rango")
    if not 0 <= humidity <= 100:
        raise ValueError("humidity fuera de rango")

    return AmbientReading(
        timestamp=datetime.now(),
        lux=lux,
        temperature_c=temperature,
        humidity=humidity,
        connected=True,
    )


def parse_reading(payload):
    if isinstance(payload, bytes):
        payload = payload.decode("utf-8")
    return reading_from_mapping(json.loads(payload))


def _make_client(client_id):
    if CallbackAPIVersion is not None:
        return mqtt.Client(CallbackAPIVersion.VERSION2, client_id=client_id)
    return mqtt.Client(client_id=client_id)


class MqttAmbientClient:
    def __init__(
        self,
        bus,
        host="127.0.0.1",
        port=1883,
        topic="fatiga/ambient",
        status_topic=STATUS_TOPIC_DEFAULT,
        keepalive=30,
        qos=0,
        client_id=None,
    ):
        self.bus = bus
        self.host = host
        self.port = port
        self.topic = topic
        self.status_topic = status_topic
        self.keepalive = keepalive
        self.qos = qos
        self.client_id = client_id or f"blinky-app-{os.getpid()}"
        self._client = None
        self._stop = threading.Event()

    def start(self):
        if mqtt is None:
            raise RuntimeError("paho-mqtt no está instalado")
        self._client = _make_client(self.client_id)
        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.on_message = self._on_message
        self._client.connect_async(self.host, self.port, self.keepalive)
        self._stop.clear()
        self._client.loop_start()

    def _on_connect(self, client, userdata, flags, reason_code, properties=None):
        if not _is_success(reason_code):
            return
        subscriptions = [(self.topic, self.qos)]
        if self.status_topic:
            subscriptions.append((self.status_topic, 1))
        client.subscribe(subscriptions)

    def _on_disconnect(self, client, userdata, *args):
        self.bus.publish("ambient.status", "offline")

    def _on_message(self, client, userdata, message):
        try:
            payload = message.payload.decode("utf-8")
        except Exception:
            return

        if self.status_topic and message.topic == self.status_topic:
            # Un "offline" retenido es de una sesión anterior: al arrancar no
            # debe marcar el nodo como desconectado antes de oír tráfico nuevo.
            if getattr(message, "retain", False) and payload == "offline":
                return
            if payload in ("online", "offline"):
                self.bus.publish("ambient.status", payload)
            return

        try:
            reading = parse_reading(payload)
        except Exception:
            return
        self.bus.publish("ambient.reading", reading)

    def stop(self):
        self._stop.set()
        client = self._client
        self._client = None
        if client is not None:
            try:
                client.loop_stop()
            except Exception:
                pass
            try:
                client.disconnect()
            except Exception:
                pass


def _is_success(reason_code):
    if hasattr(reason_code, "is_failure"):
        return not reason_code.is_failure
    return reason_code == 0
