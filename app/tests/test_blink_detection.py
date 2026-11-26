import math
import sys
import tempfile
import types
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest import mock

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fatiga_visual.core.config import Settings
from fatiga_visual.core.events import EventBus
from fatiga_visual.core.models import BlinkMetrics, VisionFrame
from fatiga_visual.decision import rules
from fatiga_visual.runtime import pipeline as pipeline_module
from fatiga_visual.runtime.pipeline import RuntimePipeline
from fatiga_visual.vision.blink_detector import BlinkDetector
from fatiga_visual.vision.blink_metrics import BlinkMetricsAggregator
from fatiga_visual.vision.calibration import EarCalibration
from fatiga_visual.vision.ear import average_eye_aspect_ratio, eye_aspect_ratios
from tools import blink_eval  # noqa: E402

LEFT_EYE = (362, 385, 387, 263, 373, 380)
RIGHT_EYE = (33, 160, 158, 133, 153, 144)


def make_landmarks(open_height=1.2):
    """478 landmarks con ambos ojos a la altura indicada (en píxeles/100)."""
    landmarks = [
        types.SimpleNamespace(x=0.5, y=0.5, z=0.0, visibility=1.0)
        for _ in range(478)
    ]
    for indices, center_x in ((LEFT_EYE, 34.0), (RIGHT_EYE, 66.0)):
        points = [
            (center_x - 4.0, 50.0),
            (center_x - 2.0, 50.0 - open_height),
            (center_x + 2.0, 50.0 - open_height),
            (center_x + 4.0, 50.0),
            (center_x + 2.0, 50.0 + open_height),
            (center_x - 2.0, 50.0 + open_height),
        ]
        for index, (x, y) in zip(indices, points):
            landmarks[index] = types.SimpleNamespace(
                x=x / 100.0, y=y / 100.0, z=0.0, visibility=1.0
            )
    return landmarks


class EarPerEyeTests(unittest.TestCase):
    def test_returns_both_eyes(self):
        landmarks = make_landmarks(1.2)
        left, right = eye_aspect_ratios(landmarks, 100, 100)
        self.assertAlmostEqual(left, 0.3, places=4)
        self.assertAlmostEqual(right, 0.3, places=4)
        self.assertAlmostEqual(
            average_eye_aspect_ratio(landmarks, 100, 100), 0.3, places=4
        )

    def test_closed_landmarks_have_lower_ear(self):
        open_ear = average_eye_aspect_ratio(make_landmarks(1.2), 100, 100)
        closed_ear = average_eye_aspect_ratio(make_landmarks(0.3), 100, 100)
        self.assertLess(closed_ear, open_ear)


