import sys
import types
import unittest
from datetime import datetime
from pathlib import Path
from unittest import mock

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fatiga_visual.core.config import Settings
from fatiga_visual.core.events import EventBus
from fatiga_visual.core.models import FaceOverlay, VisionFrame
from fatiga_visual.runtime import pipeline as pipeline_module
from fatiga_visual.runtime.pipeline import RuntimePipeline
from fatiga_visual.ui.state import AppState
from fatiga_visual.vision.face_landmarks import (
    IRIS_CENTER_INDICES,
    overlay_from_landmarks,
)
from fatiga_visual.vision.overlay import cover_crop, project_overlay


def make_landmarks(count=478):
    return [
        types.SimpleNamespace(x=(index % 100) / 100.0, y=(index // 100) / 5.0)
        for index in range(count)
    ]


class OverlayGeometryTests(unittest.TestCase):
    def test_extracts_normalized_points(self):
        landmarks = make_landmarks()
        overlay = overlay_from_landmarks(landmarks)
        self.assertIsNotNone(overlay)
        self.assertEqual(len(overlay.oval), 36)
        self.assertEqual(len(overlay.left_eye), 16)
        self.assertEqual(len(overlay.right_eye), 16)
        self.assertEqual(len(overlay.irises), 2)
        left_iris = landmarks[IRIS_CENTER_INDICES[0]]
        self.assertEqual(overlay.irises[0], (left_iris.x, left_iris.y))

    def test_model_without_iris_still_draws_face_and_eyes(self):
        overlay = overlay_from_landmarks(make_landmarks(count=468))
        self.assertTrue(overlay.visible)
        self.assertEqual(overlay.irises, ())

    def test_no_landmarks_returns_none(self):
        self.assertIsNone(overlay_from_landmarks(None))
        self.assertFalse(FaceOverlay.empty().visible)

    def test_cover_crop_and_projection(self):
        self.assertEqual(cover_crop(1280, 720, 880, 480), (880, 495, 0, 7))
        overlay = FaceOverlay(
            timestamp=datetime.now(),
            oval=((0.5, 0.5),),
            left_eye=((0.25, 0.25),),
        )
        points = project_overlay(overlay, 1280, 720, 880, 480)
        self.assertEqual(points["oval"], ((440, 240),))
        self.assertEqual(points["left_eye"], ((220, 117),))
        self.assertEqual(points["right_eye"], ())
        self.assertEqual(points["irises"], ())


class FakeDetector:
    backend = "fake"
    available = True
    error = ""

    def __init__(self, landmarks):
        self.landmarks = landmarks

    def process(self, frame, timestamp=None):
        return VisionFrame(
            timestamp=datetime.now(),
            image=frame,
            landmarks=self.landmarks,
            confidence=1.0,
        )

    def close(self):
        pass


class FakeCamera:
    def state(self):
        return "running"


class PipelineOverlayTests(unittest.TestCase):
    def _pipeline(self, landmarks, bus):
        settings = Settings(
            {
                "vision": {
                    "auto_calibrate": False,
                    "use_blendshapes": False,
                    "overlay_publish_seconds": 0.0,
                    "face_grace_seconds": 0.0,
                    "calibration_path": "",
                }
            }
        )
        fake = FakeDetector(landmarks)
        with mock.patch.object(
            pipeline_module, "FaceLandmarkDetector", return_value=fake
        ):
            pipeline = RuntimePipeline(settings, bus, camera=FakeCamera())
        return pipeline, fake

    def test_publishes_overlay_and_clears_it_when_face_is_lost(self):
        bus = EventBus()
        overlays = []
        bus.subscribe("vision.landmarks", overlays.append)
        pipeline, fake = self._pipeline(make_landmarks(), bus)
        frame = np.zeros((100, 100, 3), dtype=np.uint8)

        pipeline._process_frame(frame, 1.0)
        self.assertTrue(overlays)
        self.assertTrue(overlays[-1].visible)
        self.assertEqual(len(overlays[-1].oval), 36)

        fake.landmarks = None
        pipeline._process_frame(frame, 1.1)
        self.assertFalse(overlays[-1].visible)

        fake.landmarks = make_landmarks()
        pipeline._process_frame(frame, 1.2)
        self.assertTrue(overlays[-1].visible)
        pipeline._reset_vision_state()
        self.assertFalse(overlays[-1].visible)

    def test_no_bus_does_not_break_frame_processing(self):
        pipeline, _fake = self._pipeline(make_landmarks(), None)
        pipeline._process_frame(np.zeros((100, 100, 3), dtype=np.uint8), 2.0)


class AppStateOverlayTests(unittest.TestCase):
    def test_overlay_event_updates_state_and_camera_off_clears_it(self):
        bus = EventBus()
        state = AppState(Settings({}), bus, simulate=False, seed_demo=False)
        overlay = FaceOverlay(timestamp=datetime.now(), oval=((0.5, 0.5),))

        bus.publish("vision.landmarks", overlay)
        self.assertIs(state.face_overlay, overlay)

        state.set_camera(False)
        self.assertFalse(state.face_overlay.visible)


if __name__ == "__main__":
    unittest.main()
