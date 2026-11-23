import sys
import unittest
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fatiga_visual.core.config import DEFAULTS, Settings, load_settings, settings_path
from fatiga_visual.core.events import EventBus
from fatiga_visual.core.models import AmbientReading, BlinkMetrics, ExposureMetrics
from fatiga_visual.decision import rules
from fatiga_visual.decision.engine import DecisionEngine

# Mapping completo: las reglas ya no tienen fallbacks numéricos propios.
THRESHOLDS = dict(Settings({}).section("thresholds"))


def blink(rate, confidence=1.0):
    return BlinkMetrics(
        timestamp=datetime.now(), blinks=100, blink_rate=rate, confidence=confidence
    )


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

    def test_cooldown_from_config_prevents_duplicates(self):
        self.settings = Settings({"thresholds": {"cooldown_seconds": 300}})
        engine = DecisionEngine(self.settings)
        first = engine.evaluate(blink(8), exposure(5), ambient())
        second = engine.evaluate(blink(8), exposure(5), ambient())
        self.assertEqual(len(first), 1)
        self.assertEqual(second, [])

    def test_zero_cooldown_from_config_allows_repeat(self):
        self.settings = Settings({"thresholds": {"cooldown_seconds": 0}})
        engine = DecisionEngine(self.settings)
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


class ConfiguredThresholdsTests(unittest.TestCase):
    """SCRUM-32: una sola fuente, documentada, sin números fijos en el código."""

    def test_yaml_mirrors_defaults(self):
        self.assertEqual(load_settings().section("thresholds"), DEFAULTS["thresholds"])

    def test_every_yaml_threshold_has_justification(self):
        lines = settings_path().read_text(encoding="utf-8").splitlines()
        documented = []
        inside = False
        for line in lines:
            if line.startswith("thresholds:"):
                inside = True
                continue
            if inside and line and not line[0].isspace() and not line.startswith("#"):
                break
            if (
                inside
                and line.startswith("  ")
                and ":" in line
                and not line.lstrip().startswith("#")
            ):
                documented.append((line.strip().split(":", 1)[0], "#" in line))
        self.assertEqual({key for key, _ in documented}, set(DEFAULTS["thresholds"]))
        for key, has_comment in documented:
            self.assertTrue(has_comment, f"{key} sin justificación en settings.yaml")

    def test_no_hardcoded_fallbacks_in_rules_or_engine(self):
        source_dir = Path(__file__).resolve().parents[1] / "src" / "fatiga_visual"
        rules_source = (source_dir / "decision" / "rules.py").read_text(encoding="utf-8")
        engine_source = (source_dir / "decision" / "engine.py").read_text(encoding="utf-8")
        self.assertNotRegex(rules_source, r"thresholds\.get\(")
        self.assertNotRegex(engine_source, r"cooldown_seconds\s*=\s*\d")
        self.assertGreaterEqual(rules_source.count('thresholds["'), 10)

    def test_changing_blink_rate_low_changes_the_rule(self):
        thresholds = Settings({"thresholds": {"blink_rate_low": 25}}).section("thresholds")
        self.assertIsNone(rules.low_blink_rate(blink(20), None, None, THRESHOLDS))
        result = rules.low_blink_rate(blink(20), None, None, thresholds)
        self.assertEqual(result.id, "blink-low")

    def test_min_confidence_comes_from_thresholds(self):
        unreliable = blink(8, confidence=0.2)
        default = Settings({}).section("thresholds")
        relaxed = Settings({"thresholds": {"min_confidence": 0.1}}).section("thresholds")
        self.assertIsNone(rules.low_blink_rate(unreliable, None, None, default))
        self.assertIsNotNone(rules.low_blink_rate(unreliable, None, None, relaxed))


if __name__ == "__main__":
    unittest.main()
