"""Pipeline real: cámara -> landmarks -> EAR -> métricas -> decisión.

Es el pegamento del sistema cuando hay hardware. No dibuja nada y no conoce
Tk: publica los mismos temas que la fuente simulada para que la UI no cambie.

Temas publicados:
- blink.metrics
- blink.event (parpadeo o cierre largo, para reacciones inmediatas)
- vision.status (backend, rostro, calibración y umbral)
- exposure.metrics
- exposure.break (inicio y fin de una pausa válida)
- decision.recommendation

La cámara es compartida con la UI (VisionFrame). Si la ventana no la activa,
el pipeline sigue contando tiempo de sesión pero no genera parpadeos.

Detección:
1. MediaPipe Face Landmarker extrae los 478 landmarks y `eyeBlink`.
2. Se calcula el EAR de cada ojo y se suaviza con un EMA.
3. Una calibración de pocos segundos adapta el umbral a la persona y la luz.
4. `BlinkDetector` aplica histéresis, duración y clasifica cierres largos.
5. `BlinkMetricsAggregator` calcula tasa, PERCLOS e intervalos.
"""

import threading
import time
from datetime import datetime
from pathlib import Path

from fatiga_visual.core.models import BlinkEvent, FaceOverlay, PresenceEvent, VisionStatus
from fatiga_visual.decision.engine import DecisionEngine
from fatiga_visual.exposure.breaks import BreakDetector
from fatiga_visual.exposure.bus import ExposureBusPublisher
from fatiga_visual.exposure.exposure_timer import ExposureTimer
from fatiga_visual.exposure.presence import PresenceTracker
from fatiga_visual.vision.blink_detector import BlinkDetector
from fatiga_visual.vision.blink_metrics import BlinkMetricsAggregator
from fatiga_visual.vision.calibration import EarCalibration
from fatiga_visual.vision.camera import CameraStream
from fatiga_visual.vision.ear import average_eye_aspect_ratio, eye_aspect_ratios
from fatiga_visual.vision.face_landmarks import FaceLandmarkDetector, overlay_from_landmarks
from fatiga_visual.vision.smoothing import ExponentialSmoother

try:
    import cv2
except Exception:
    cv2 = None


