"""Pipeline simulado: misma salida que pipeline.py, sin cámara ni sensores.

Se usa para demos, pruebas de UI y para seguir trabajando cuando MediaPipe o el
ESP32 no están disponibles. Publica exactamente los mismos temas del EventBus:

- blink.metrics
- exposure.metrics
- ambient.reading (opcional)
- decision.recommendation

Nunca actualiza widgets directamente.
"""

import random
import threading
import time
from datetime import datetime

from fatiga_visual.core.models import AmbientReading, BlinkMetrics, VisionStatus
from fatiga_visual.decision.engine import DecisionEngine
from fatiga_visual.exposure.exposure_timer import ExposureTimer


class SimulatedPipeline:
    def __init__(
        self,
        settings,
        bus,
        ambient_state=None,
        is_running=None,
        simulate_ambient=True,
    ):
        self.settings = settings
        self.bus = bus
        self.ambient_state = ambient_state
        self.is_running = is_running or (lambda: True)
        self.simulate_ambient = simulate_ambient
        self.interval = max(0.05, float(settings.get("runtime.publish_seconds", 1.0)))
        self.blink_target = float(settings.get("runtime.simulated.blink_rate", 18.0))
        self.ambient_seconds = max(self.interval, float(settings.get("runtime.simulated.ambient_seconds", 5.0)))
        self._jitter = float(settings.get("runtime.simulated.jitter", 2.0))

        self.timer = ExposureTimer(
            break_after_minutes=int(settings.get("thresholds.continuous_minutes", 20))
        )
        self.timer.session_seconds = int(settings.get("session.initial_seconds", 0))
        self.timer.continuous_seconds = int(settings.get("session.initial_continuous_seconds", 0))
        self.timer.breaks_taken = int(settings.get("session.initial_breaks", 0))
        self.blinks = int(settings.get("session.initial_blinks", 0))
        self._blink_fraction = 0.0
        self.engine = DecisionEngine(settings, bus)

        self._ambient = AmbientReading(
            timestamp=datetime.now(),
            lux=420.0,
            temperature_c=23.4,
            humidity=48.0,
            connected=True,
        )
        self._next_ambient = 0.0
        self._thread = None
        self._stop = threading.Event()

    def start(self):
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="runtime-simulated", daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        thread = self._thread
        self._thread = None
        if thread is not None and thread.is_alive():
            thread.join(timeout=2.0)

    def _run(self):
        last = time.monotonic()
        self._tick(0.0)
        while not self._stop.wait(self.interval):
            now = time.monotonic()
            elapsed = now - last
            last = now
            if self.is_running():
                self._tick(elapsed)

    def _tick(self, elapsed):
        self.timer.tick(elapsed)
        if self.timer.break_due:
            self.timer.take_break()

        self._maybe_publish_ambient()

        blink_rate = max(4.0, random.gauss(self.blink_target, self._jitter))
        self._blink_fraction += (blink_rate * max(0.0, elapsed)) / 60.0
        whole_blinks = int(self._blink_fraction)
        self._blink_fraction -= whole_blinks
        self.blinks += whole_blinks

        eyes_closed = random.random() < 0.04
        blink = BlinkMetrics(
            timestamp=datetime.now(),
            blinks=self.blinks,
            blink_rate=blink_rate,
            eyes_closed=eyes_closed,
            ear=0.12 if eyes_closed else 0.28,
            confidence=1.0,
            mean_blink_duration_ms=round(random.gauss(180.0, 25.0), 1),
            last_blink_duration_ms=round(random.gauss(180.0, 25.0), 1),
            inter_blink_seconds=round(max(1.0, 60.0 / max(1.0, blink_rate)), 2),
            perclos=round(random.uniform(0.02, 0.09), 4),
            long_closures=0,
            elapsed_seconds=round(self.timer.session_seconds, 1),
            calibration_progress=1.0,
            source="simulated",
        )
        exposure = self.timer.snapshot()
        status = VisionStatus(
            timestamp=datetime.now(),
            backend="simulated",
            available=True,
            face_found=True,
            calibrating=False,
            calibration_progress=1.0,
            threshold=0.21,
            message="Fuente simulada",
        )

        self.bus.publish("blink.metrics", blink)
        self.bus.publish("vision.status", status)
        self.bus.publish("exposure.metrics", exposure)

        ambient = self.ambient_state.latest() if self.ambient_state is not None else None
        if ambient is None and self.simulate_ambient:
            ambient = self._ambient
        self.engine.evaluate(blink, exposure, ambient)

    def _maybe_publish_ambient(self):
        if not self.simulate_ambient:
            return
        now = time.monotonic()
        if now < self._next_ambient:
            return
        self._next_ambient = now + self.ambient_seconds
        self._ambient = AmbientReading(
            timestamp=datetime.now(),
            lux=max(0.0, random.gauss(420.0, 25.0)),
            temperature_c=random.gauss(23.4, 0.3),
            humidity=min(100.0, max(0.0, random.gauss(48.0, 2.0))),
            connected=True,
        )
        self.bus.publish("ambient.reading", self._ambient)