class TimedBlinkDetectorTests(unittest.TestCase):
    def test_timed_blink_reports_duration(self):
        detector = BlinkDetector(threshold=0.21, min_closed_frames=2)
        start = 10.0
        self.assertIsNone(detector.update(0.30, start))
        self.assertIsNone(detector.update(0.15, start + 0.04))
        self.assertEqual(detector.update(0.15, start + 0.08), "closed")
        self.assertEqual(detector.update(0.15, start + 0.12), None)
        event = detector.update(0.30, start + 0.16)
        self.assertEqual(event, "opened")
        self.assertAlmostEqual(detector.last_duration_ms, 120.0, places=0)
        self.assertEqual(detector.blinks, 1)

    def test_hysteresis_keeps_closure_between_thresholds(self):
        detector = BlinkDetector(
            threshold=0.21, reopen_margin=0.05, min_closed_frames=2
        )
        detector.update(0.30, 0.0)
        detector.update(0.15, 0.04)
        self.assertEqual(detector.update(0.15, 0.08), "closed")
        # 0.24 está por encima del umbral pero por debajo del reopen (0.26).
        self.assertIsNone(detector.update(0.24, 0.12))
        self.assertTrue(detector.is_closed)
        self.assertEqual(detector.update(0.30, 0.16), "opened")

    def test_long_closure_is_not_counted_as_blink(self):
        detector = BlinkDetector(
            threshold=0.21,
            min_closed_frames=2,
            max_blink_duration_ms=800,
        )
        self.assertIsNone(detector.update(0.30, 0.0))
        self.assertIsNone(detector.update(0.10, 0.04))
        self.assertEqual(detector.update(0.10, 0.08), "closed")
        self.assertIsNone(detector.update(0.10, 1.40))
        event = detector.update(0.30, 1.60)
        self.assertEqual(event, "long_closure")
        self.assertEqual(detector.long_closures, 1)
        self.assertEqual(detector.blinks, 0)

    def test_blendshape_helps_when_ear_is_in_hysteresis_band(self):
        detector = BlinkDetector(
            threshold=0.21,
            reopen_margin=0.05,
            min_closed_frames=2,
            blink_score_threshold=0.65,
        )
        # EAR en 0.24: por encima del umbral de cierre (0.21) pero por debajo
        # del de reapertura (0.26). La blendshape inicia el cierre.
        self.assertIsNone(detector.update(0.24, 0.0, blink_score=0.05))
        self.assertIsNone(detector.update(0.24, 0.04, blink_score=0.90))
        self.assertEqual(detector.update(0.24, 0.08, blink_score=0.90), "closed")
        self.assertEqual(detector.update(0.30, 0.16, blink_score=0.90), "opened")
        self.assertEqual(detector.blinks, 1)

    def test_stuck_blendshape_does_not_hold_closure(self):
        detector = BlinkDetector(
            threshold=0.21,
            min_closed_frames=2,
            max_blink_duration_ms=800,
            long_closure_seconds=1.5,
            blink_score_threshold=0.65,
        )
        self.assertIsNone(detector.update(0.30, 0.0, blink_score=0.05))
        self.assertIsNone(detector.update(0.12, 0.04, blink_score=0.95))
        self.assertEqual(detector.update(0.12, 0.08, blink_score=0.95), "closed")
        # El EAR ya está abierto aunque la blendshape siga en 0.95: debe
        # cerrar el parpadeo, no esperar a que baje la blendshape.
        self.assertEqual(detector.update(0.30, 0.16, blink_score=0.95), "opened")
        self.assertEqual(detector.blinks, 1)
        self.assertEqual(detector.long_closures, 0)
        self.assertAlmostEqual(detector.last_duration_ms, 120.0, places=0)

    def test_cooldown_suppresses_duplicate_blink(self):
        detector = BlinkDetector(
            threshold=0.21,
            min_closed_frames=1,
            cooldown_seconds=0.20,
        )
        detector.update(0.10, 0.00)
        self.assertEqual(detector.update(0.30, 0.04), "opened")
        detector.update(0.10, 0.08)
        self.assertIsNone(detector.update(0.30, 0.12))
        self.assertEqual(detector.blinks, 1)


