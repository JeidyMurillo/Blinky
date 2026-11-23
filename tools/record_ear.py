r"""Graba EAR de la cámara del PC con etiquetas de verdad de campo (SCRUM-23).

Uso (desde la raíz del repo):
    python tools\record_ear.py --output tools\data\sesion1.csv

No abre ventana de OpenCV (algunas builds no incluyen highgui). El estado se
muestra en la terminal y la tecla se detecta con `msvcrt` en Windows:

  1. Los primeros segundos (4 por defecto) mirar al frente SIN parpadear:
     ahí se calcula el umbral EAR calibrado.
  2. Después, cada vez que cierres los ojos pulsa ESPACIO en ese momento.
     La tecla marca ~0.3 s como "ojos cerrados" (verdad de campo).
  3. ENTER o Q termina antes de tiempo.

Alternativa sin teclado: `--auto-cues` imprime "PARPADEA AHORA" cada 3 s y
etiqueta automáticamente esa ventana. Úsala si la terminal no recibe teclas.

El CSV resultante lo evalúa `tools/blink_eval.py`, que compara el umbral fijo
0.21 contra el aprendido. No necesita ESP32 ni sensores ambientales.
"""

import argparse
import csv
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app" / "src"))

import cv2  # noqa: E402

from fatiga_visual.core.config import DEFAULTS, load_settings  # noqa: E402
from fatiga_visual.vision.blink_detector import BlinkDetector  # noqa: E402
from fatiga_visual.vision.camera import CameraStream  # noqa: E402
from fatiga_visual.vision.calibration import EarCalibration  # noqa: E402
from fatiga_visual.vision.ear import average_eye_aspect_ratio  # noqa: E402
from fatiga_visual.vision.face_landmarks import FaceLandmarkDetector  # noqa: E402
from fatiga_visual.vision.smoothing import ExponentialSmoother  # noqa: E402

try:
    import msvcrt
except ImportError:  # pragma: no cover - Linux/macOS
    msvcrt = None

FIXED_THRESHOLD = 0.21
LABEL_SECONDS = 0.30
FIELDS = (
    "time",
    "ear",
    "confidence",
    "closed_real",
    "closed_pred",
    "threshold",
    "threshold_calibrated",
    "calibrating",
    "blink_score",
)


def _prepare(frame, width):
    if width > 0 and frame.shape[1] > width:
        scale = width / float(frame.shape[1])
        height = max(1, int(frame.shape[0] * scale))
        return cv2.resize(frame, (width, height), interpolation=cv2.INTER_AREA)
    return frame


def _read_key():
    """Devuelve ' ', '\\r', 'q', etc. sin bloquear; None si no hay tecla."""
    if msvcrt is None:
        return None
    try:
        if not msvcrt.kbhit():
            return None
        char = msvcrt.getwch()
        if char in ("\x00", "\xe0"):  # tecla especial: consumir el segundo byte
            msvcrt.getwch()
            return None
        return char.lower()
    except OSError:  # sin consola adjunta: se usa --auto-cues
        return None


