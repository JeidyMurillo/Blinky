"""Estado compartido que leen las 3 interfaces.

Qué va aquí:
- Datos de sesión, cámara, sensores ambientales y recomendaciones activas.
- Suscripción por tema para que cada vista se actualice sin acoplarse.
- Adaptadores para eventos del backend: blink.metrics, exposure.metrics,
  ambient.reading, ambient.status y decision.recommendation.

Los eventos pueden llegar desde hilos de MQTT o del runtime. Por eso `emit`
los encola y MainWindow los consume con `drain_events()` en el hilo de Tk.

La UI no accede a la cámara ni a MQTT desde aquí: solo consume estado.
"""

import queue
import random
from datetime import datetime, timedelta

from fatiga_visual.core.models import AmbientReading, FaceOverlay, Recommendation
from fatiga_visual.exposure.exposure_timer import ExposureTimer


class AppState:
    def __init__(self, settings, bus=None, simulate=True, seed_demo=True, camera_stream=None):
        self.settings = settings
        self.bus = bus
        self.simulate = simulate
        self.seed_demo = seed_demo
        self.camera_stream = camera_stream
        self.session_seconds = int(settings.get("session.initial_seconds", 0)) if seed_demo else 0
        self.blinks = int(settings.get("session.initial_blinks", 0)) if seed_demo else 0
        self.blink_rate = float(settings.get("session.blink_rate", 0)) if seed_demo else 0.0
        self.eyes_closed = False
        self.ear = 0.0
        self.blink_duration_ms = 0.0
        self.inter_blink_seconds = 0.0
        self.perclos = 0.0
        self.long_closures = 0
        self.confidence = 1.0
        self.calibration_progress = 1.0
        self.vision_status = None
        self.face_overlay = FaceOverlay.empty()
        self.last_blink_at = None
        self.last_blink_kind = None
        self.break_history = []
        self.active_break = None
        self.last_break_at = None
        self.running = True
        self.camera_on = False
        self.alert_dismissed = False

        self.ambient = AmbientReading(
            timestamp=datetime.now(),
            lux=420.0,
            temperature_c=23.4,
            humidity=48.0,
            connected=True,
        )
        self.exposure = ExposureTimer(break_after_minutes=20)
        self.exposure.session_seconds = self.session_seconds
        self.exposure.continuous_seconds = 0
        self.exposure.breaks_taken = 0

        self.blink_history = [
            ("Lun", 0),
            ("Mar", 0),
            ("Mie", 0),
            ("Jue", 0),
            ("Vie", 0),
            ("Sab", 0),
            ("Dom", self.blinks),
        ]
        self.recommendations = [] if not seed_demo else [
            Recommendation(
                id="blink-low",
                title="Tus ojos necesitan una pausa",
                message=(
                    "Detectamos una disminucion en tu frecuencia de parpadeo. "
                    "Una rutina breve puede ayudarte a relajar la vista."
                ),
                severity="high",
                action="Ver recomendaciones",
                created_at=datetime.now() - timedelta(minutes=3),
            ),
            Recommendation(
                id="break-20",
                title="Aplica la regla 20-20-20",
                message=(
                    "Llevas 24 minutos frente a la pantalla. Mira durante 20 segundos "
                    "un objeto a 6 metros de distancia."
                ),
                severity="medium",
                action="Ver recomendaciones",
                created_at=datetime.now() - timedelta(minutes=8),
            ),
            Recommendation(
                id="hydrate",
                title="Manten una postura comoda",
                message="Relaja los hombros y alinea la pantalla a la altura de los ojos.",
                severity="low",
                action="Ver recomendaciones",
                created_at=datetime.now() - timedelta(minutes=12),
            ),
        ]

        self._listeners = []
        self._events = queue.Queue()
        if bus is not None:
            bus.subscribe("blink.metrics", self.update_blink_metrics)
            bus.subscribe(
                settings.get("bus.topics.exposure_metrics", "exposure.metrics"),
                self.update_exposure,
            )
            bus.subscribe(
                settings.get("bus.topics.exposure_break", "exposure.break"),
                self.update_break_event,
            )
            bus.subscribe("ambient.reading", self.update_ambient)
            bus.subscribe("ambient.status", self.update_ambient_status)
            bus.subscribe("blink.event", self.update_blink_event)
            bus.subscribe("vision.status", self.update_vision_status)
            bus.subscribe("vision.landmarks", self.update_face_overlay)
            bus.subscribe("decision.recommendation", self.add_recommendation)

    @property
    def continuous_seconds(self):
        """Tiempo continuo frente a la pantalla (se reinicia tras una pausa)."""
        return int(getattr(self.exposure, "continuous_seconds", 0))

    @property
    def break_after_seconds(self):
        return max(1, int(self.settings.get("thresholds.continuous_minutes") * 60))

    @property
    def break_due(self):
        return self.continuous_seconds >= self.break_after_seconds

    @property
    def break_active(self):
        return self.active_break is not None

    @property
    def last_break(self):
        return self.break_history[0] if self.break_history else None

    @property
    def user_present(self):
        """Presión de presencia para el cronómetro; simulación cuenta como presente."""
        status = getattr(self, "vision_status", None)
        if status is None or getattr(status, "backend", "") == "simulated":
            return True
        return bool(getattr(status, "face_found", False))

    def subscribe(self, listener):
        self._listeners.append(listener)

    def emit(self, topic):
        # Los eventos pueden llegar desde MQTT o desde el runtime. Se encolan
        # para que MainWindow los consuma en el hilo de Tk.
        self._events.put(topic)
        for listener in list(self._listeners):
            try:
                listener(topic)
            except Exception:
                pass

    def drain_events(self):
        topics = []
        while True:
            try:
                topics.append(self._events.get_nowait())
            except queue.Empty:
                break
        return topics

    def tick(self):
        if not self.running:
            return False
        if not self.simulate:
            return False
        self.session_seconds += 1
        self.exposure.tick(1)
        blink_started = False
        if random.random() > 0.89 and not self.eyes_closed:
            self.eyes_closed = True
            blink_started = True
        self.emit("tick")
        return blink_started

    def finish_blink(self):
        if not self.eyes_closed:
            return
        self.eyes_closed = False
        self.blinks += 1
        if self.blink_history:
            self.blink_history[-1] = (self.blink_history[-1][0], self.blinks)
        self.emit("tick")

    def toggle_running(self):
        self.running = not self.running
        self.emit("monitoring")

    def set_camera(self, active):
        self.camera_on = active
        if not active:
            self.clear_face_overlay()
            # Camara apagada no es una pausa válida.
            self.active_break = None
        self.emit("camera")

    def clear_face_overlay(self):
        self.face_overlay = FaceOverlay.empty()

    def update_face_overlay(self, overlay):
        # Dato de alta frecuencia: el widget lo lee directo. No va a la cola de
        # eventos de Tk para no llenarla con decenas de topics por segundo.
        self.face_overlay = overlay if overlay is not None else FaceOverlay.empty()

    def set_alert_dismissed(self, dismissed=True):
        self.alert_dismissed = dismissed
        self.emit("recommendations")

    def primary_recommendation(self):
        if not self.recommendations:
            return None
        priority = {"high": 0, "medium": 1, "low": 2}
        return sorted(
            self.recommendations,
            key=lambda item: (priority.get(item.severity, 3), item.created_at),
        )[0]

    def complete_recommendation(self, recommendation_id):
        self.recommendations = [item for item in self.recommendations if item.id != recommendation_id]
        self.alert_dismissed = False
        self.emit("recommendations")

    def add_recommendation(self, recommendation):
        if recommendation is None:
            return
        if all(item.id != recommendation.id for item in self.recommendations):
            self.recommendations.append(recommendation)
            self.alert_dismissed = False
            self.emit("recommendations")

    def update_blink_metrics(self, metrics):
        if metrics is None:
            return
        self.blinks = metrics.blinks
        self.blink_rate = metrics.blink_rate
        self.eyes_closed = metrics.eyes_closed
        self.ear = getattr(metrics, "ear", 0.0)
        self.blink_duration_ms = getattr(metrics, "mean_blink_duration_ms", 0.0)
        self.inter_blink_seconds = getattr(metrics, "inter_blink_seconds", 0.0)
        self.perclos = getattr(metrics, "perclos", 0.0)
        self.long_closures = getattr(metrics, "long_closures", 0)
        self.confidence = getattr(metrics, "confidence", 1.0)
        self.calibration_progress = getattr(metrics, "calibration_progress", 1.0)
        if self.blink_history:
            self.blink_history[-1] = (self.blink_history[-1][0], self.blinks)
        self.emit("tick")

    def update_blink_event(self, event):
        if event is None:
            return
        self.last_blink_at = getattr(event, "timestamp", None)
        self.last_blink_kind = getattr(event, "kind", None)
        self.emit("blink")

    def update_vision_status(self, status):
        if status is None:
            return
        self.vision_status = status
        self.calibration_progress = getattr(status, "calibration_progress", 1.0)
        self.emit("vision")

    def update_exposure(self, metrics):
        if metrics is None:
            return
        self.session_seconds = metrics.session_seconds
        self.exposure.session_seconds = metrics.session_seconds
        self.exposure.continuous_seconds = metrics.continuous_seconds
        self.exposure.breaks_taken = metrics.breaks_taken
        self.emit("tick")

    def update_break_event(self, event):
        if event is None:
            return
        if getattr(event, "kind", "finished") == "started":
            self.active_break = event
        else:
            self.active_break = None
            self.last_break_at = getattr(event, "timestamp", None)
            self.break_history.insert(0, event)
            del self.break_history[20:]
        self.emit("break")

    def update_ambient(self, reading):
        if reading is None:
            return
        self.ambient = reading
        self.emit("ambient")

    def update_ambient_status(self, status):
        if status != "offline":
            return
        connected = getattr(self.ambient, "connected", True)
        if not connected:
            return
        self.ambient = self.ambient.__class__(
            **{**self.ambient.__dict__, "connected": False}
        )
        self.emit("ambient")
