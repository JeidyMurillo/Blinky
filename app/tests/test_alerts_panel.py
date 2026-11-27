import sys
import unittest
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fatiga_visual.core.config import Settings
from fatiga_visual.core.events import EventBus
from fatiga_visual.core.models import (
    AmbientReading,
    ExposureMetrics,
    Recommendation,
    RecommendationResolved,
)
from fatiga_visual.decision.engine import DecisionEngine
from fatiga_visual.ui.panels.alerts_panel import alert_time, priority_text
from fatiga_visual.ui.state import AppState


def exposure(minutes):
    return ExposureMetrics(
        timestamp=datetime.now(),
        session_seconds=minutes * 60,
        continuous_seconds=minutes * 60,
        breaks_taken=0,
    )


def ambient(lux):
    return AmbientReading(
        timestamp=datetime.now(),
        lux=lux,
        temperature_c=23.4,
        humidity=48,
    )


def recommendation(recommendation_id, severity, created_at):
    return Recommendation(
        id=recommendation_id,
        title=recommendation_id,
        message=recommendation_id,
        severity=severity,
        created_at=created_at,
    )


class EngineResolutionTests(unittest.TestCase):
    def _engine(self, cooldown):
        bus = EventBus()
        resolved = []
        bus.subscribe("decision.recommendation.resolved", resolved.append)
        engine = DecisionEngine(
            Settings({"thresholds": {"cooldown_seconds": cooldown}}), bus
        )
        return engine, resolved

    def test_resolves_after_two_evaluations_without_the_condition(self):
        engine, resolved = self._engine(0)
        start = datetime(2026, 1, 1, 8, 0, 0)

        first = engine.evaluate(None, exposure(5), ambient(100), now=start)
        self.assertEqual([item.id for item in first], ["light-low"])
        engine.evaluate(None, exposure(5), ambient(420), now=start + timedelta(seconds=1))
        self.assertEqual(resolved, [])

        engine.evaluate(None, exposure(5), ambient(420), now=start + timedelta(seconds=2))
        self.assertEqual([item.id for item in resolved], ["light-low"])
        self.assertEqual(resolved[0].resolved_at, start + timedelta(seconds=2))

    def test_cooldown_keeps_the_alert_active_until_resolved(self):
        engine, resolved = self._engine(300)
        start = datetime(2026, 1, 1, 8, 0, 0)
        low_light = ambient(100)

        engine.evaluate(None, exposure(5), low_light, now=start)
        engine.evaluate(None, exposure(5), low_light, now=start + timedelta(seconds=30))
        self.assertEqual(resolved, [])

        engine.evaluate(None, exposure(5), ambient(420), now=start + timedelta(seconds=60))
        self.assertEqual(resolved, [])
        engine.evaluate(None, exposure(5), ambient(420), now=start + timedelta(seconds=90))
        self.assertEqual([item.id for item in resolved], ["light-low"])

    def test_resolved_rule_can_emit_again(self):
        engine, resolved = self._engine(300)
        start = datetime(2026, 1, 1, 8, 0, 0)

        engine.evaluate(None, exposure(5), ambient(100), now=start)
        engine.evaluate(None, exposure(5), ambient(420), now=start + timedelta(seconds=1))
        engine.evaluate(None, exposure(5), ambient(420), now=start + timedelta(seconds=2))
        again = engine.evaluate(
            None, exposure(5), ambient(100), now=start + timedelta(seconds=3)
        )
        self.assertEqual([item.id for item in again], ["light-low"])
        self.assertEqual(len(resolved), 1)


class AppStateAlertPanelTests(unittest.TestCase):
    def setUp(self):
        self.bus = EventBus()
        self.state = AppState(Settings({}), self.bus, seed_demo=False)
        self.start = datetime(2026, 1, 1, 8, 0, 0)

    def test_orders_by_priority_then_time(self):
        for item in (
            recommendation("low", "low", self.start),
            recommendation("medium", "medium", self.start + timedelta(seconds=1)),
            recommendation("high", "high", self.start - timedelta(seconds=1)),
        ):
            self.state.add_recommendation(item)
        self.assertEqual(
            [item.id for item in self.state.visible_recommendations()],
            ["high", "medium", "low"],
        )

    def test_dismiss_hides_until_the_engine_emits_again(self):
        first = recommendation("break-20", "medium", self.start)
        self.bus.publish("decision.recommendation", first)
        self.state.dismiss_recommendation("break-20")
        self.assertEqual(self.state.visible_recommendations(), [])

        again = recommendation("break-20", "medium", self.start + timedelta(minutes=5))
        self.bus.publish("decision.recommendation", again)
        self.assertEqual(
            [item.id for item in self.state.visible_recommendations()], ["break-20"]
        )
        self.assertEqual(self.state.recommendations[0].created_at, again.created_at)

    def test_resolution_event_removes_the_alert(self):
        item = recommendation("light-low", "medium", self.start)
        self.bus.publish("decision.recommendation", item)
        self.state.dismiss_recommendation("light-low")

        self.bus.publish(
            "decision.recommendation.resolved",
            RecommendationResolved(id="light-low", resolved_at=self.start),
        )
        self.assertEqual(self.state.recommendations, [])
        self.assertNotIn("light-low", self.state.dismissed_ids)
        self.assertIsNone(self.state.primary_recommendation())


class AlertsPanelHelpersTests(unittest.TestCase):
    def test_priority_labels(self):
        self.assertEqual(priority_text("high"), "Prioridad alta")
        self.assertEqual(priority_text("medium"), "Prioridad media")
        self.assertEqual(priority_text("low"), "Sugerencia")

    def test_time_shows_clock_and_age(self):
        created_at = datetime(2026, 1, 1, 8, 0, 0)
        self.assertEqual(
            alert_time(created_at, now=created_at + timedelta(seconds=20)),
            "08:00 - Hace instantes",
        )
        self.assertEqual(
            alert_time(created_at, now=created_at + timedelta(minutes=5)),
            "08:00 - Hace 5 min",
        )
        self.assertEqual(
            alert_time(created_at, now=created_at + timedelta(hours=2)),
            "08:00 - Hace 2 h",
        )


if __name__ == "__main__":
    unittest.main()
