"""Evalúa una grabación de EAR y compara el umbral fijo contra el calibrado.

Uso (desde la raíz del repo):
    python tools\blink_eval.py ruta/al/registro.csv

Si el CSV tiene columnas `ear`, `closed_real` y `time` (las escribe
`tools/record_ear.py`), calcula exactitud, precisión y recall a nivel de
fotograma y de parpadeo para ambos umbrales. Las filas de calibración se
ignoran para que no falseen la comparación. El veredicto `MEJORA` usa la
exactitud de **parpadeos** (la métrica del sistema); la de fotogramas es
diagnóstica porque hay muchos más fotogramas abiertos que cerrados.

Sin esas columnas mantiene el comportamiento anterior: cuenta parpadeos con
`--threshold` (por defecto 0.21).
"""

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app" / "src"))

from fatiga_visual.core.config import load_settings  # noqa: E402
from fatiga_visual.vision.blink_detector import BlinkDetector  # noqa: E402

FIXED_THRESHOLD = 0.21


def read_rows(csv_path):
    with open(csv_path, newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def usable_rows(rows):
    """Descarta filas sin EAR y las de calibración (no tienen etiqueta válida)."""
    selected = []
    for row in rows:
        ear = (row.get("ear") or "").strip()
        calibrating = (row.get("calibrating") or "0").strip()
        if not ear or calibrating == "1":
            continue
        try:
            float(ear)
        except ValueError:
            continue
        selected.append(row)
    return selected


def calibrated_threshold_from(rows, override=None):
    if override is not None:
        return float(override)
    for row in rows:
        value = (row.get("threshold_calibrated") or "").strip()
        if value:
            return float(value)
    return None


def frame_metrics(rows, threshold):
    tp = fp = fn = tn = 0
    for row in rows:
        ear = float(row["ear"])
        real = int(float(row.get("closed_real") or 0)) == 1
        predicted = ear < threshold
        if predicted and real:
            tp += 1
        elif predicted and not real:
            fp += 1
        elif not predicted and real:
            fn += 1
        else:
            tn += 1
    total = tp + fp + fn + tn
    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
        "accuracy": (tp + tn) / total if total else 0.0,
        "precision": tp / (tp + fp) if tp + fp else 0.0,
        "recall": tp / (tp + fn) if tp + fn else 0.0,
    }


def real_blink_times(rows):
    """Un parpadeo real empieza en cada flanco ascendente de closed_real."""
    times = []
    previous = 0
    for row in rows:
        label = int(float(row.get("closed_real") or 0))
        if label == 1 and previous == 0:
            times.append(float(row.get("time") or 0.0))
        previous = label
    return times


def detected_blink_times(rows, threshold, settings):
    """Instante en que se confirma cada cierre (evento 'closed').

    La etiqueta closed_real marca el inicio del cierre, así que hay que
    compararla con 'closed', no con 'opened' (que ocurre al reabrir, ~0.4 s
    después y hacía parecer que fallaba la detección).
    """
    detector = BlinkDetector(
        threshold=threshold,
        min_closed_frames=int(settings.get("vision.min_closed_frames", 2)),
        max_closed_frames=int(settings.get("vision.max_closed_frames", 15)),
        reopen_margin=float(settings.get("vision.reopen_margin", 0.02)),
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
    times = []
    for row in rows:
        event = detector.update(float(row["ear"]), float(row.get("time") or 0.0))
        if event == "closed":
            times.append(float(row.get("time") or 0.0))
    return times


def event_metrics(real, detected, tolerance=0.6):
    """Empareja cada parpadeo real con el detectado más cercano dentro de tolerance."""
    used = set()
    true_positives = 0
    for moment in real:
        candidates = [
            index
            for index, found in enumerate(detected)
            if index not in used and abs(found - moment) <= tolerance
        ]
        if candidates:
            best = min(candidates, key=lambda index: abs(detected[index] - moment))
            used.add(best)
            true_positives += 1
    false_positives = len(detected) - true_positives
    false_negatives = len(real) - true_positives
    denominator = true_positives + false_positives + false_negatives
    return {
        "real": len(real),
        "detected": len(detected),
        "tp": true_positives,
        "fp": false_positives,
        "fn": false_negatives,
        "accuracy": true_positives / denominator if denominator else 1.0,
        "precision": (
            true_positives / (true_positives + false_positives)
            if true_positives + false_positives
            else 0.0
        ),
        "recall": (
            true_positives / (true_positives + false_negatives)
            if true_positives + false_negatives
            else 0.0
        ),
    }


def _show(name, threshold, frames, events):
    print(f"{name}: umbral={threshold:.4f}")
    print(
        "  fotogramas: "
        f"exactitud={frames['accuracy']:.1%}  precisión={frames['precision']:.1%}  "
        f"recall={frames['recall']:.1%}  (TP={frames['tp']} FP={frames['fp']} "
        f"FN={frames['fn']} TN={frames['tn']})"
    )
    print(
        "  parpadeos:  "
        f"reales={events['real']}  detectados={events['detected']}  "
        f"TP={events['tp']} FP={events['fp']} FN={events['fn']}  "
        f"exactitud={events['accuracy']:.1%}"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_path")
    parser.add_argument("--threshold", type=float, default=FIXED_THRESHOLD)
    parser.add_argument("--calibrated-threshold", type=float, default=None)
    parser.add_argument("--tolerance", type=float, default=0.6)
    args = parser.parse_args()

    rows = read_rows(args.csv_path)
    selected = usable_rows(rows)
    if not selected:
        print("ERROR: el CSV no tiene filas de EAR utilizables.")
        return 1

    # Modo original: sin etiquetas de verdad, solo se cuenta.
    if "closed_real" not in (rows[0] if rows else {}):
        detector = BlinkDetector(threshold=args.threshold)
        count = 0
        for row in selected:
            if detector.update(float(row["ear"])) == "opened":
                count += 1
        print(f"muestras: {len(selected)}")
        print(f"parpadeos: {count}")
        print(f"umbral: {args.threshold}")
        return 0

    settings = load_settings()
    real = real_blink_times(selected)

    fixed_frames = frame_metrics(selected, args.threshold)
    fixed_events = event_metrics(
        real, detected_blink_times(selected, args.threshold, settings), args.tolerance
    )
    _show("UMBRAL FIJO", args.threshold, fixed_frames, fixed_events)

    calibrated = calibrated_threshold_from(rows, args.calibrated_threshold)
    if calibrated is None:
        print("\nAVISO: el CSV no trae umbral calibrado y no se pasó --calibrated-threshold.")
        return 0

    calibrated_frames = frame_metrics(selected, calibrated)
    calibrated_events = event_metrics(
        real, detected_blink_times(selected, calibrated, settings), args.tolerance
    )
    _show("UMBRAL CALIBRADO", calibrated, calibrated_frames, calibrated_events)

    # La métrica del sistema es la detección de parpadeos. La exactitud por
    # fotograma queda como diagnóstico: hay muchos más fotogramas con ojos
    # abiertos que cerrados y un solo FP pesa más que varios FN.
    improves = calibrated_events["accuracy"] >= fixed_events["accuracy"]
    print(
        f"\nMEJORA: {'SÍ' if improves else 'NO'} (parpadeos: "
        f"{fixed_events['accuracy']:.1%} -> {calibrated_events['accuracy']:.1%}). "
        f"Fotogramas: {fixed_frames['accuracy']:.1%} -> "
        f"{calibrated_frames['accuracy']:.1%} (solo diagnóstico)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
