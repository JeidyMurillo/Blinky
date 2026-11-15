import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fatiga_visual.vision.blink_detector import BlinkDetector
from fatiga_visual.vision.ear import eye_aspect_ratio


class EarTests(unittest.TestCase):
    def test_open_eye(self):
        points = [(0, 0), (2.5, 3), (7.5, 3), (10, 0), (7.5, -3), (2.5, -3)]
        self.assertAlmostEqual(eye_aspect_ratio(points), 0.6, places=3)

    def test_closed_eye_lower_than_open(self):
        open_points = [(0, 0), (2.5, 3), (7.5, 3), (10, 0), (7.5, -3), (2.5, -3)]
        closed_points = [(0, 0), (2.5, 0.5), (7.5, 0.5), (10, 0), (7.5, -0.5), (2.5, -0.5)]
        self.assertLess(eye_aspect_ratio(closed_points), eye_aspect_ratio(open_points))

    def test_requires_six_points(self):
        with self.assertRaises(ValueError):
            eye_aspect_ratio([(0, 0), (1, 1)])


class BlinkDetectorTests(unittest.TestCase):
    def test_blink_needs_minimum_closed_frames(self):
        detector = BlinkDetector(threshold=0.21, min_closed_frames=2)
        self.assertIsNone(detector.update(0.3))
        self.assertIsNone(detector.update(0.15))
        self.assertEqual(detector.update(0.15), "closed")
        self.assertEqual(detector.update(0.3), "opened")

    def test_single_closed_frame_is_not_a_blink(self):
        detector = BlinkDetector(threshold=0.21, min_closed_frames=2)
        detector.update(0.3)
        detector.update(0.15)
        self.assertIsNone(detector.update(0.3))


if __name__ == "__main__":
    unittest.main()
