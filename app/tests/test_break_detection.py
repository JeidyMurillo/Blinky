import sys
import types
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fatiga_visual.core.config import Settings
from fatiga_visual.core.events import EventBus
from fatiga_visual.core.models import BreakEvent, VisionFrame
from fatiga_visual.exposure.breaks import BreakDetector
from fatiga_visual.runtime import pipeline as pipeline_module
from fatiga_visual.runtime.pipeline import RuntimePipeline
from fatiga_visual.runtime.simulated import SimulatedPipeline
from fatiga_visual.ui.state import AppState


def make_landmarks(count=468):
    return [
        types.SimpleNamespace(x=(index % 100) / 100.0, y=(index // 100) / 5.0)
        for index in range(count)
    ]


class BreakDetectorTests(unittest.TestCase):
    def setUp(self):
        self.start = datetime(2026, 1, 1, 12, 0, 0)
        self.detector = BreakDetector(min_break_seconds=20)

    def at(self, seconds):
        return self.start + timedelta(seconds=seconds)

    def test_short_absence_is_not_a_break(self):
        self.assertIsNone(self.detector.update(True, self.at(0)))
        self.assertIsNone(self.detector.update(False, self.at(1)))
        self.assertIsNone(self.detector.update(False, self.at(10)))
        self.assertIsNone(self.detector.update(True, self.at(11)))
        self.assertFalse(self.detector.active)
        self.assertIsNone(self.detector.absent_since)

    def test_long_absence_emits_start_then_finish(self):
        self.assertIsNone(self.detector.update(True, self.at(0)))
        self.assertIsNone(self.detector.update(False, self.at(5)))

        started = self.detector.update(False, self.at(25), continuous_seconds=900)
        self.assertIsNotNone(started)
        self.assertEqual(started.kind, "started")
        self.assertEqual(started.started_at, self.at(5))
        self.assertEqual(started.continuous_before_seconds, 900)
        self.assertTrue(self.detector.active)

        # Mientras sigue ausente no se repite el evento de inicio.
        self.assertIsNone(self.detector.update(False, self.at(40)))

        finished = self.detector.update(True, self.at(50))
        self.assertIsNotNone(finished)
        self.assertEqual(finished.kind, "finished")
        self.assertEqual(finished.started_at, self.at(5))
        self.assertEqual(finished.duration_seconds, 45)
        self.assertEqual(finished.continuous_before_seconds, 900)
        self.assertFalse(self.detector.active)
        self.assertIsNone(self.detector.update(True, self.at(51)))

    def test_reset_discards_pending_absence(self):
        self.detector.update(False, self.at(0))
        self.detector.reset()
        self.assertIsNone(self.detector.update(False, self.at(60)))
        self.assertFalse(self.detector.active)


class FakeDetector:
    backend = "fake"
    available = True
    error = ""

    def __init__(self, landmarks):
        self.landmarks = landmarks

    def process(self, frame, timestamp=None):
        return VisionFrame(
            timestamp=datetime.now(),
            image=frame,
            landmarks=self.landmarks,
            confidence=1.0,
        )

    def close(self):
        pass


class FakeCamera:
    def state(self):
        return "running"


class FakeDatetime:
    current = datetime(2026, 1, 1, 12, 0, 0)

    @classmethod
    def now(cls):
        return cls.current


class PipelineBreakTests(unittest.TestCase):
    def _pipeline(self, bus):
        settings = Settings(
            {
                "vision": {
                    "auto_calibrate": False,
                    "use_blendshapes": False,
                    "face_grace_seconds": 0.0,
                    "calibration_path": "",
                },
                "exposure": {"break_min_seconds": 1},
            }
        )
        fake = FakeDetector(make_landmarks())
        with mock.patch.object(
            pipeline_module, "FaceLandmarkDetector", return_value=fake
        ):
            return RuntimePipeline(settings, bus, camera=FakeCamera())

    def test_detects_break_resets_counter_and_publishes_both_events(self):
        bus = EventBus()
        events = []
        bus.subscribe("exposure.break", events.append)
        pipeline = self._pipeline(bus)
        base = FakeDatetime.current

        with mock.patch.object(pipeline_module, "datetime", FakeDatetime):
            # Presente: el contador avanza.
            pipeline._face_found = True
            pipeline._last_face_at = 1.0
            for second in (1, 2):
                FakeDatetime.current = base + timedelta(seconds=second)
                pipeline._sample(1.0, float(second))
            self.assertEqual(pipeline.timer.continuous_seconds, 2)

            # Ausencia corta: no cuenta como pausa.
            pipeline._face_found = False
            FakeDatetime.current = base + timedelta(seconds=3)
            pipeline._sample(1.0, 3.0)
            self.assertEqual(events, [])
            self.assertEqual(pipeline.timer.continuous_seconds, 3)

            # Se supera el mínimo: se publica el inicio y se reinicia el conteo.
            FakeDatetime.current = base + timedelta(seconds=4)
            pipeline._sample(1.0, 4.0)
            self.assertEqual([event.kind for event in events], ["started"])
            self.assertEqual(pipeline.timer.breaks_taken, 1)
            self.assertEqual(pipeline.timer.continuous_seconds, 0)
            self.assertEqual(events[-1].continuous_before_seconds, 3)

            # Vuelve el rostro: se cierra la pausa con su duración.
            pipeline._face_found = True
            pipeline._last_face_at = 6.0
            FakeDatetime.current = base + timedelta(seconds=6)
            pipeline._sample(1.0, 6.0)
            self.assertEqual(
                [event.kind for event in events], ["started", "finished"]
            )
            self.assertEqual(events[-1].duration_seconds, 3)
            self.assertEqual(pipeline.timer.continuous_seconds, 1)

    def test_camera_off_does_not_count_as_break(self):
        bus = EventBus()
        events = []
        bus.subscribe("exposure.break", events.append)
        pipeline = self._pipeline(bus)
        with mock.patch.object(pipeline_module, "datetime", FakeDatetime):
            with mock.patch.object(pipeline, "_camera_state", return_value="stopped"):
                pipeline._sample(1.0, 10.0)
        self.assertEqual(events, [])
        self.assertFalse(pipeline.break_detector.active)


class SimulatedBreakTests(unittest.TestCase):
    def test_publishes_break_when_continuous_goal_is_reached(self):
        bus = EventBus()
        events = []
        bus.subscribe("exposure.break", events.append)
        settings = Settings(
            {
                "session": {"initial_continuous_seconds": 1200},
                "thresholds": {"continuous_minutes": 20},
            }
        )
        pipeline = SimulatedPipeline(settings, bus, simulate_ambient=False)
        pipeline._tick(0.0)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].kind, "finished")
        self.assertEqual(events[0].duration_seconds, 20.0)
        self.assertEqual(pipeline.timer.continuous_seconds, 0)
        self.assertEqual(pipeline.timer.breaks_taken, 1)


