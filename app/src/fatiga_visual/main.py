"""Punto de entrada de Blinky.

Qué va aquí:
- Crear EventBus, cargar settings.yaml y AppState.
- Construir el grafo: MQTT opcional, almacenamiento y runtime.
- Abrir MainWindow y su mainloop.

Fuentes de datos (`runtime.source` en settings.yaml):
- `ui`: la simulación vive dentro de AppState (comportamiento anterior).
- `simulated`: runtime/simulated.py publica eventos sin hardware.
- `real`: runtime/pipeline.py usa la cámara compartida con la UI.

Ejecutar:
    cd app/src
    python -m fatiga_visual.main
"""

import queue
import sys
import threading
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fatiga_visual.ambient.ambient_state import AmbientState
from fatiga_visual.ambient.mqtt_client import MqttAmbientClient
from fatiga_visual.core.config import load_settings
from fatiga_visual.core.events import EventBus
from fatiga_visual.runtime import RuntimePipeline, SimulatedPipeline
from fatiga_visual.storage.repository import Repository
from fatiga_visual.ui.main_window import MainWindow
from fatiga_visual.ui.state import AppState
from fatiga_visual.vision.camera import CameraStream

SOURCES = ("ui", "simulated", "real")


def _source(settings):
    value = str(settings.get("runtime.source", "real")).lower()
    return value if value in SOURCES else "real"


def _start_storage(settings, bus):
    if not settings.get("storage.enabled", True):
        return None, None
    try:
        path = settings.get("storage.path", "") or None
        repository = Repository(path=path)
        session_id = repository.start_session(source=_source(settings))
    except Exception as exc:
        print(f"Aviso: no se pudo abrir la base de datos: {exc}")
        return None, None

    # Un solo hilo escribe en SQLite para no frenar al pipeline ni a la UI.
    writes = queue.Queue()

    def drain():
        while True:
            handler, payload = writes.get()
            if handler is None:
                return
            try:
                handler(payload)
            except Exception:
                pass

    writer = threading.Thread(target=drain, name="storage-writer", daemon=True)
    writer.start()

    def stop():
        writes.put((None, None))
        writer.join(timeout=5.0)
        repository.end_session(session_id)
        repository.close()

    repository.stop = stop

    def safe(handler):
        return lambda payload: writes.put((handler, payload))

    bus.subscribe(
        "blink.metrics",
        safe(lambda reading: repository.record_blink(reading, session_id)),
    )
    bus.subscribe(
        settings.get("bus.topics.exposure_metrics", "exposure.metrics"),
        safe(lambda reading: repository.record_exposure(reading, session_id)),
    )
    bus.subscribe(
        "ambient.reading",
        safe(lambda reading: repository.record_ambient(reading, session_id)),
    )
    bus.subscribe(
        "decision.recommendation",
        safe(lambda reading: repository.record_recommendation(reading, session_id)),
    )
    return repository, session_id


def _start_mqtt(settings, bus):
    if not settings.get("mqtt.enabled", False):
        return None
    try:
        client = MqttAmbientClient(
            bus,
            host=settings.get("mqtt.host", "127.0.0.1"),
            port=int(settings.get("mqtt.port", 1883)),
            topic=settings.get("mqtt.topics.ambient", "fatiga/ambient"),
            status_topic=settings.get("mqtt.topics.status", "fatiga/ambient/status"),
            keepalive=int(settings.get("mqtt.keepalive", 30)),
            qos=int(settings.get("mqtt.qos", 0)),
        )
        client.start()
        return client
    except Exception as exc:
        print(f"Aviso: MQTT no disponible: {exc}")
        return None


def _start_runtime(settings, bus, state, ambient_state, camera, mqtt_client):
    source = _source(settings)
    if source == "ui":
        return None

    simulate_ambient = mqtt_client is None
    if source == "real":
        runtime = RuntimePipeline(
            settings,
            bus,
            camera=camera,
            ambient_state=ambient_state,
            is_running=lambda: state.running,
        )
        if runtime.available:
            runtime.start()
            return runtime
        detail = getattr(runtime.detector, "error", "")
        print(
            "Aviso: el detector de visión no está disponible; "
            f"se usa la fuente simulada. {detail}"
        )
        runtime.stop()

    runtime = SimulatedPipeline(
        settings,
        bus,
        ambient_state=ambient_state,
        is_running=lambda: state.running,
        simulate_ambient=simulate_ambient,
    )
    runtime.start()
    return runtime


def main():
    bus = EventBus()
    settings = load_settings()
    source = _source(settings)

    camera = None
    if source == "real":
        camera = CameraStream(
            index=int(settings.get("camera.index", 0)),
            width=int(settings.get("camera.width", 1280)),
            height=int(settings.get("camera.height", 720)),
            fps=int(settings.get("camera.fps", 30)),
        )

    state = AppState(
        settings,
        bus,
        simulate=(source == "ui"),
        seed_demo=(source == "ui"),
        camera_stream=camera,
    )
    ambient_state = AmbientState(
        stale_after_seconds=int(settings.get("ambient.stale_after_seconds", 15))
    )
    bus.subscribe("ambient.reading", ambient_state.update)

    repository, session_id = _start_storage(settings, bus)
    mqtt_client = _start_mqtt(settings, bus)
    runtime = _start_runtime(settings, bus, state, ambient_state, camera, mqtt_client)

    window = MainWindow(state)
    try:
        window.mainloop()
    finally:
        if runtime is not None:
            runtime.stop()
        if mqtt_client is not None:
            mqtt_client.stop()
        if repository is not None:
            repository.stop()
        if camera is not None:
            camera.stop()


if __name__ == "__main__":
    main()
