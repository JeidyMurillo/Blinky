import sys
import types
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fatiga_visual.vision.face_landmarks import (
    FaceLandmarkDetector,
    default_model_path,
)

try:
    import mediapipe  # noqa: F401

    MEDIAPIPE_AVAILABLE = True
except Exception:
    MEDIAPIPE_AVAILABLE = False

MODEL_AVAILABLE = default_model_path().exists()


class HelperTests(unittest.TestCase):
    def test_prepare_image_accepts_grayscale_and_rgba(self):
        detector = FaceLandmarkDetector.__new__(FaceLandmarkDetector)
        gray = np.zeros((20, 30), dtype=np.uint8)
        prepared = detector._prepare_image(gray)
        self.assertEqual(prepared.shape, (20, 30, 3))

        rgba = np.zeros((20, 30, 4), dtype=np.uint8)
        prepared = detector._prepare_image(rgba)
        self.assertEqual(prepared.shape, (20, 30, 3))

    def test_blink_score_averages_both_eyes(self):
        categories = [
            types.SimpleNamespace(category_name="eyeBlinkLeft", score=0.8),
            types.SimpleNamespace(category_name="eyeBlinkRight", score=0.4),
            types.SimpleNamespace(category_name="jawOpen", score=0.9),
        ]
        self.assertAlmostEqual(FaceLandmarkDetector._blink_score(categories), 0.6)

    def test_blink_score_requires_both_eyes(self):
        categories = [
            types.SimpleNamespace(category_name="eyeBlinkLeft", score=0.8),
        ]
        self.assertIsNone(FaceLandmarkDetector._blink_score(categories))


@unittest.skipUnless(
    MEDIAPIPE_AVAILABLE and MODEL_AVAILABLE,
    "MediaPipe o el modelo face_landmarker.task no están disponibles",
)
class MediaPipeBackendTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.detector = FaceLandmarkDetector(allow_download=False)

    @classmethod
    def tearDownClass(cls):
        cls.detector.close()

    def test_detector_is_available(self):
        self.assertTrue(self.detector.available, self.detector.error)

    def test_blank_image_has_no_face(self):
        frame = np.zeros((64, 64, 3), dtype=np.uint8)
        result = self.detector.process(frame, timestamp=1.0)
        self.assertIsNone(result.landmarks)
        self.assertEqual(result.confidence, 0.0)


if __name__ == "__main__":
    unittest.main()
