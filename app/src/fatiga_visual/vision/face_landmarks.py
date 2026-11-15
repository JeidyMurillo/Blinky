"""Detección de landmarks faciales con MediaPipe Face Landmarker.

MediaPipe 1.x ya no incluye `mp.solutions.face_mesh`; ahora usa la API de
*tasks* y un modelo `.task`. Este módulo:

- Busca el modelo en `vision.model_path`, en la variable de entorno
  `BLINKY_FACE_MODEL` o en la caché del usuario.
- Lo descarga la primera vez si falta.
- Devuelve 478 landmarks (los mismos índices de ojo que FaceMesh) y, cuando
  está disponible, la blendshape `eyeBlink` como señal auxiliar.
"""

import os
import shutil
import time
import urllib.request
from datetime import datetime
from pathlib import Path

import numpy as np

from fatiga_visual.core.models import VisionFrame

try:
    import mediapipe as mp
except Exception:
    mp = None

MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/face_landmarker/"
    "face_landmarker/float16/1/face_landmarker.task"
)
MODEL_FILENAME = "face_landmarker.task"


def default_model_path():
    override = os.environ.get("BLINKY_FACE_MODEL")
    if override:
        return Path(override).expanduser()
    base = os.environ.get("LOCALAPPDATA")
    if base:
        cache = Path(base)
    else:
        cache = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
    return cache / "Blinky" / "models" / MODEL_FILENAME


def download_model(destination, timeout=60):
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    with urllib.request.urlopen(MODEL_URL, timeout=timeout) as response:
        with temporary.open("wb") as target:
            shutil.copyfileobj(response, target)
    temporary.replace(destination)
    return destination


class FaceLandmarkDetector:
    def __init__(
        self,
        max_faces=1,
        refine_landmarks=True,
        model_path=None,
        running_mode="video",
        use_blendshapes=True,
        allow_download=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    ):
        self.max_faces = int(max_faces)
        self.refine_landmarks = bool(refine_landmarks)
        self.running_mode = "video" if running_mode == "video" else "image"
        self.use_blendshapes = bool(use_blendshapes)
        self.model_path = Path(model_path).expanduser() if model_path else default_model_path()
        self._error = ""
        self._landmarker = None
        self._vision = None
        self._last_timestamp_ms = 0

        if mp is None:
            self._error = (
                "MediaPipe no está instalado. Instala mediapipe>=1.2 para usar "
                "la detección real."
            )
            return

        try:
            from mediapipe.tasks.python import vision
            from mediapipe.tasks.python.core.base_options import BaseOptions
        except Exception as exc:
            self._error = f"No se pudo cargar la API de MediaPipe: {exc}"
            return

        try:
            if not self.model_path.exists():
                if not allow_download:
                    raise FileNotFoundError(
                        f"Falta el modelo {self.model_path} y la descarga está desactivada."
                    )
                download_model(self.model_path)
            mode = (
                vision.RunningMode.VIDEO
                if self.running_mode == "video"
                else vision.RunningMode.IMAGE
            )
            options = vision.FaceLandmarkerOptions(
                base_options=BaseOptions(model_asset_path=str(self.model_path)),
                running_mode=mode,
                num_faces=self.max_faces,
                min_face_detection_confidence=min_detection_confidence,
                min_face_presence_confidence=min_detection_confidence,
                min_tracking_confidence=min_tracking_confidence,
                output_face_blendshapes=self.use_blendshapes,
                output_facial_transformation_matrixes=False,
            )
            self._landmarker = vision.FaceLandmarker.create_from_options(options)
            self._vision = vision
        except Exception as exc:
            self._landmarker = None
            self._error = f"No se pudo iniciar Face Landmarker: {exc}"

    @property
    def available(self):
        return self._landmarker is not None

    @property
    def error(self):
        return self._error

    @property
    def backend(self):
        return "mediapipe-face-landmarker"

    def process(self, frame_rgb, timestamp=None):
        """Devuelve VisionFrame con landmarks o None si no hay rostro."""
        if self._landmarker is None:
            return VisionFrame(
                timestamp=datetime.now(),
                image=frame_rgb,
                landmarks=None,
                confidence=0.0,
            )

        frame = self._prepare_image(frame_rgb)
        if frame is None:
            return VisionFrame(
                timestamp=datetime.now(),
                image=frame_rgb,
                landmarks=None,
                confidence=0.0,
            )

        image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
        if self.running_mode == "video" and hasattr(self._landmarker, "detect_for_video"):
            stamp = int((timestamp if timestamp is not None else time.monotonic()) * 1000)
            if stamp <= self._last_timestamp_ms:
                stamp = self._last_timestamp_ms + 1
            self._last_timestamp_ms = stamp
            result = self._landmarker.detect_for_video(image, stamp)
        else:
            result = self._landmarker.detect(image)

        landmarks = None
        if result.face_landmarks:
            landmarks = result.face_landmarks[0]

        blink_score = None
        if landmarks is not None and getattr(result, "face_blendshapes", None):
            blink_score = self._blink_score(result.face_blendshapes[0])

        return VisionFrame(
            timestamp=datetime.now(),
            image=frame_rgb,
            landmarks=landmarks,
            blink_score=blink_score,
            confidence=self._confidence(landmarks),
        )

    def _prepare_image(self, frame_rgb):
        if frame_rgb is None:
            return None
        frame = np.asarray(frame_rgb)
        if frame.ndim == 2:
            frame = np.stack((frame,) * 3, axis=-1)
        elif frame.ndim == 3 and frame.shape[2] == 4:
            frame = frame[:, :, :3]
        if frame.ndim != 3 or frame.shape[2] != 3:
            return None
        if frame.dtype != np.uint8:
            frame = np.clip(frame, 0, 255).astype(np.uint8)
        return np.ascontiguousarray(frame)

    @staticmethod
    def _blink_score(blendshapes):
        scores = {}
        for category in blendshapes or []:
            name = getattr(category, "category_name", None)
            if name:
                scores[name] = float(getattr(category, "score", 0.0))
        left = scores.get("eyeBlinkLeft")
        right = scores.get("eyeBlinkRight")
        if left is None or right is None:
            return None
        return max(0.0, min(1.0, (left + right) / 2.0))

    @staticmethod
    def _confidence(landmarks):
        if not landmarks:
            return 0.0
        values = []
        for landmark in landmarks:
            visibility = float(getattr(landmark, "visibility", 0.0) or 0.0)
            if visibility > 0.0:
                values.append(visibility)
        if not values:
            return 1.0
        return max(0.0, min(1.0, sum(values) / len(values)))

    def close(self):
        if self._landmarker is not None:
            try:
                self._landmarker.close()
            except Exception:
                pass
            self._landmarker = None
