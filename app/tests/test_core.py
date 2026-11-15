import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fatiga_visual.core.config import Settings
from fatiga_visual.core.events import EventBus
from fatiga_visual.ui.state import AppState


class SettingsTests(unittest.TestCase):
    def test_reads_nested_values(self):
        settings = Settings({"camera": {"index": 2}})
        self.assertEqual(settings.get("camera.index"), 2)

    def test_falls_back_to_defaults(self):
        settings = Settings({})
        self.assertEqual(settings.get("thresholds.blink_rate_low"), 15)

    def test_missing_key_returns_custom_default(self):
        settings = Settings({})
        self.assertEqual(settings.get("no.existe", "fallback"), "fallback")

    def test_section_merges_defaults(self):
        settings = Settings({"thresholds": {"lux_min": 250}})
        section = settings.section("thresholds")
        self.assertEqual(section["lux_min"], 250)
        self.assertIn("blink_rate_low", section)


class EventBusTests(unittest.TestCase):
    def test_publish_reaches_subscribers(self):
        bus = EventBus()
        received = []
        bus.subscribe("tick", received.append)
        bus.publish("tick", 42)
        self.assertEqual(received, [42])

    def test_unsubscribe(self):
        bus = EventBus()
        received = []
        handler = received.append
        bus.subscribe("tick", handler)
        bus.unsubscribe("tick", handler)
        bus.publish("tick", 1)
        self.assertEqual(received, [])


class AppStateTests(unittest.TestCase):
    def setUp(self):
        self.state = AppState(Settings({}), EventBus())

    def test_tick_advances_session(self):
        start = self.state.session_seconds
        self.state.tick()
        self.assertEqual(self.state.session_seconds, start + 1)

    def test_pause_stops_clock(self):
        self.state.toggle_running()
        start = self.state.session_seconds
        self.state.tick()
        self.assertEqual(self.state.session_seconds, start)

    def test_completing_recommendation_removes_it(self):
        recommendation = self.state.primary_recommendation()
        self.state.complete_recommendation(recommendation.id)
        self.assertTrue(all(item.id != recommendation.id for item in self.state.recommendations))

    def test_ambient_update_refreshes_state(self):
        reading = self.state.ambient.__class__(
            timestamp=self.state.ambient.timestamp,
            lux=500,
            temperature_c=24.0,
            humidity=50.0,
        )
        self.state.update_ambient(reading)
        self.assertEqual(self.state.ambient.lux, 500)


if __name__ == "__main__":
    unittest.main()
