import math
import sys
import time
import types
import unittest
from datetime import datetime
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fatiga_visual.ambient.ambient_state import AmbientState
from fatiga_visual.core.config import Settings
from fatiga_visual.core.events import EventBus
from fatiga_visual.core.models import AmbientReading, BlinkMetrics, VisionFrame
from fatiga_visual.runtime import pipeline as pipeline_module
from fatiga_visual.runtime.pipeline import RuntimePipeline
from fatiga_visual.runtime.simulated import SimulatedPipeline
from fatiga_visual.ui.state import AppState


def wait_for(condition, timeout=2.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if condition():
            return True
        time.sleep(0.02)
    return False


class SimulatedRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.settings = Settings(
            {
                "runtime": {
                    "publish_seconds": 0.05,
                    "simulated": {"blink_rate": 18.0, "ambient_seconds": 0.05, "jitter": 0.0},
                },
                "session": {
                    "initial_seconds": 0,
                    "initial_blinks": 0,
                    "initial_continuous_seconds": 0,
                    "initial_breaks": 0,
                },
            }
        )
        self.bus = EventBus()
        self.received = {"blink.metrics": [], "exposure.metrics": [], "ambient.reading": []}
        for topic in self.received:
            self.bus.subscribe(topic, self.received[topic].append)

    def test_publishes_same_events_as_real_pipeline(self):
        pipeline = SimulatedPipeline(self.settings, self.bus)
        pipeline.start()
        try:
            self.assertTrue(wait_for(lambda: len(self.received["blink.metrics"]) > 0))
            self.assertTrue(wait_for(lambda: len(self.received["exposure.metrics"]) > 0))
            self.assertTrue(wait_for(lambda: len(self.received["ambient.reading"]) > 0))
        finally:
            pipeline.stop()

        blink = self.received["blink.metrics"][-1]
        exposure = self.received["exposure.metrics"][-1]
        self.assertGreaterEqual(blink.blink_rate, 4.0)
        self.assertGreaterEqual(exposure.session_seconds, 0)

    def test_stop_is_idempotent(self):
        pipeline = SimulatedPipeline(self.settings, self.bus)
        pipeline.start()
        pipeline.stop()
        pipeline.stop()

    def test_simulated_ambient_values_generate_recommendations(self):
        """Los valores configurados llegan al motor y a las recomendaciones de la UI."""
        settings = Settings(
            {
                "runtime": {
                    "publish_seconds": 0.05,
                    "simulated": {
                        "blink_rate": 18.0,
                        "ambient_seconds": 0.05,
                        "jitter": 0.0,
                        "ambient_lux": 120.0,
                        "ambient_temperature": 29.0,
                        "ambient_humidity": 20.0,
                    },
                }
            }
        )
        state = AppState(settings, self.bus, simulate=False, seed_demo=False)
        received = []
        self.bus.subscribe("decision.recommendation", received.append)
        pipeline = SimulatedPipeline(settings, self.bus)
        pipeline.start()
        try:
            self.assertTrue(wait_for(lambda: len(received) >= 3))
        finally:
            pipeline.stop()

        reading = self.received["ambient.reading"][-1]
        self.assertLess(reading.lux, 300)
        expected = {"light-low", "temperature-high", "humidity-low"}
        self.assertTrue(expected.issubset({item.id for item in received}))
        self.assertTrue(expected.issubset({item.id for item in state.recommendations}))


class ExternalStateTests(unittest.TestCase):
    def test_app_state_does_not_simulate_when_runtime_owns_data(self):
        state = AppState(Settings({}), EventBus(), simulate=False, seed_demo=False)
        start = state.session_seconds
        state.tick()
        self.assertEqual(state.session_seconds, start)
        self.assertEqual(state.recommendations, [])

    def test_exposure_event_updates_state(self):
        bus = EventBus()
        state = AppState(Settings({}), bus, simulate=False, seed_demo=False)
        pipeline = SimulatedPipeline(
            Settings(
                {
                    "runtime": {
                        "publish_seconds": 0.05,
                        "simulated": {"blink_rate": 18.0, "ambient_seconds": 0.05},
                    }
                }
            ),
            bus,
            is_running=lambda: state.running,
        )
        pipeline.start()
        try:
            self.assertTrue(wait_for(lambda: state.session_seconds > 0))
        finally:
            pipeline.stop()
        self.assertTrue(state.drain_events())


class RealPipelineAmbientTests(unittest.TestCase):
    """Las lecturas del nodo IoT (AmbientState) alimentan al motor de reglas."""

    ambient_ids = {
        "light-low",
        "light-high",
        "temperature-low",
        "temperature-high",
        "humidity-low",
        "humidity-high",
        "blink-light",
    }

    def _pipeline(self, bus, ambient_state):
        settings = Settings(
            {
                "vision": {
                    "auto_calibrate": False,
                    "use_blendshapes": False,
                    "face_grace_seconds": 0.0,
                    "calibration_path": "",
                }
            }
        )
        detector = types.SimpleNamespace(
            available=True,
            backend="fake",
            error="",
            process=lambda frame, timestamp=None: VisionFrame(
                timestamp=datetime.now(), image=frame, landmarks=None, confidence=1.0
            ),
            close=lambda: None,
        )
        camera = types.SimpleNamespace(state=lambda: "running")
        with mock.patch.object(pipeline_module, "FaceLandmarkDetector", return_value=detector):
            return RuntimePipeline(settings, bus, camera=camera, ambient_state=ambient_state)

    def _evaluate(self, lux, temperature, humidity, stale=False):
        bus = EventBus()
        received = []
        bus.subscribe("decision.recommendation", received.append)
        reading = AmbientReading(
            timestamp=datetime.now(),
            lux=lux,
            temperature_c=temperature,
            humidity=humidity,
            connected=True,
        )
        if stale:
            # AmbientState marca la lectura vencida con connected=False.
            ambient_state = types.SimpleNamespace(
                latest=lambda: AmbientReading(**{**reading.__dict__, "connected": False})
            )
        else:
            ambient_state = AmbientState(stale_after_seconds=15)
            ambient_state.update(reading)
        pipeline = self._pipeline(bus, ambient_state)
        try:
            pipeline._sample(1.0, time.monotonic())
        finally:
            pipeline.detector.close()
        return {item.id for item in received}

    def test_each_out_of_range_variable_warns(self):
        ids = self._evaluate(lux=120.0, temperature=29.0, humidity=20.0)
        self.assertTrue({"light-low", "temperature-high", "humidity-low"}.issubset(ids))

    def test_in_range_values_warn_nothing(self):
        ids = self._evaluate(lux=500.0, temperature=23.4, humidity=48.0)
        self.assertFalse(self.ambient_ids & ids)

    def test_stale_iot_reading_warns_nothing(self):
        ids = self._evaluate(lux=120.0, temperature=29.0, humidity=20.0, stale=True)
        self.assertFalse(self.ambient_ids & ids)


class BlinkMetricsBusTests(unittest.TestCase):
    """SCRUM-22: métricas periódicas, payload válido y consumo por el motor."""

    def test_blink_metrics_are_periodic_valid_and_reach_the_engine(self):
        settings = Settings(
            {
                "runtime": {
                    "publish_seconds": 0.05,
                    "simulated": {"blink_rate": 5.0, "jitter": 0.0},
                },
                "thresholds": {
                    "blink_rate_low": 15,
                    "blink_warmup_seconds": 0,
                    "continuous_minutes": 20,
                },
                "session": {
                    "initial_seconds": 0,
                    "initial_continuous_seconds": 0,
                    "initial_breaks": 0,
                    "initial_blinks": 0,
                },
            }
        )
        bus = EventBus()
        metrics = []
        recommendations = []
        bus.subscribe("blink.metrics", metrics.append)
        bus.subscribe("decision.recommendation", recommendations.append)

        # Sin ambiente simulado: demuestra que SCRUM-22 no depende del ESP32.
        pipeline = SimulatedPipeline(settings, bus, simulate_ambient=False)
        pipeline.start()
        try:
            self.assertTrue(wait_for(lambda: len(metrics) >= 3))
            self.assertTrue(
                wait_for(lambda: any(item.id == "blink-low" for item in recommendations))
            )
        finally:
            pipeline.stop()

        self.assertGreaterEqual(len(metrics), 3)
        for item in metrics:
            self.assertIsInstance(item, BlinkMetrics)
            for field in (
                "blink_rate",
                "ear",
                "confidence",
                "mean_blink_duration_ms",
                "last_blink_duration_ms",
                "inter_blink_seconds",
                "perclos",
                "elapsed_seconds",
                "calibration_progress",
            ):
                self.assertTrue(math.isfinite(getattr(item, field)), field)
            self.assertGreaterEqual(item.blink_rate, 0.0)
            self.assertLessEqual(item.blink_rate, 120.0)
            self.assertGreaterEqual(item.perclos, 0.0)
            self.assertLessEqual(item.perclos, 1.0)
            self.assertGreaterEqual(item.mean_blink_duration_ms, 0.0)
            self.assertGreaterEqual(item.elapsed_seconds, 0.0)
        self.assertIn("blink-low", {item.id for item in recommendations})


if __name__ == "__main__":
    unittest.main()