class RuntimePipeline:
    def __init__(self, settings, bus, camera=None, ambient_state=None, is_running=None):
        self.settings = settings
        self.bus = bus
        self.ambient_state = ambient_state
        self.is_running = is_running or (lambda: True)
        self.camera = camera or CameraStream(
            index=int(settings.get("camera.index", 0)),
            width=int(settings.get("camera.width", 1280)),
            height=int(settings.get("camera.height", 720)),
            fps=int(settings.get("camera.fps", 30)),
        )

        self.use_blendshapes = bool(settings.get("vision.use_blendshapes", True))
        self.detector = FaceLandmarkDetector(
            model_path=str(settings.get("vision.model_path", "") or "") or None,
            running_mode="video",
            use_blendshapes=self.use_blendshapes,
            allow_download=bool(settings.get("vision.allow_model_download", True)),
        )

        self.auto_calibrate = bool(settings.get("vision.auto_calibrate", True))
        self.reopen_margin = float(settings.get("vision.reopen_margin", 0.02))
        self.calibration = EarCalibration(
            seconds=float(settings.get("vision.calibration_seconds", 4.0)),
            min_samples=int(settings.get("vision.calibration_min_samples", 24)),
            fallback=float(settings.get("vision.ear_threshold", 0.21)),
            ratio=float(settings.get("vision.calibration_ratio", 0.60)),
            floor=float(settings.get("vision.calibration_floor", 0.06)),
            ceiling=float(settings.get("vision.calibration_ceiling", 0.28)),
        )
        self._calibration_path = self._resolve_calibration_path(settings)
        self._load_calibration()

        self.blink_detector = BlinkDetector(
            threshold=self.calibration.threshold(),
            min_closed_frames=int(settings.get("vision.min_closed_frames", 2)),
            max_closed_frames=int(settings.get("vision.max_closed_frames", 15)),
            reopen_margin=self.reopen_margin,
            min_blink_duration_ms=float(settings.get("vision.min_blink_duration_ms", 0.0)),
            max_blink_duration_ms=float(settings.get("vision.max_blink_duration_ms", 800.0)),
            long_closure_seconds=float(settings.get("vision.long_closure_seconds", 1.5)),
            blink_score_threshold=(
                float(settings.get("vision.blink_score_threshold", 0.55))
                if self.use_blendshapes
                else None
            ),
            cooldown_seconds=float(settings.get("vision.blink_cooldown_seconds", 0.06)),
        )
        self.smoother = ExponentialSmoother(float(settings.get("vision.smoothing_alpha", 0.65)))
        self.aggregator = BlinkMetricsAggregator(
            window_seconds=int(settings.get("vision.blink_window_seconds", 60)),
            min_rate_window_seconds=float(
                settings.get("vision.min_rate_window_seconds", 10.0)
            ),
        )

        self.presence = PresenceTracker(
            absent_after_seconds=int(settings.get("exposure.absent_after_seconds", 20))
        )
        self.timer = ExposureTimer(
            break_after_minutes=int(settings.get("thresholds.continuous_minutes"))
        )
        self.break_detector = BreakDetector(
            min_break_seconds=float(settings.get("exposure.break_min_seconds", 20))
        )
        self.engine = DecisionEngine(settings, bus)
        self.exposure_bus = ExposureBusPublisher(bus, settings)
        self.publish_seconds = max(0.2, float(settings.get("runtime.publish_seconds", 1.0)))
        self.frame_interval = max(
            0.0, float(settings.get("runtime.frame_interval_ms", 40)) / 1000.0
        )
        self.auto_start_camera = bool(settings.get("runtime.auto_start_camera", False))
        self.processing_width = int(settings.get("vision.processing_width", 640))
        self.face_grace_seconds = max(
            0.0, float(settings.get("vision.face_grace_seconds", 0.4))
        )
        # Mismo umbral que usa el motor de decisión (SCRUM-32).
        self.min_confidence = float(settings.get("thresholds.min_confidence"))
        self.overlay_interval = max(
            0.0, float(settings.get("vision.overlay_publish_seconds", 0.05))
        )

        self._thread = None
        self._stop = threading.Event()
        self._owns_camera = False
        self._face_found = False
        self._face_missing_since = None
        self._last_face_at = None
        self._last_ear = 0.0
        self._last_blink_score = None
        self._last_confidence = 0.0
        self._was_present = False
        self._vision_message = self.detector.error
        self._last_overlay_at = 0.0
        self._overlay_visible = False
        self._calibration_started = False
        self._aggregator_started = False
        self._presence_event = None

    @staticmethod
    def _resolve_calibration_path(settings):
        value = str(settings.get("vision.calibration_path", "") or "").strip()
        if value:
            return Path(value).expanduser()
        return Path(__file__).resolve().parents[3] / "blinky_calibration.json"

    def _load_calibration(self):
        try:
            loaded = self.calibration.load(self._calibration_path)
        except Exception:
            loaded = False
        if loaded:
            # Arrancar con el último umbral bueno mientras se recalibra.
            self.calibration.fallback = self.calibration.threshold_value
        # No calibrar aquí: los segundos deben contar desde que la cámara ve
        # una cara, no desde que se abre la aplicación.
        self.calibration.reset()
        self._calibration_started = False

    @property
    def available(self):
        """True si MediaPipe y el modelo están listos."""
        return self.detector.available

    @property
    def calibration_progress(self):
        if not self.auto_calibrate:
            return 1.0
        if not self._calibration_started:
            return 0.0
        return self.calibration.progress()

    def _camera_state(self):
        state = getattr(self.camera, "state", None)
        try:
            return state() if state is not None else ""
        except Exception:
            return ""

    def start(self):
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop.clear()
        if self.auto_start_camera:
            self._owns_camera = True
            self.camera.start()
        self._thread = threading.Thread(target=self._run, name="runtime-pipeline", daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        thread = self._thread
        self._thread = None
        if thread is not None and thread.is_alive():
            thread.join(timeout=3.0)
        if self.calibration.ready:
            self.calibration.save(self._calibration_path)
        self.detector.close()
        if self._owns_camera:
            self._owns_camera = False
            self.camera.stop()

    def _run(self):
        last_frame_seq = -1
        last_frame_at = 0.0
        last_publish = time.monotonic() - self.publish_seconds

        while not self._stop.is_set():
            now = time.monotonic()
            seq, frame, _fps = self.camera.read_frame()
            if (
                frame is not None
                and seq != last_frame_seq
                and now - last_frame_at >= self.frame_interval
            ):
                last_frame_seq = seq
                last_frame_at = now
                self._process_frame(frame, now)

            if now - last_publish >= self.publish_seconds:
                elapsed = max(0.0, now - last_publish)
                last_publish = now
                self._sample(elapsed, now)

            self._stop.wait(0.01)

    def _prepare_frame(self, frame):
        if (
            cv2 is not None
            and self.processing_width > 0
            and frame.shape[1] > self.processing_width
        ):
            scale = self.processing_width / float(frame.shape[1])
            height = max(1, int(frame.shape[0] * scale))
            return cv2.resize(
                frame, (self.processing_width, height), interpolation=cv2.INTER_AREA
            )
        return frame

    def _process_frame(self, frame, now):
        prepared = self._prepare_frame(frame)
        try:
            vision_frame = self.detector.process(prepared, now)
        except Exception as exc:
            self._vision_message = f"Error de visión: {exc}"
            self._mark_face_missing(now)
            return

        if vision_frame.landmarks is None:
            self._mark_face_missing(now)
            return

        if vision_frame.confidence < self.min_confidence:
            self._vision_message = "Rostro detectado con baja confianza"
            self._mark_face_missing(now)
            return

        self._vision_message = ""
        self._face_found = True
        self._face_missing_since = None
        self._last_face_at = now
        self._last_confidence = vision_frame.confidence
        self._publish_overlay(vision_frame.landmarks, now)

        try:
            height, width = prepared.shape[:2]
            left_ear, right_ear = eye_aspect_ratios(
                vision_frame.landmarks, width, height
            )
            ear = (left_ear + right_ear) / 2.0
        except Exception as exc:
            self._vision_message = f"No se pudo calcular el EAR: {exc}"
            self._mark_face_missing(now)
            return

        # Un EAR fuera de rango suele indicar landmarks malos (rostro cortado
        # o girado). Se ignora el fotograma para no corromper el suavizado ni
        # la calibración; si el problema persiste, la cara se marca ausente.
        if ear <= 0.0 or ear > 0.50:
            return

        ear = self.smoother.update(ear)
        self._last_ear = ear
        self._last_blink_score = vision_frame.blink_score

        if self.auto_calibrate and not self.calibration.ready:
            if not self._calibration_started:
                self.calibration.start(now)
                self._calibration_started = True
            self.calibration.add(ear, now)
            if not self.calibration.ready:
                # Mientras calibra no se detectan parpadeos: el umbral aún no
                # es fiable y contar cierres aquí dispararía el PERCLOS.
                self.aggregator.set_eyes_closed(False, datetime.now())
                return
            self.blink_detector.set_threshold(
                self.calibration.threshold(), self.reopen_margin
            )
            self.blink_detector.reset()
            self.calibration.save(self._calibration_path)

        if not self._aggregator_started:
            self.aggregator.start(datetime.now())
            self._aggregator_started = True

        event = self.blink_detector.update(
            ear, now, blink_score=vision_frame.blink_score
        )
        self.aggregator.set_eyes_closed(self.blink_detector.is_closed, datetime.now())

        if event == "opened":
            self.aggregator.add_blink(
                datetime.now(),
                ear,
                duration_ms=self.blink_detector.last_duration_ms,
            )
            self._publish_blink_event("blink", self.blink_detector.last_duration_ms)
        elif event == "long_closure":
            self.aggregator.add_long_closure(
                datetime.now(), duration_ms=self.blink_detector.last_duration_ms
            )
            self._publish_blink_event(
                "long_closure", self.blink_detector.last_duration_ms
            )

    def _mark_face_missing(self, now):
        if self._face_missing_since is None:
            self._face_missing_since = now
        if now - self._face_missing_since < self.face_grace_seconds:
            return
        self._face_found = False
        self._last_ear = 0.0
        self._last_confidence = 0.0
        self._last_blink_score = None
        self._clear_overlay()
        self.blink_detector.reset()
        self.smoother.reset()
        self.aggregator.set_eyes_closed(False, datetime.now())

    def _reset_vision_state(self):
        self._face_found = False
        self._face_missing_since = None
        self._last_face_at = None
        self._last_ear = 0.0
        self._last_confidence = 0.0
        self._last_blink_score = None
        self._clear_overlay()
        self.blink_detector.reset()
        self.smoother.reset()
        self.aggregator.set_eyes_closed(False, datetime.now())

    def _publish_overlay(self, landmarks, now):
        """Publica puntos normalizados para el overlay; va throttleado."""
        if self.bus is None or now - self._last_overlay_at < self.overlay_interval:
            return
        self._last_overlay_at = now
        overlay = overlay_from_landmarks(landmarks)
        if overlay is None or not overlay.visible:
            self._clear_overlay()
            return
        self._overlay_visible = True
        self.bus.publish("vision.landmarks", overlay)

    def _clear_overlay(self):
        if self.bus is None or not self._overlay_visible:
            return
        self._overlay_visible = False
        self.bus.publish("vision.landmarks", FaceOverlay.empty())

    def _publish_break_event(self, event):
        self.exposure_bus.publish_break(event)

    def _publish_blink_event(self, kind, duration_ms):
        if self.bus is None:
            return
        self.bus.publish(
            "blink.event",
            BlinkEvent(
                timestamp=datetime.now(),
                kind=kind,
                ear=self._last_ear,
                duration_ms=max(0.0, float(duration_ms)),
                confidence=self._last_confidence,
            ),
        )

    def _sample(self, elapsed, now):
        if not self.is_running():
            return

        camera_state = self._camera_state()
        camera_running = camera_state == CameraStream.RUNNING
        if not camera_running:
            # Sin cámara no hay parpadeos: evita que un cierre quede "abierto"
            # para siempre y que el PERCLOS siga subiendo.
            self._reset_vision_state()

        now_dt = datetime.now()
        face_found = (
            camera_running
            and self._face_found
            and self._last_face_at is not None
            and now - self._last_face_at <= 2.0
        )
        presence_confidence = self._last_confidence if face_found else 0.0
        if camera_running:
            break_event = self.break_detector.update(
                face_found, now_dt, continuous_seconds=self.timer.continuous_seconds
            )
            self._presence_event = self.presence.update(
                face_found, now_dt, confidence=presence_confidence
            )
            present = self.presence.present
            if self.break_detector.active:
                # Pausa ya validada: el contador no debe seguir avanzando aunque
                # PresenceTracker todavía tolere la ausencia.
                present = False
        else:
            # Camara apagada no es una pausa: se descarta la ausencia en curso.
            self.break_detector.reset()
            break_event = None
            self._presence_event = self.presence.update(False, now_dt, confidence=0.0)
            present = False
        self._was_present = present

        if break_event is not None:
            if break_event.kind == "started":
                # HU-08: la ausencia minima cumplida reinicia el contador.
                self.timer.take_break()
            self._publish_break_event(break_event)

        self.timer.tick(elapsed, present=present)
        if self._presence_event is not None:
            self.exposure_bus.publish_presence(self._presence_event)
            self._presence_event = None
        exposure = self.timer.snapshot()
        blink = self.aggregator.snapshot(
            ear=self._last_ear,
            confidence=self._last_confidence,
            source=self.detector.backend if self.detector.available else "unavailable",
            calibration_progress=self.calibration_progress,
        )
        # Solo se muestra "Calibrando" cuando la cámara ya vio un rostro y la
        # calibración empezó de verdad. Antes de eso el mensaje correcto es
        # "Colócate frente a la cámara".
        calibrating = (
            self.auto_calibrate
            and camera_running
            and self._calibration_started
            and not self.calibration.ready
        )
        message = self._vision_message
        if not camera_running:
            message = (
                "Conectando camara..."
                if camera_state == CameraStream.STARTING
                else "Activa la camara para detectar parpadeos"
            )
        elif not face_found and not calibrating:
            message = message or "Colocate frente a la camara"
        status = VisionStatus(
            timestamp=now_dt,
            backend=self.detector.backend,
            available=self.detector.available,
            face_found=face_found,
            calibrating=calibrating,
            calibration_progress=self.calibration_progress,
            threshold=self.blink_detector.threshold,
            message=message,
        )

        self.bus.publish("blink.metrics", blink)
        self.bus.publish("vision.status", status)
        self.exposure_bus.publish_metrics(exposure)

        ambient = self.ambient_state.latest() if self.ambient_state is not None else None
        self.engine.evaluate(blink, exposure, ambient)
