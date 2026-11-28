import sys
import tempfile
import threading
import time
import unittest
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fatiga_visual.core.models import (
    AmbientReading,
    BlinkMetrics,
    ExposureMetrics,
    Recommendation,
)
from fatiga_visual.core.config import Settings
from fatiga_visual.core.events import EventBus
from fatiga_visual.decision.engine import DecisionEngine
from fatiga_visual.main import _start_storage
from fatiga_visual.storage.database import Database
from fatiga_visual.storage.repository import Repository


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.path = Path(self.temp_dir.name) / "test.db"
        self.db = Database(self.path)
        self.repo = Repository(self.db)
        self.session_id = self.repo.start_session("test")
        self.now = datetime.now()

    def tearDown(self):
        self.repo.close()
        self.temp_dir.cleanup()

    def test_schema_creates_two_views(self):
        views = {
            row["name"]
            for row in self.db.query("SELECT name FROM sqlite_master WHERE type = 'view'")
        }
        self.assertIn("v_daily_blinks", views)
        self.assertIn("v_daily_ambient", views)

    def test_records_and_queries_series(self):
        self.repo.record_blink(
            BlinkMetrics(timestamp=self.now, blinks=10, blink_rate=12.0, ear=0.25),
            self.session_id,
        )
        self.repo.record_blink(
            BlinkMetrics(
                timestamp=self.now,
                blinks=11,
                blink_rate=13.0,
                ear=0.26,
                mean_blink_duration_ms=175.0,
                inter_blink_seconds=4.2,
                perclos=0.08,
                long_closures=1,
                confidence=0.9,
                source="mediapipe",
            ),
            self.session_id,
        )
        self.repo.record_ambient(
            AmbientReading(
                timestamp=self.now,
                lux=420.0,
                temperature_c=23.4,
                humidity=48.0,
            ),
            self.session_id,
        )
        self.repo.record_exposure(
            ExposureMetrics(
                timestamp=self.now,
                session_seconds=60,
                continuous_seconds=30,
                breaks_taken=1,
            ),
            self.session_id,
        )
        self.repo.record_recommendation(
            Recommendation(
                id="blink-low",
                title="Pausa",
                message="Descansa",
                severity="high",
                created_at=self.now,
            ),
            self.session_id,
        )

        blinks = self.repo.blink_series(self.session_id)
        self.assertEqual(len(blinks), 2)
        self.assertEqual(blinks[-1]["blinks"], 11)
        self.assertEqual(blinks[-1]["mean_blink_duration_ms"], 175.0)
        self.assertEqual(blinks[-1]["long_closures"], 1)
        self.assertEqual(blinks[-1]["source"], "mediapipe")

        ambient = self.repo.ambient_series(self.session_id)
        self.assertEqual(ambient[0]["lux"], 420.0)

        exposure = self.repo.exposure_series(self.session_id)
        self.assertEqual(exposure[0]["breaks_taken"], 1)

        recommendations = self.repo.latest_recommendations()
        self.assertEqual(recommendations[0]["id"], "blink-low")

    def test_daily_views_aggregate(self):
        self.repo.record_blink(
            BlinkMetrics(timestamp=self.now, blinks=10, blink_rate=12.0),
            self.session_id,
        )
        self.repo.record_blink(
            BlinkMetrics(timestamp=self.now, blinks=11, blink_rate=16.0),
            self.session_id,
        )
        self.repo.record_ambient(
            AmbientReading(
                timestamp=self.now,
                lux=400.0,
                temperature_c=23.0,
                humidity=50.0,
            ),
            self.session_id,
        )

        daily_blinks = self.repo.daily_blinks()
        self.assertEqual(len(daily_blinks), 1)
        self.assertEqual(daily_blinks[0]["samples"], 2)
        self.assertAlmostEqual(daily_blinks[0]["avg_blink_rate"], 14.0)
        self.assertIn("avg_perclos", daily_blinks[0])
        self.assertIn("avg_blink_duration_ms", daily_blinks[0])

        daily_ambient = self.repo.daily_ambient()
        self.assertEqual(len(daily_ambient), 1)
        self.assertAlmostEqual(daily_ambient[0]["avg_lux"], 400.0)

    def test_migrates_old_blink_samples_table(self):
        import sqlite3

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "old.db"
            connection = sqlite3.connect(path)
            connection.execute(
                """
                CREATE TABLE blink_samples (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER,
                    ts TEXT NOT NULL,
                    blinks INTEGER NOT NULL,
                    blink_rate REAL NOT NULL,
                    eyes_closed INTEGER NOT NULL DEFAULT 0,
                    ear REAL NOT NULL DEFAULT 0
                )
                """
            )
            connection.commit()
            connection.close()

            db = Database(path)
            try:
                columns = {
                    row["name"] for row in db.query("PRAGMA table_info(blink_samples)")
                }
                self.assertIn("perclos", columns)
                self.assertIn("long_closures", columns)
                self.assertIn("source", columns)
            finally:
                db.close()

    def test_session_summary_and_end(self):
        self.repo.record_blink(
            BlinkMetrics(timestamp=self.now, blinks=42, blink_rate=12.0),
            self.session_id,
        )
        summary = self.repo.session_summary(self.session_id)
        self.assertEqual(summary["source"], "test")
        self.assertEqual(summary["blinks"], 42)

        self.repo.end_session(self.session_id)
        summary = self.repo.session_summary(self.session_id)
        self.assertIsNotNone(summary["ended_at"])

    def test_series_filter_by_time_range(self):
        base = datetime(2026, 11, 27, 8, 0, 0)
        for minute in (0, 10, 20, 30):
            self.repo.record_blink(
                BlinkMetrics(
                    timestamp=base + timedelta(minutes=minute), blinks=minute, blink_rate=12.0
                ),
                self.session_id,
            )
        rows = self.repo.blink_series(
            since=base + timedelta(minutes=10), until=base + timedelta(minutes=20)
        )
        self.assertEqual([row["blinks"] for row in rows], [10, 20])
        self.assertEqual(len(self.repo.blink_series(since=base + timedelta(minutes=25))), 1)
        self.assertEqual(len(self.repo.blink_series()), 4)


class StorageWiringTests(unittest.TestCase):
    """Motor -> bus -> hilo escritor -> SQLite, sin bloquear a quien publica."""

    def test_recommendations_reach_storage_without_blocking(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "wiring.db"
            settings = Settings({"storage": {"path": str(path)}, "runtime": {"source": "simulated"}})
            bus = EventBus()
            repository, _ = _start_storage(settings, bus)

            gate = threading.Event()
            original = repository.record_recommendation
            repository.record_recommendation = lambda *a: (gate.wait(5), original(*a))

            engine = DecisionEngine(settings, bus)
            long_session = ExposureMetrics(
                timestamp=datetime.now(),
                session_seconds=25 * 60,
                continuous_seconds=25 * 60,
                breaks_taken=0,
            )
            started = time.perf_counter()
            results = engine.evaluate(exposure=long_session)
            self.assertLess(time.perf_counter() - started, 0.5)
            self.assertTrue(results)

            gate.set()
            repository.stop()
            stored = Repository(path=path)
            try:
                saved = stored.latest_recommendations()
            finally:
                stored.close()
            self.assertEqual({row["id"] for row in saved}, {r.id for r in results})
            self.assertTrue(all(row["severity"] and row["message"] for row in saved))


if __name__ == "__main__":
    unittest.main()
