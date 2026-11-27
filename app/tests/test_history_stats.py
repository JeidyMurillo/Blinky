import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fatiga_visual.core.models import BlinkMetrics, ExposureMetrics, Recommendation
from fatiga_visual.storage.database import Database
from fatiga_visual.storage.repository import Repository
from fatiga_visual.ui.views.stats_view import (
    StatsView,
    _format_duration,
    _format_session_day,
    _value,
)


class HistoryRepositoryTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.temp_dir.name) / "history.db")
        self.repo = Repository(self.db)
        self.now = datetime.now()
        self.current_id = self.repo.start_session("test")
        self.old_id = self.db.execute(
            "INSERT INTO sessions (started_at, ended_at, source) VALUES (?, ?, ?)",
            (
                (self.now - timedelta(days=2)).isoformat(timespec="seconds"),
                (self.now - timedelta(days=2, hours=-1)).isoformat(timespec="seconds"),
                "test",
            ),
        )

        self.repo.record_blink(
            BlinkMetrics(timestamp=self.now, blinks=42, blink_rate=12.0, ear=0.24),
            self.current_id,
        )
        self.repo.record_exposure(
            ExposureMetrics(
                timestamp=self.now,
                session_seconds=600,
                continuous_seconds=300,
                breaks_taken=2,
            ),
            self.current_id,
        )
        self.repo.record_recommendation(
            Recommendation(
                id="history-low-blink",
                title="Pausa",
                message="Descansa",
                severity="high",
                created_at=self.now,
            ),
            self.current_id,
        )
        self.repo.record_blink(
            BlinkMetrics(timestamp=self.now - timedelta(days=2), blinks=18, blink_rate=9.0),
            self.old_id,
        )

    def tearDown(self):
        self.repo.close()
        self.temp_dir.cleanup()

    def test_history_lists_current_and_previous_sessions(self):
        sessions = self.repo.session_history(limit=10)

        self.assertEqual(len(sessions), 2)
        self.assertEqual(sessions[0]["id"], self.current_id)
        self.assertTrue(sessions[0]["current"])
        self.assertFalse(sessions[1]["current"])
        self.assertEqual(sessions[1]["id"], self.old_id)
        self.assertIsNotNone(sessions[1]["ended_at"])

    def test_history_aggregates_blinks_exposure_and_alerts(self):
        current = self.repo.session_history(limit=10)[0]

        self.assertEqual(current["blinks"], 42)
        self.assertEqual(current["avg_blink_rate"], 12.0)
        self.assertEqual(current["breaks_taken"], 2)
        self.assertEqual(current["exposure_seconds"], 600)
        self.assertEqual(current["max_continuous_seconds"], 300)
        self.assertEqual(current["alerts"], 1)

    def test_session_alert_count(self):
        self.assertEqual(self.repo.session_alert_count(self.current_id), 1)
        self.assertEqual(self.repo.session_alert_count(self.old_id), 0)
        self.assertEqual(self.repo.session_alert_count(), 1)

    def test_session_summary_includes_exposure_fields(self):
        summary = self.repo.session_summary(self.current_id)

        self.assertEqual(summary["exposure_seconds"], 600)
        self.assertEqual(summary["max_continuous_seconds"], 300)


class FakeState:
    blink_history = [("Lun", 99)]


class FakeRepository:
    def daily_blinks(self, days=7):
        return [
            {"day": "2026-11-26", "max_blinks": 12},
            {"day": "2026-11-27", "max_blinks": 30},
        ]


class StatsFormatTests(unittest.TestCase):
    def test_daily_chart_uses_repository_instead_of_demo_history(self):
        view = StatsView.__new__(StatsView)
        view.state = FakeState()
        view.repository = FakeRepository()

        self.assertEqual(view._daily_history(), [("11-26", 12), ("11-27", 30)])

    def test_daily_chart_falls_back_without_repository(self):
        view = StatsView.__new__(StatsView)
        view.state = FakeState()
        view.repository = None

        self.assertEqual(view._daily_history(), [("Lun", 99)])

    def test_format_session_day(self):
        self.assertEqual(_format_session_day("2026-11-27T14:05:00"), "27/11 14:05")
        self.assertEqual(_format_session_day(None), "—")

    def test_format_duration(self):
        self.assertEqual(
            _format_duration(
                {
                    "started_at": "2026-11-27T10:00:00",
                    "ended_at": "2026-11-27T11:30:00",
                }
            ),
            "01:30",
        )
        self.assertEqual(
            _format_duration({"started_at": "2026-11-27T10:00:00", "ended_at": None}),
            "En curso",
        )

    def test_value_handles_missing_aggregates(self):
        self.assertEqual(_value(None), "—")
        self.assertEqual(_value(12.34, 1), "12.3")
        self.assertEqual(_value(7), "7")


if __name__ == "__main__":
    unittest.main()