def record(args):
    settings = load_settings()
    calibration = EarCalibration(
        seconds=float(settings.get("vision.calibration_seconds", 4.0)),
        min_samples=int(settings.get("vision.calibration_min_samples", 24)),
        fallback=FIXED_THRESHOLD,
        ratio=float(settings.get("vision.calibration_ratio", 0.60)),
        floor=float(settings.get("vision.calibration_floor", 0.06)),
        ceiling=float(settings.get("vision.calibration_ceiling", 0.28)),
    )
    detector = FaceLandmarkDetector(
        model_path=str(settings.get("vision.model_path", "") or "") or None,
        running_mode="video",
        use_blendshapes=bool(settings.get("vision.use_blendshapes", True)),
        allow_download=bool(settings.get("vision.allow_model_download", True)),
    )
    if not detector.available:
        print(f"ERROR: {detector.error}")
        return 1

    camera = CameraStream(
        index=args.camera_index if args.camera_index is not None else int(settings.get("camera.index", 0)),
        width=int(settings.get("camera.width", 1280)),
        height=int(settings.get("camera.height", 720)),
        fps=int(settings.get("camera.fps", 30)),
    )
    camera.start()
    deadline = time.monotonic() + 10.0
    while time.monotonic() < deadline:
        if camera.state() in (CameraStream.RUNNING, CameraStream.ERROR):
            break
        time.sleep(0.05)
    if camera.state() != CameraStream.RUNNING:
        print(f"ERROR: no se pudo abrir la cámara ({camera.message()})")
        camera.stop()
        detector.close()
        return 1

    reopen_margin = float(settings.get("vision.reopen_margin", 0.02))
    detector_blink = BlinkDetector(
        threshold=FIXED_THRESHOLD,
        min_closed_frames=int(settings.get("vision.min_closed_frames", 2)),
        max_closed_frames=int(settings.get("vision.max_closed_frames", 15)),
        reopen_margin=reopen_margin,
        min_blink_duration_ms=float(settings.get("vision.min_blink_duration_ms", 0.0)),
        max_blink_duration_ms=float(settings.get("vision.max_blink_duration_ms", 800.0)),
        long_closure_seconds=float(settings.get("vision.long_closure_seconds", 1.5)),
        blink_score_threshold=(
            float(settings.get("vision.blink_score_threshold", 0.65))
            if settings.get("vision.use_blendshapes", True)
            else None
        ),
        cooldown_seconds=float(settings.get("vision.blink_cooldown_seconds", 0.06)),
    )
    smoother = ExponentialSmoother(float(settings.get("vision.smoothing_alpha", 0.65)))
    min_confidence = settings.get("thresholds.min_confidence")
    if min_confidence is None:  # rama anterior a SCRUM-32
        min_confidence = settings.get(
            "vision.min_confidence", DEFAULTS["vision"]["min_confidence"]
        )
    min_confidence = float(min_confidence)
    processing_width = int(settings.get("vision.processing_width", 640))

    output = Path(args.output).expanduser()
    output.parent.mkdir(parents=True, exist_ok=True)

    started = time.monotonic()
    last_seq = -1
    label_until = 0.0
    presses = 0
    rows = 0
    calibrated = ""
    next_cue = None
    last_status = 0.0

    print("Grabando. Mira al frente sin parpadear durante la calibración.")
    if args.auto_cues:
        print(f"Después: parpadea cada {args.cue_interval:g} s cuando diga PARPADEA AHORA.")
    else:
        print("Después: cierra los ojos y pulsa ESPACIO en el mismo momento.")
    print("ENTER o Q para terminar.\n")

    try:
        with output.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=FIELDS)
            writer.writeheader()
            while time.monotonic() - started < args.seconds:
                now = time.monotonic()
                seq, frame_rgb, _fps = camera.read_frame()
                if frame_rgb is None or seq == last_seq:
                    time.sleep(0.005)
                    continue
                last_seq = seq

                prepared = _prepare(frame_rgb, processing_width)
                vision = detector.process(prepared, now)
                valid = (
                    vision.landmarks is not None
                    and vision.confidence >= min_confidence
                )
                ear = None
                if valid:
                    try:
                        height, width = prepared.shape[:2]
                        ear = average_eye_aspect_ratio(vision.landmarks, width, height)
                    except Exception:
                        ear = None
                if ear is not None and 0.0 < ear <= 0.50:
                    ear = smoother.update(ear)
                else:
                    ear = None

                calibrating = not calibration.ready
                closed_pred = 0
                if ear is not None:
                    if calibrating:
                        calibration.add(ear, now)
                        if calibration.ready:
                            calibrated = f"{calibration.threshold_value:.4f}"
                            detector_blink.set_threshold(
                                calibration.threshold_value, reopen_margin
                            )
                            detector_blink.reset()
                            print(
                                f"\n>>> Umbral calibrado: {calibrated} "
                                f"({calibration.count} muestras)"
                            )
                            if args.auto_cues:
                                next_cue = now + 1.0
                    else:
                        detector_blink.update(
                            ear, now, blink_score=vision.blink_score
                        )
                        closed_pred = int(detector_blink.is_closed)

                if args.auto_cues and not calibrating and next_cue is not None:
                    if now >= next_cue and presses < args.blinks:
                        label_until = now + LABEL_SECONDS
                        presses += 1
                        next_cue = now + args.cue_interval
                        print(f">>> PARPADEA AHORA ({presses}/{args.blinks})", flush=True)

                closed_real = int(now < label_until)
                threshold = (
                    calibration.threshold()
                    if not calibration.ready
                    else calibration.threshold_value
                )
                writer.writerow(
                    {
                        "time": f"{now - started:.3f}",
                        "ear": f"{ear:.6f}" if ear is not None else "",
                        "confidence": f"{vision.confidence:.3f}",
                        "closed_real": closed_real,
                        "closed_pred": closed_pred,
                        "threshold": f"{threshold:.4f}",
                        "threshold_calibrated": calibrated,
                        "calibrating": int(calibrating),
                        "blink_score": (
                            f"{vision.blink_score:.3f}"
                            if vision.blink_score is not None
                            else ""
                        ),
                    }
                )
                rows += 1

                if now - last_status >= 0.5:
                    last_status = now
                    state = "CALIBRANDO" if calibrating else "GRABANDO"
                    print(
                        f"\rt={now - started:5.1f}s  {state}  filas={rows}  "
                        f"etiquetas={presses}  umbral={calibrated or '...'}   ",
                        end="",
                        flush=True,
                    )

                key = _read_key()
                if key == " ":
                    label_until = time.monotonic() + LABEL_SECONDS
                    presses += 1
                elif key in ("\r", "\n", "q", "\x1b"):
                    break
    finally:
        camera.stop()
        detector.close()

    print()
    if not calibration.ready:
        print("AVISO: la calibración no terminó; repite con el rostro visible.")
    print(f"Guardado: {output}")
    print(f"Filas: {rows} | etiquetas: {presses} | umbral calibrado: {calibrated or 'n/d'}")
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="tools/data/ear_session.csv")
    parser.add_argument("--seconds", type=float, default=40.0)
    parser.add_argument(
        "--camera-index",
        type=int,
        default=None,
        help="Override de camera.index de settings.yaml",
    )
    parser.add_argument(
        "--auto-cues",
        action="store_true",
        help="Etiquetar automáticamente cada cue_interval segundos (sin teclado)",
    )
    parser.add_argument("--cue-interval", type=float, default=3.0)
    parser.add_argument("--blinks", type=int, default=10)
    return record(parser.parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
