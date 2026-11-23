import sys
import unittest
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fatiga_visual.core.config import Settings
from fatiga_visual.core.events import EventBus
from fatiga_visual.core.models import AmbientReading, BlinkMetrics, ExposureMetrics
from fatiga_visual.decision import rules
from fatiga_visual.decision.engine import DecisionEngine

THRESHOLDS = {
    "blink_rate_low": 15,
    "continuous_minutes": 20,
    "lux_min": 300,
    "lux_max": 1000,
    "temperature_min": 18,
    "temperature_max": 26,
    "humidity_min": 30,
    "humidity_max": 60,
}


def blink(rate):
    return BlinkMetrics(timestamp=datetime.now(), blinks=100, blink_rate=rate)


def exposure(minutes):
    return ExposureMetrics(
        timestamp=datetime.now(),
        session_seconds=minutes * 60,
        continuous_seconds=minutes * 60,
        breaks_taken=0,
    )


def ambient(lux=420, temperature=23.4, humidity=48):
    return AmbientReading(
        timestamp=datetime.now(),
        lux=lux,
        temperature_c=temperature,
        humidity=humidity,
    )


class RuleTests(unittest.TestCase):
    def test_low_blink_rate(self):
        result = rules.low_blink_rate(blink(9), exposure(5), ambient(), THRESHOLDS)
        self.assertIsNotNone(result)
        self.assertEqual(result.id, "blink-low")
        self.assertEqual(result.severity, "high")

    def test_normal_blink_rate_ignored(self):
        self.assertIsNone(rules.low_blink_rate(blink(18), exposure(5), ambient(), THRESHOLDS))

    def test_long_exposure(self):
        result = rules.continuous_exposure(blink(18), exposure(21), ambient(), THRESHOLDS)
        self.assertEqual(result.id, "break-20")

    def test_short_exposure_ignored(self):
        self.assertIsNone(rules.continuous_exposure(blink(18), exposure(5), ambient(), THRESHOLDS))

    def test_low_light(self):
        result = rules.ambient_light(blink(18), exposure(5), ambient(lux=120), THRESHOLDS)
        self.assertEqual(result.id, "light-low")

    def test_high_light(self):
        result = rules.ambient_light(blink(18), exposure(5), ambient(lux=1400), THRESHOLDS)
        self.assertEqual(result.id, "light-high")

    def test_good_light_ignored(self):
        self.assertIsNone(rules.ambient_light(blink(18), exposure(5), ambient(lux=500), THRESHOLDS))

    def test_temperature_out_of_range(self):
        high = rules.ambient_temperature(blink(18), exposure(5), ambient(temperature=29), THRESHOLDS)
        low = rules.ambient_temperature(blink(18), exposure(5), ambient(temperature=14), THRESHOLDS)
        self.assertEqual(high.id, "temperature-high")
        self.assertEqual(low.id, "temperature-low")
        self.assertIn("29.0 C", high.message)

    def test_temperature_in_range_ignored(self):
        self.assertIsNone(rules.ambient_temperature(blink(18), exposure(5), ambient(), THRESHOLDS))

    def test_humidity_out_of_range(self):
        dry = rules.ambient_humidity(blink(18), exposure(5), ambient(humidity=20), THRESHOLDS)
        wet = rules.ambient_humidity(blink(18), exposure(5), ambient(humidity=75), THRESHOLDS)
        self.assertEqual(dry.id, "humidity-low")
        self.assertEqual(wet.id, "humidity-high")
        self.assertIn("Toma agua", dry.message)

    def test_humidity_in_range_ignored(self):
        self.assertIsNone(rules.ambient_humidity(blink(18), exposure(5), ambient(), THRESHOLDS))

    def test_ambient_rules_ignore_missing_or_stale_data(self):
        ambient_rules = (
            rules.ambient_light,
            rules.ambient_temperature,
            rules.ambient_humidity,
            rules.combined_blink_light,
        )
        stale = AmbientReading(
            timestamp=datetime.now(),
            lux=120,
            temperature_c=29,
            humidity=20,
            connected=False,
        )
        for rule in ambient_rules:
            self.assertIsNone(rule(blink(18), exposure(5), None, THRESHOLDS))
            self.assertIsNone(rule(blink(8), exposure(5), stale, THRESHOLDS))

    def test_combined_blink_and_bad_light(self):
        result = rules.combined_blink_light(blink(8), exposure(5), ambient(lux=120), THRESHOLDS)
        self.assertEqual(result.id, "blink-light")
        self.assertEqual(result.severity, "high")
        self.assertIn("lampara", result.message)
        # Sin una de las dos condiciones, no se emite el aviso combinado.
        self.assertIsNone(rules.combined_blink_light(blink(18), exposure(5), ambient(lux=120), THRESHOLDS))
        self.assertIsNone(rules.combined_blink_light(blink(8), exposure(5), ambient(lux=500), THRESHOLDS))


class EngineTests(unittest.TestCase):
    def setUp(self):
        self.settings = Settings(
            {"thresholds": THRESHOLDS, "mqtt": {"topics": {"ambient": "fatiga/ambient"}}}
        )

    def test_emits_and_publishes(self):
        bus = EventBus()
        received = []
        bus.subscribe("decision.recommendation", received.append)
        engine = DecisionEngine(self.settings, bus)

        results = engine.evaluate(blink(8), exposure(25), ambient(lux=150))

        self.assertGreaterEqual(len(results), 2)
        self.assertEqual(len(received), len(results))

    def test_cooldown_prevents_duplicates(self):
        engine = DecisionEngine(self.settings, cooldown_seconds=300)
        first = engine.evaluate(blink(8), exposure(5), ambient())
        second = engine.evaluate(blink(8), exposure(5), ambient())
        self.assertEqual(len(first), 1)
        self.assertEqual(second, [])

    def test_zero_cooldown_allows_repeat(self):
        engine = DecisionEngine(self.settings, cooldown_seconds=0)
        engine.evaluate(blink(8), exposure(5), ambient())
        second = engine.evaluate(blink(8), exposure(5), ambient())
        self.assertEqual(len(second), 1)

    def test_ambient_recommendations_are_published(self):
        bus = EventBus()
        received = []
        bus.subscribe("decision.recommendation", received.append)
        engine = DecisionEngine(self.settings, bus)

        results = engine.evaluate(
            blink(18), exposure(5), ambient(lux=120, temperature=29, humidity=20)
        )

        ids = {item.id for item in results}
        self.assertIn("light-low", ids)
        self.assertIn("temperature-high", ids)
        self.assertIn("humidity-low", ids)
        self.assertEqual(len(received), len(results))


if __name__ == "__main__":
    unittest.main()
