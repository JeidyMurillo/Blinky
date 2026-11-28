import sys
import tempfile
import unittest
from dataclasses import replace
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fatiga_visual.core.config import DEFAULTS, Settings, load_settings, settings_path
from fatiga_visual.core.events import EventBus
from fatiga_visual.core.models import AmbientReading, BlinkMetrics, ExposureMetrics
from fatiga_visual.decision import rules
from fatiga_visual.decision.engine import DecisionEngine
from fatiga_visual.storage.repository import Repository

# Mapping completo: las reglas ya no tienen fallbacks numéricos propios.
THRESHOLDS = dict(Settings({}).section("thresholds"))


def blink(rate, confidence=1.0, elapsed=60):
    return BlinkMetrics(
        timestamp=datetime.now(),
        blinks=100,
        blink_rate=rate,
        elapsed_seconds=elapsed,
        confidence=confidence,
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


class SustainedLowBlinkRateTests(unittest.TestCase):
    def setUp(self):
        self.rule = rules.SustainedLowBlinkRate()
        self.start = datetime(2026, 1, 1, 8, 0, 0)
        self.low = blink(9)

    def evaluate(self, blink_metrics, seconds):
        now = self.start + timedelta(seconds=seconds)
        return self.rule(blink_metrics, None, None, THRESHOLDS, now=now)

    def test_alerts_only_after_window_and_min_samples(self):
        self.assertIsNone(self.evaluate(self.low, 0))
        self.assertIsNone(self.evaluate(self.low, 30))
        result = self.evaluate(self.low, 60)
        self.assertIsNotNone(result)
        self.assertEqual(result.id, "blink-low")
        self.assertIn("umbral de 15", result.message)

    def test_value_at_threshold_is_not_low(self):
        at_limit = blink(15)
        for seconds in (0, 30, 60):
            self.assertIsNone(self.evaluate(at_limit, seconds))
        self.assertIsNone(self.evaluate(blink(14), 90))
        self.assertEqual(self.rule.window.samples, 1)

    def test_missing_data_resets_the_window(self):
        self.assertIsNone(self.evaluate(self.low, 0))
        self.assertIsNone(self.evaluate(None, 10))
        self.assertEqual(self.rule.window.samples, 0)
        self.assertIsNone(self.evaluate(self.low, 20))
        self.assertIsNone(self.evaluate(self.low, 50))
        self.assertEqual(self.rule.window.samples, 2)

    def test_missing_rate_is_ignored(self):
        no_rate = replace(self.low, blink_rate=None)
        self.assertIsNone(self.evaluate(no_rate, 0))
        self.assertEqual(self.rule.window.samples, 0)

    def test_low_confidence_and_warmup_are_ignored(self):
        self.assertIsNone(self.evaluate(replace(self.low, confidence=0.1), 0))
        self.assertIsNone(self.evaluate(blink(9, elapsed=5), 10))
        self.assertEqual(self.rule.window.samples, 0)

    def test_large_gap_restarts_window(self):
        self.assertIsNone(self.evaluate(self.low, 0))
        self.assertIsNone(self.evaluate(self.low, 30))
        self.assertIsNone(self.evaluate(self.low, 120))
        self.assertEqual(self.rule.window.samples, 1)

    def test_recovery_resets_window(self):
        self.assertIsNone(self.evaluate(self.low, 0))
        self.assertIsNone(self.evaluate(blink(18), 30))
        self.assertEqual(self.rule.window.samples, 0)


class TwentyTwentyTwentyTests(unittest.TestCase):
    def setUp(self):
        self.rule = rules.TwentyTwentyTwenty()
        self.start = datetime(2026, 1, 1, 8, 0, 0)

    def _exposure(self, minutes, breaks=0):
        return ExposureMetrics(
            timestamp=self.start,
            session_seconds=int(minutes * 60),
            continuous_seconds=int(minutes * 60),
            breaks_taken=breaks,
        )

    def test_alerts_at_twenty_minutes_with_clear_instructions(self):
        self.assertIsNone(self.rule(None, self._exposure(19), None, THRESHOLDS))
        result = self.rule(None, self._exposure(20), None, THRESHOLDS)

        self.assertIsNotNone(result)
        self.assertEqual(result.id, "break-20")
        self.assertIn("20 pies", result.message)
        self.assertIn("6 m", result.message)
        self.assertIn("20 segundos", result.message)

    def test_does_not_repeat_without_a_valid_break(self):
        self.assertIsNotNone(self.rule(None, self._exposure(20), None, THRESHOLDS))
        for minutes in (21, 25, 40):
            self.assertIsNone(
                self.rule(None, self._exposure(minutes), None, THRESHOLDS)
            )

    def test_rearms_after_a_valid_break(self):
        self.assertIsNotNone(self.rule(None, self._exposure(20), None, THRESHOLDS))
        self.assertIsNone(self.rule(None, self._exposure(25), None, THRESHOLDS))

        after_break = ExposureMetrics(
            timestamp=self.start,
            session_seconds=1500,
            continuous_seconds=0,
            breaks_taken=1,
        )
        self.assertIsNone(self.rule(None, after_break, None, THRESHOLDS))
        self.assertIsNone(self.rule(None, self._exposure(5, breaks=1), None, THRESHOLDS))

        again = self.rule(None, self._exposure(20, breaks=1), None, THRESHOLDS)
        self.assertIsNotNone(again)
        self.assertEqual(again.id, "break-20")

    def test_reset_clears_latch(self):
        self.assertIsNotNone(self.rule(None, self._exposure(20), None, THRESHOLDS))
        self.rule.reset()
        self.assertIsNotNone(self.rule(None, self._exposure(20), None, THRESHOLDS))


class EngineTests(unittest.TestCase):
    def setUp(self):
        self.settings = Settings(
            {"thresholds": THRESHOLDS, "mqtt": {"topics": {"ambient": "fatiga/ambient"}}}
        )

    def test_alerts_reach_ui_and_storage_with_valid_payload(self):
        """SCRUM-33: UI y storage reciben la alerta una vez, respetando el cooldown."""
        bus = EventBus()
        ui_received = []
        bus.subscribe("decision.recommendation", ui_received.append)
        with tempfile.TemporaryDirectory() as temp_dir:
            repository = Repository(path=Path(temp_dir) / "alerts.db")
            try:
                bus.subscribe("decision.recommendation", repository.record_recommendation)
                engine = DecisionEngine(self.settings, bus, cooldown_seconds=300)
                start = datetime(2026, 11, 27, 8, 0, 0)
                for seconds in (0, 60):
                    engine.evaluate(
                        None, exposure(25), ambient(lux=150), now=start + timedelta(seconds=seconds)
                    )
                saved = repository.latest_recommendations()
            finally:
                repository.close()

        self.assertTrue(ui_received)
        ids = [r.id for r in ui_received]
        self.assertEqual(len(ids), len(set(ids)), "el cooldown debe evitar repetidas")
        for recommendation in ui_received:
            self.assertIn(recommendation.severity, ("low", "medium", "high"))
            self.assertTrue(recommendation.message)
            self.assertIsInstance(recommendation.created_at, datetime)
        self.assertEqual({row["id"] for row in saved}, set(ids))

    def test_emits_and_publishes(self):
        bus = EventBus()
        received = []
        bus.subscribe("decision.recommendation", received.append)
        engine = DecisionEngine(self.settings, bus)

        results = engine.evaluate(blink(8), exposure(25), ambient(lux=150))

        self.assertGreaterEqual(len(results), 2)
        self.assertEqual(len(received), len(results))

    def test_cooldown_from_config_prevents_duplicates(self):
        engine = DecisionEngine(Settings({"thresholds": {"cooldown_seconds": 300}}))
        low = blink(8)
        start = datetime(2026, 1, 1, 8, 0, 0)
        first = []
        for seconds in (0, 30, 60):
            first = engine.evaluate(
                low,
                exposure(5),
                ambient(),
                now=start + timedelta(seconds=seconds),
            )
        self.assertEqual(len(first), 1)
        self.assertEqual(first[0].id, "blink-low")
        second = engine.evaluate(
            low, exposure(5), ambient(), now=start + timedelta(seconds=90)
        )
        self.assertEqual(second, [])

    def test_zero_cooldown_from_config_allows_repeat(self):
        engine = DecisionEngine(Settings({"thresholds": {"cooldown_seconds": 0}}))
        low = blink(8)
        start = datetime(2026, 1, 1, 8, 0, 0)
        for seconds in (0, 30, 60):
            engine.evaluate(
                low,
                exposure(5),
                ambient(),
                now=start + timedelta(seconds=seconds),
            )
        second = engine.evaluate(
            low, exposure(5), ambient(), now=start + timedelta(seconds=90)
        )
        self.assertEqual(len(second), 1)
        self.assertEqual(second[0].id, "blink-low")

    def test_20_20_20_is_latched_until_a_valid_break(self):
        settings = Settings(
            {"thresholds": {"cooldown_seconds": 0, "continuous_minutes": 20}}
        )
        engine = DecisionEngine(settings)
        start = datetime(2026, 1, 1, 8, 0, 0)

        def exp(minutes, breaks=0):
            return ExposureMetrics(
                timestamp=start,
                session_seconds=int(minutes * 60),
                continuous_seconds=int(minutes * 60),
                breaks_taken=breaks,
            )

        first = engine.evaluate(None, exp(21), None, now=start)
        self.assertEqual([item.id for item in first], ["break-20"])
        repeated = engine.evaluate(
            None, exp(25), None, now=start + timedelta(seconds=300)
        )
        self.assertEqual(repeated, [])

        engine.evaluate(
            None, exp(0, breaks=1), None, now=start + timedelta(seconds=301)
        )
        again = engine.evaluate(
            None, exp(21, breaks=1), None, now=start + timedelta(seconds=302)
        )
        self.assertEqual([item.id for item in again], ["break-20"])

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
