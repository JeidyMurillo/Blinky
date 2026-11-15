import sys
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fatiga_visual.core.config import Settings
from fatiga_visual.core.events import EventBus
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


if __name__ == "__main__":
    unittest.main()
