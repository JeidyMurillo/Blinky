import sys
import unittest
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fatiga_visual.core.config import Settings
from fatiga_visual.core.models import ExposureMetrics, PresenceEvent, VisionStatus
from fatiga_visual.exposure.exposure_timer import ExposureTimer
from fatiga_visual.exposure.presence import PresenceTracker
from fatiga_visual.ui.state import AppState


class ContinuousTimerTests(unittest.TestCase):
    def test_continuous_time_only_advances_when_present(self):
        timer = ExposureTimer(break_after_minutes=20)
        timer.tick(10, present=True)
        timer.tick(5, present=False)
        timer.tick(3, present=True)
        self.assertEqual(timer.session_seconds, 18)
        self.assertEqual(timer.continuous_seconds, 13)
        self.assertFalse(timer.break_due)

    def test_short_absence_keeps_the_chronometer_running(self):
        start = datetime(2026, 1, 1, 12, 0, 0)
        presence = PresenceTracker(absent_after_seconds=20)
        timer = ExposureTimer()

        self.assertTrue(presence.update(True, start).present)
        timer.tick(10, present=presence.present)
        self.assertIsNone(presence.update(False, start + timedelta(seconds=2)))
        timer.tick(2, present=presence.present)
        self.assertIsNone(presence.update(True, start + timedelta(seconds=3)))
        timer.tick(1, present=presence.present)

        self.assertEqual(timer.continuous_seconds, 13)
        self.assertEqual(timer.breaks_taken, 0)

    def test_real_break_resets_the_chronometer(self):
        start = datetime(2026, 1, 1, 12, 0, 0)
        presence = PresenceTracker(absent_after_seconds=20)
        timer = ExposureTimer()

        presence.update(True, start)
        timer.tick(1200, present=True)
        self.assertTrue(timer.break_due)

        event = presence.update(False, start + timedelta(seconds=25))
        self.assertIsNotNone(event)
        self.assertFalse(event.present)
        timer.take_break()
        self.assertEqual(timer.continuous_seconds, 0)
        self.assertEqual(timer.breaks_taken, 1)

        presence.update(True, start + timedelta(seconds=26))
        timer.tick(5, present=presence.present)
        self.assertEqual(timer.continuous_seconds, 5)

    def test_presence_event_published_on_state_change(self):
        start = datetime(2026, 1, 1, 12, 0, 0)
        presence = PresenceTracker(absent_after_seconds=2)
        self.assertTrue(presence.update(True, start).present)
        self.assertIsNone(presence.update(True, start + timedelta(seconds=1)))
        absent = presence.update(False, start + timedelta(seconds=4))
        self.assertFalse(absent.present)
        self.assertEqual(absent.confidence, 0.0)


class AppStateChronometerTests(unittest.TestCase):
    def test_exposes_continuous_time_break_goal_and_presence(self):
        settings = Settings({"thresholds": {"continuous_minutes": 1}})
        state = AppState(settings, None, simulate=False, seed_demo=False)

        state.update_exposure(
            ExposureMetrics(
                timestamp=datetime.now(),
                session_seconds=300,
                continuous_seconds=30,
                breaks_taken=1,
            )
        )
        self.assertEqual(state.continuous_seconds, 30)
        self.assertEqual(state.break_after_seconds, 60)
        self.assertFalse(state.break_due)
        self.assertTrue(state.user_present)

        state.update_exposure(
            ExposureMetrics(
                timestamp=datetime.now(),
                session_seconds=330,
                continuous_seconds=60,
                breaks_taken=1,
                break_due=True,
            )
        )
        self.assertTrue(state.break_due)

        state.update_presence(PresenceEvent(timestamp=datetime.now(), present=False))
        self.assertFalse(state.user_present)
        state.update_presence(PresenceEvent(timestamp=datetime.now(), present=True))
        self.assertTrue(state.user_present)

        state.presence_state = None
        state.vision_status = VisionStatus(
            timestamp=datetime.now(),
            backend="mediapipe-face-landmarker",
            available=True,
            face_found=False,
        )
        self.assertFalse(state.user_present)


if __name__ == "__main__":
    unittest.main()
