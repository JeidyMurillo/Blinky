import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "app" / "src"))

import blink_eval  # noqa: E402
from fatiga_visual.core.config import Settings  # noqa: E402


def row(time, ear, closed, calibrated="0.1500", calibrating="0"):
    return {
        "time": f"{time:.3f}",
        "ear": f"{ear:.3f}",
        "closed_real": str(closed),
        "threshold_calibrated": calibrated,
        "calibrating": calibrating,
    }


class BlinkEvalTests(unittest.TestCase):
    def test_usable_rows_skips_calibration_and_empty_ear(self):
        rows = [
            row(0.0, 0.18, 0, calibrating="1"),
            row(0.1, 0.18, 0),
            row(0.2, 0.0, 0),
            row(0.3, 0.18, 0),
        ]
        rows[2]["ear"] = ""
        self.assertEqual(len(blink_eval.usable_rows(rows)), 2)

    def test_calibrated_threshold_comes_from_recording(self):
        rows = [row(0.0, 0.18, 0, calibrated=""), row(0.1, 0.18, 0, calibrated="")]
        self.assertIsNone(blink_eval.calibrated_threshold_from(rows))
        self.assertEqual(blink_eval.calibrated_threshold_from(rows, 0.17), 0.17)
        rows[1]["threshold_calibrated"] = "0.1937"
        self.assertEqual(blink_eval.calibrated_threshold_from(rows), 0.1937)

    def test_frame_metrics_show_the_improvement(self):
        rows = [row(i * 0.04, 0.18, 0) for i in range(10)]
        rows += [row(i * 0.04, 0.10, 1) for i in range(10, 15)]
        rows += [row(i * 0.04, 0.18, 0) for i in range(15, 25)]
        fixed = blink_eval.frame_metrics(rows, 0.21)
        calibrated = blink_eval.frame_metrics(rows, 0.15)
        self.assertLess(fixed["accuracy"], calibrated["accuracy"])
        self.assertEqual(calibrated["accuracy"], 1.0)

    def test_detected_blink_times_use_closure_event(self):
        settings = Settings({})
        rows = [row(i * 0.04, 0.30, 0) for i in range(6)]
        rows += [row(i * 0.04, 0.22, 1) for i in range(6, 11)]
        rows += [row(i * 0.04, 0.30, 0) for i in range(11, 17)]
        # Con 0.21 el EAR de 0.22 nunca baja del umbral: no detecta el cierre.
        self.assertEqual(blink_eval.detected_blink_times(rows, 0.21, settings), [])
        # Con 0.23 sí detecta exactamente un cierre.
        self.assertEqual(len(blink_eval.detected_blink_times(rows, 0.23, settings)), 1)

    def test_event_metrics_match_real_blinks_by_time(self):
        real = [0.2, 1.2]
        detected = [0.25, 3.0]
        metrics = blink_eval.event_metrics(real, detected, tolerance=0.6)
        self.assertEqual(metrics["tp"], 1)
        self.assertEqual(metrics["fp"], 1)
        self.assertEqual(metrics["fn"], 1)


if __name__ == "__main__":
    unittest.main()
