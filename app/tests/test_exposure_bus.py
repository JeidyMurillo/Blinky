import sys
import unittest
from dataclasses import replace
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fatiga_visual.core.config import Settings
from fatiga_visual.core.events import EventBus
from fatiga_visual.core.models import BreakEvent, ExposureMetrics
from fatiga_visual.exposure.bus import (
    BREAK_TOPIC,
    METRICS_TOPIC,
    ExposureBusPublisher,
    break_payload,
    is_valid,
    metrics_payload,
)
from fatiga_visual.exposure.exposure_timer import ExposureTimer
from fatiga_visual.runtime.simulated import SimulatedPipeline


class ExposurePayloadTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 1, 1, 12, 0, 0)
        self.metrics = ExposureMetrics(
            timestamp=self.now,
            session_seconds=600,
            continuous_seconds=300,
            breaks_taken=1,
            break_due=False,
            user_present=True,
        )

    def test_metrics_payload_matches_schema(self):
        payload = metrics_payload(self.metrics)
        self.assertEqual(payload["event"], METRICS_TOPIC)
        self.assertTrue(payload["user_present"])
        self.assertTrue(is_valid(payload))

    def test_break_payload_matches_schema(self):
        event = BreakEvent(
            timestamp=self.now,
            started_at=self.now - timedelta(seconds=25),
            kind="finished",
            duration_seconds=25.0,
            continuous_before_seconds=600.0,
        )
        payload = break_payload(event)
        self.assertEqual(payload["event"], BREAK_TOPIC)
        self.assertTrue(is_valid(payload))

    def test_edge_cases_are_rejected(self):
        self.assertFalse(is_valid(metrics_payload(replace(self.metrics, session_seconds=-1))))
        self.assertFalse(is_valid(metrics_payload(replace(self.metrics, user_present=None))))
        invalid_break = break_payload(
            BreakEvent(
                timestamp=self.now,
                started_at=self.now,
                kind="paused",
                duration_seconds=1.0,
            )
        )
        self.assertFalse(is_valid(invalid_break))
        self.assertFalse(is_valid({"event": METRICS_TOPIC}))


class ExposureBusPublisherTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 1, 1, 12, 0, 0)
        self.metrics = ExposureMetrics(
            timestamp=self.now,
            session_seconds=60,
            continuous_seconds=60,
            breaks_taken=0,
        )
        self.bus = EventBus()
        self.received = []
        self.bus.subscribe(METRICS_TOPIC, self.received.append)

    def test_publishes_valid_metrics(self):
        publisher = ExposureBusPublisher(self.bus)
        self.assertTrue(publisher.publish_metrics(self.metrics))
        self.assertEqual(self.received, [self.metrics])

    def test_invalid_payload_is_not_published(self):
        publisher = ExposureBusPublisher(self.bus)
        invalid = replace(self.metrics, continuous_seconds=-1)
        self.assertFalse(publisher.publish_metrics(invalid))
        self.assertEqual(self.received, [])

    def test_topics_come_from_settings(self):
        settings = Settings({"bus": {"topics": {"exposure_metrics": "custom.metrics"}}})
        custom = []
        self.bus.subscribe("custom.metrics", custom.append)
        publisher = ExposureBusPublisher(self.bus, settings)
        self.assertTrue(publisher.publish_metrics(self.metrics))
        self.assertEqual(custom, [self.metrics])
        self.assertEqual(self.received, [])


class ExposurePipelineTests(unittest.TestCase):
    def test_timer_reports_presence(self):
        timer = ExposureTimer()
        timer.tick(5, present=True)
        self.assertTrue(timer.snapshot().user_present)
        timer.tick(3, present=False)
        self.assertFalse(timer.snapshot().user_present)

    def test_simulated_pipeline_publishes_valid_metrics(self):
        bus = EventBus()
        received = []
        bus.subscribe(METRICS_TOPIC, received.append)
        settings = Settings({"runtime": {"publish_seconds": 0.05}})
        pipeline = SimulatedPipeline(settings, bus, simulate_ambient=False)
        pipeline._tick(1.0)
        self.assertTrue(received)
        self.assertTrue(is_valid(metrics_payload(received[-1])))
        self.assertTrue(received[-1].user_present)


if __name__ == "__main__":
    unittest.main()