class AppStateBreakTests(unittest.TestCase):
    def test_tracks_active_and_completed_breaks(self):
        bus = EventBus()
        state = AppState(Settings({}), bus, simulate=False, seed_demo=False)
        topics = []
        state.subscribe(topics.append)
        started_at = datetime(2026, 1, 1, 12, 0, 0)
        started = BreakEvent(
            timestamp=started_at,
            started_at=started_at,
            kind="started",
            continuous_before_seconds=600,
        )
        finished = BreakEvent(
            timestamp=started_at + timedelta(seconds=25),
            started_at=started_at,
            kind="finished",
            duration_seconds=25,
        )

        bus.publish("exposure.break", started)
        self.assertTrue(state.break_active)
        self.assertIs(state.active_break, started)
        self.assertEqual(state.break_history, [])

        bus.publish("exposure.break", finished)
        self.assertFalse(state.break_active)
        self.assertIs(state.last_break, finished)
        self.assertEqual(len(state.break_history), 1)
        self.assertEqual(state.last_break_at, finished.timestamp)
        self.assertIn("break", topics)

        bus.publish("exposure.break", started)
        state.set_camera(False)
        self.assertFalse(state.break_active)
        self.assertEqual(len(state.break_history), 1)


if __name__ == "__main__":
    unittest.main()