class CalibrationTests(unittest.TestCase):
    def test_not_ready_returns_fallback(self):
        calibration = EarCalibration(seconds=2.0, min_samples=5, fallback=0.22)
        calibration.start(0.0)
        for index in range(4):
            calibration.add(0.30, index * 0.1)
        self.assertFalse(calibration.ready)
        self.assertEqual(calibration.threshold(), 0.22)
        self.assertLess(calibration.progress(0.4), 1.0)

    def test_learns_personal_threshold_ignoring_blinks(self):
        calibration = EarCalibration(
            seconds=1.0, min_samples=10, fallback=0.21, ratio=0.72
        )
        calibration.start(0.0)
        samples = [0.30, 0.31, 0.29, 0.32, 0.30, 0.10, 0.31, 0.29, 0.30, 0.32, 0.30]
        for index, ear in enumerate(samples):
            calibration.add(ear, index * 0.1)
        self.assertTrue(calibration.ready)
        self.assertGreaterEqual(calibration.threshold(), 0.12)
        self.assertLess(calibration.threshold(), 0.30)
        self.assertGreater(calibration.stats["open_ear_p75"], 0.29)

    def test_accepts_low_open_ear(self):
        calibration = EarCalibration(
            seconds=0.5, min_samples=5, fallback=0.21
        )
        calibration.start(0.0)
        for index, ear in enumerate([0.14, 0.15, 0.14, 0.15, 0.14, 0.15]):
            calibration.add(ear, index * 0.1)
        self.assertTrue(calibration.ready)
        # Con ojos pequeños/cámara lejos el umbral baja con el usuario, pero
        # nunca por debajo del floor de seguridad.
        self.assertGreaterEqual(calibration.threshold(), 0.06)
        self.assertLess(calibration.threshold(), 0.12)

    def test_progress_does_not_reach_one_before_ready(self):
        calibration = EarCalibration(seconds=1.0, min_samples=10)
        calibration.start(0.0)
        calibration.add(0.30, 0.1)
        calibration.add(0.31, 0.2)
        # Pasa mucho tiempo pero faltan muestras: sigue sin estar lista y no
        # debe mostrar 100%.
        self.assertFalse(calibration.ready)
        self.assertLess(calibration.progress(5.0), 1.0)

    def test_rejects_implausible_high_ear(self):
        calibration = EarCalibration(seconds=0.5, min_samples=4)
        calibration.start(0.0)
        samples = [0.30, 0.31, 0.29, 0.80, 0.90, 0.30, 0.30]
        for index, ear in enumerate(samples):
            calibration.add(ear, index * 0.1)
        self.assertTrue(calibration.ready)
        self.assertLess(calibration.threshold(), 0.25)
        self.assertEqual(calibration.stats["samples"], 4)

    def test_high_outliers_do_not_inflate_threshold(self):
        calibration = EarCalibration(seconds=1.0, min_samples=10)
        calibration.start(0.0)
        samples = [0.30] * 20 + [0.48, 0.49, 0.47]
        for index, ear in enumerate(samples):
            calibration.add(ear, index * 0.05)
        self.assertTrue(calibration.ready)
        # El p75 se calcula sobre el núcleo recortado; unos pocos valores
        # altos no deben llevar el umbral al techo.
        self.assertLess(calibration.threshold(), 0.25)

    def test_rejects_corrupt_saved_calibration(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "calibration.json"
            path.write_text(
                '{"threshold": 0.28, "ready": true, '
                '"stats": {"median": 0.54, "open_ear_p75": 0.63}}',
                encoding="utf-8",
            )
            calibration = EarCalibration(fallback=0.21)
            self.assertFalse(calibration.load(path))
            self.assertEqual(calibration.threshold(), 0.21)

    def test_save_and_load_roundtrip(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "calibration.json"
            calibration = EarCalibration(seconds=0.4, min_samples=4)
            calibration.start(0.0)
            for index, ear in enumerate([0.30, 0.31, 0.29, 0.30, 0.31]):
                calibration.add(ear, index * 0.1)
            self.assertTrue(calibration.ready)
            self.assertTrue(calibration.save(path))

            restored = EarCalibration()
            self.assertTrue(restored.load(path))
            self.assertTrue(restored.ready)
            self.assertAlmostEqual(
                restored.threshold(), calibration.threshold(), places=4
            )


class AggregatorTests(unittest.TestCase):
    def test_rate_duration_and_inter_blink(self):
        aggregator = BlinkMetricsAggregator(window_seconds=60)
        start = datetime(2026, 1, 1, 12, 0, 0)
        aggregator.start(start)
        aggregator.add_blink(start + timedelta(seconds=10), duration_ms=150)
        aggregator.add_blink(start + timedelta(seconds=14), duration_ms=170)
        aggregator.add_blink(start + timedelta(seconds=18), duration_ms=160)
        snapshot = aggregator.snapshot(timestamp=start + timedelta(seconds=30))
        self.assertEqual(snapshot.blinks, 3)
        self.assertAlmostEqual(snapshot.blink_rate, 6.0, places=1)
        self.assertAlmostEqual(snapshot.mean_blink_duration_ms, 160.0, places=1)
        self.assertAlmostEqual(snapshot.inter_blink_seconds, 4.0, places=1)

    def test_perclos_counts_closed_time(self):
        aggregator = BlinkMetricsAggregator(window_seconds=60)
        start = datetime(2026, 1, 1, 12, 0, 0)
        aggregator.start(start)
        aggregator.set_eyes_closed(True, start + timedelta(seconds=10))
        aggregator.set_eyes_closed(False, start + timedelta(seconds=16))
        aggregator.set_eyes_closed(True, start + timedelta(seconds=20))
        aggregator.set_eyes_closed(False, start + timedelta(seconds=22))
        snapshot = aggregator.snapshot(timestamp=start + timedelta(seconds=30))
        self.assertAlmostEqual(snapshot.perclos, 8.0 / 30.0, places=3)

    def test_long_closures_are_counted(self):
        aggregator = BlinkMetricsAggregator(window_seconds=60)
        start = datetime(2026, 1, 1, 12, 0, 0)
        aggregator.start(start)
        aggregator.add_long_closure(start + timedelta(seconds=5), duration_ms=1200)
        aggregator.add_long_closure(start + timedelta(seconds=9), duration_ms=1500)
        snapshot = aggregator.snapshot(timestamp=start + timedelta(seconds=20))
        self.assertEqual(snapshot.long_closures, 2)
        self.assertEqual(snapshot.blinks, 0)


class FakeSequenceDetector:
    backend = "fake"
    available = True

    def __init__(self, heights):
        self.heights = list(heights)
        self.index = 0
        self.error = ""

    def process(self, frame, timestamp=None):
        height = self.heights[min(self.index, len(self.heights) - 1)]
        self.index += 1
        return VisionFrame(
            timestamp=datetime.now(),
            image=frame,
            landmarks=make_landmarks(height),
            blink_score=None,
            confidence=1.0,
        )

    def close(self):
        pass


class FakeCamera:
    """Cámara mínima: solo responde a state() como CameraStream."""

    def __init__(self, state="running"):
        self._state = state

    def state(self):
        return self._state


class PipelineIntegrationTests(unittest.TestCase):
    def _pipeline(self, heights, directory):
        settings = Settings(
            {
                "vision": {
                    "auto_calibrate": False,
                    "use_blendshapes": False,
                    "smoothing_alpha": 1.0,
                    "calibration_path": str(Path(directory) / "calibration.json"),
                    "ear_threshold": 0.21,
                    "min_closed_frames": 2,
                    "max_blink_duration_ms": 800,
                },
                "runtime": {"frame_interval_ms": 40},
            }
        )
        fake = FakeSequenceDetector(heights)
        with mock.patch.object(
            pipeline_module, "FaceLandmarkDetector", return_value=fake
        ):
            pipeline = RuntimePipeline(settings, EventBus())
        pipeline.auto_calibrate = False
        pipeline.calibration.reset()
        pipeline.blink_detector.set_threshold(0.21, 0.04)
        return pipeline

    def test_end_to_end_blink_is_counted(self):
        heights = [1.2] * 5 + [0.3] * 3 + [1.2] * 5
        with tempfile.TemporaryDirectory() as directory:
            pipeline = self._pipeline(heights, directory)
            frame = np.zeros((100, 100, 3), dtype=np.uint8)
            for index in range(len(heights)):
                pipeline._process_frame(frame, index * 0.04)
            self.assertEqual(pipeline.blink_detector.blinks, 1)
            self.assertEqual(pipeline.aggregator.total_blinks, 1)
            self.assertGreater(pipeline.blink_detector.last_duration_ms, 50)

    def test_end_to_end_long_closure_is_classified(self):
        heights = [1.2] * 5 + [0.3] * 30 + [1.2] * 5
        with tempfile.TemporaryDirectory() as directory:
            pipeline = self._pipeline(heights, directory)
            frame = np.zeros((100, 100, 3), dtype=np.uint8)
            for index in range(len(heights)):
                pipeline._process_frame(frame, index * 0.04)
            self.assertEqual(pipeline.blink_detector.blinks, 0)
            self.assertEqual(pipeline.aggregator.total_long_closures, 1)

    def test_status_waits_for_face_before_calibrating(self):
        with tempfile.TemporaryDirectory() as directory:
            settings = Settings(
                {
                    "vision": {
                        "auto_calibrate": True,
                        "use_blendshapes": False,
                        "smoothing_alpha": 1.0,
                        "calibration_seconds": 1.0,
                        "calibration_min_samples": 4,
                        "calibration_path": str(Path(directory) / "calibration.json"),
                        "ear_threshold": 0.21,
                    },
                    "runtime": {"frame_interval_ms": 40},
                }
            )
            bus = EventBus()
            statuses = []
            bus.subscribe("vision.status", statuses.append)
            fake = FakeSequenceDetector([1.2] * 20)
            with mock.patch.object(
                pipeline_module, "FaceLandmarkDetector", return_value=fake
            ):
                pipeline = RuntimePipeline(
                    settings, bus, camera=FakeCamera("running")
                )

            # Cámara encendida pero sin rostro: no debe decir "Calibrando".
            pipeline._sample(0.5, 1.0)
            status = statuses[-1]
            self.assertFalse(status.calibrating)
            self.assertEqual(status.message, "Colocate frente a la camara")

            # Primer fotograma con rostro: ahora sí empieza la calibración.
            frame = np.zeros((100, 100, 3), dtype=np.uint8)
            pipeline._process_frame(frame, 1.0)
            pipeline._sample(0.5, 1.1)
            status = statuses[-1]
            self.assertTrue(status.calibrating)
            self.assertEqual(status.message, "")

    def test_calibration_waits_for_first_frame(self):
        with tempfile.TemporaryDirectory() as directory:
            settings = Settings(
                {
                    "vision": {
                        "auto_calibrate": True,
                        "use_blendshapes": False,
                        "smoothing_alpha": 1.0,
                        "calibration_seconds": 1.0,
                        "calibration_min_samples": 4,
                        "calibration_path": str(Path(directory) / "calibration.json"),
                        "ear_threshold": 0.21,
                    },
                    "runtime": {"frame_interval_ms": 40},
                }
            )
            fake = FakeSequenceDetector([1.2] * 20)
            with mock.patch.object(
                pipeline_module, "FaceLandmarkDetector", return_value=fake
            ):
                pipeline = RuntimePipeline(settings, EventBus())

            # Sin cámara/frames no se consume tiempo de calibración.
            self.assertFalse(pipeline._calibration_started)
            self.assertEqual(pipeline.calibration_progress, 0.0)

            frame = np.zeros((100, 100, 3), dtype=np.uint8)
            pipeline._process_frame(frame, 0.0)
            self.assertTrue(pipeline._calibration_started)
            self.assertGreater(pipeline.calibration_progress, 0.0)
            self.assertFalse(pipeline.calibration.ready)

            for step in range(1, 12):
                pipeline._process_frame(frame, step * 0.1)
            self.assertTrue(pipeline.calibration.ready)
            self.assertAlmostEqual(
                pipeline.blink_detector.threshold,
                pipeline.calibration.threshold(),
                places=4,
            )


class ReferenceSequenceTests(unittest.TestCase):
    """Señal de referencia determinista: 5 parpadeos reales y ruido de 1 cuadro."""

    FPS = 30.0
    THRESHOLD = 0.21
    REAL_BLINKS = (1.0, 2.5, 4.0, 6.2, 8.1)
    NOISE_DIPS = (1.8, 3.3, 5.0, 7.0, 9.0)
    BLINK_FRAMES = 4
    OPEN_EAR = 0.30
    CLOSED_EAR = 0.10

    def _settings(self, use_blendshapes=False):
        return Settings(
            {
                "vision": {
                    "min_closed_frames": 2,
                    "max_closed_frames": 15,
                    "reopen_margin": 0.02,
                    "min_blink_duration_ms": 0.0,
                    "max_blink_duration_ms": 800.0,
                    "long_closure_seconds": 1.5,
                    "blink_cooldown_seconds": 0.06,
                    "blink_score_threshold": 0.65,
                    "use_blendshapes": use_blendshapes,
                }
            }
        )

    def _rows(self):
        step = 1.0 / self.FPS
        rows = []
        for index in range(int(10.0 * self.FPS)):
            moment = round(index * step, 3)
            ear = self.OPEN_EAR + 0.004 * math.sin(index * 0.7)
            closed_real = 0
            for start in self.REAL_BLINKS:
                if start <= moment < start + self.BLINK_FRAMES * step:
                    ear = self.CLOSED_EAR
                    closed_real = 1
            for dip in self.NOISE_DIPS:
                if abs(moment - dip) < step / 2.0:
                    ear = 0.15
            rows.append(
                {
                    "time": f"{moment:.3f}",
                    "ear": f"{ear:.6f}",
                    "closed_real": str(closed_real),
                    "blink_score": "",
                }
            )
        return rows

    def test_reference_sequence_has_five_blinks_and_no_false_positives(self):
        rows = self._rows()
        real = blink_eval.real_blink_times(rows)
        detected = blink_eval.detected_blink_times(
            rows, self.THRESHOLD, self._settings()
        )
        metrics = blink_eval.event_metrics(real, detected, tolerance=0.25)

        self.assertEqual(real, list(self.REAL_BLINKS))
        self.assertEqual(len(detected), len(self.REAL_BLINKS))
        for start, found in zip(self.REAL_BLINKS, detected):
            self.assertAlmostEqual(found, start + 1.0 / self.FPS, delta=0.002)
        self.assertEqual(metrics["tp"], 5)
        self.assertEqual(metrics["fp"], 0)
        self.assertEqual(metrics["fn"], 0)
        self.assertEqual(metrics["precision"], 1.0)
        self.assertEqual(metrics["accuracy"], 1.0)

    def test_single_frame_dip_is_not_confirmed(self):
        detector = BlinkDetector(
            threshold=self.THRESHOLD,
            min_closed_frames=2,
            reopen_margin=0.02,
            cooldown_seconds=0.06,
        )
        self.assertIsNone(detector.update(0.30, 0.000))
        self.assertIsNone(detector.update(0.15, 0.033))
        self.assertIsNone(detector.update(0.30, 0.066))
        self.assertEqual(detector.blinks, 0)
        self.assertIsNone(detector.last_event)

    def test_evaluator_replays_blendshape_from_reference(self):
        rows = [
            {"time": "0.000", "ear": "0.30", "blink_score": "0.05", "closed_real": "0"},
            {"time": "0.033", "ear": "0.22", "blink_score": "0.90", "closed_real": "1"},
            {"time": "0.066", "ear": "0.22", "blink_score": "0.90", "closed_real": "1"},
            {"time": "0.100", "ear": "0.30", "blink_score": "0.90", "closed_real": "0"},
        ]
        detected = blink_eval.detected_blink_times(
            rows, self.THRESHOLD, self._settings(use_blendshapes=True)
        )
        self.assertEqual(detected, [0.066])


class FatigueRuleTests(unittest.TestCase):
    THRESHOLDS = dict(Settings({}).section("thresholds"))

    def test_warmup_suppresses_low_rate_alert(self):
        blink = BlinkMetrics(
            timestamp=datetime.now(),
            blinks=1,
            blink_rate=5.0,
            elapsed_seconds=5.0,
        )
        self.assertIsNone(rules.low_blink_rate(blink, None, None, self.THRESHOLDS))

    def test_long_closure_triggers_recommendation(self):
        blink = BlinkMetrics(
            timestamp=datetime.now(),
            blinks=10,
            blink_rate=18.0,
            perclos=0.22,
            long_closures=4,
            elapsed_seconds=60.0,
        )
        result = rules.prolonged_eye_closure(blink, None, None, self.THRESHOLDS)
        self.assertIsNotNone(result)
        self.assertEqual(result.id, "eye-closure")
        self.assertEqual(result.severity, "high")

    def test_perclos_warmup_suppresses_early_alert(self):
        blink = BlinkMetrics(
            timestamp=datetime.now(),
            blinks=3,
            blink_rate=18.0,
            perclos=0.30,
            long_closures=0,
            elapsed_seconds=20.0,
        )
        self.assertIsNone(rules.prolonged_eye_closure(blink, None, None, self.THRESHOLDS))

    def test_perclos_only_alert_uses_perclos_wording(self):
        blink = BlinkMetrics(
            timestamp=datetime.now(),
            blinks=18,
            blink_rate=18.0,
            perclos=0.22,
            long_closures=0,
            elapsed_seconds=60.0,
        )
        result = rules.prolonged_eye_closure(blink, None, None, self.THRESHOLDS)
        self.assertIsNotNone(result)
        self.assertEqual(result.id, "eye-closure")
        self.assertIn("PERCLOS", result.title)
        self.assertNotIn("cierres oculares prolongados", result.message)

    def test_long_closure_alert_is_not_blocked_by_warmup(self):
        blink = BlinkMetrics(
            timestamp=datetime.now(),
            blinks=4,
            blink_rate=18.0,
            perclos=0.05,
            long_closures=3,
            elapsed_seconds=20.0,
        )
        result = rules.prolonged_eye_closure(blink, None, None, self.THRESHOLDS)
        self.assertIsNotNone(result)
        self.assertIn("cierres oculares prolongados", result.message)

    def test_low_confidence_is_ignored(self):
        blink = BlinkMetrics(
            timestamp=datetime.now(),
            blinks=1,
            blink_rate=2.0,
            perclos=0.5,
            long_closures=8,
            confidence=0.1,
            elapsed_seconds=60.0,
        )
        self.assertIsNone(rules.low_blink_rate(blink, None, None, self.THRESHOLDS))
        self.assertIsNone(rules.prolonged_eye_closure(blink, None, None, self.THRESHOLDS))


if __name__ == "__main__":
    unittest.main()
