import sys
import time
import unittest
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fatiga_visual.core.config import Settings
from fatiga_visual.core.models import AmbientReading, BlinkMetrics, ExposureMetrics
from fatiga_visual.decision.engine import DecisionEngine


class AlertLatencyTests(unittest.TestCase):
    def test_evaluation_is_under_50ms(self):
        settings = Settings(
            {"thresholds": {"blink_rate_low": 15, "continuous_minutes": 20, "lux_min": 300}}
        )
        engine = DecisionEngine(settings, cooldown_seconds=0)
        now = datetime.now()
        blink = BlinkMetrics(timestamp=now, blinks=10, blink_rate=6)
        exposure = ExposureMetrics(
            timestamp=now, session_seconds=1800, continuous_seconds=1800, breaks_taken=0
        )
        ambient = AmbientReading(timestamp=now, lux=100, temperature_c=23.0, humidity=50.0)

        start = time.perf_counter()
        results = engine.evaluate(blink, exposure, ambient)
        elapsed = time.perf_counter() - start

        self.assertTrue(results)
        self.assertLess(elapsed, 0.05)


if __name__ == "__main__":
    unittest.main()
