"""Evalúa una grabación de EAR y cuenta parpadeos.

Uso:
    python tools/blink_eval.py ruta/al/registro.csv [--threshold 0.21]

El CSV debe tener una columna llamada "ear" (una muestra por fila). Sirve para
comparar el detector contra una grabación etiquetada y ajustar el umbral.
"""

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app" / "src"))

from fatiga_visual.vision.blink_detector import BlinkDetector


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_path")
    parser.add_argument("--threshold", type=float, default=0.21)
    args = parser.parse_args()

    detector = BlinkDetector(threshold=args.threshold)
    blinks = 0
    samples = 0
    with open(args.csv_path, newline="", encoding="utf-8") as file:
        for row in csv.DictReader(file):
            samples += 1
            event = detector.update(float(row["ear"]))
            if event == "opened":
                blinks += 1

    print(f"muestras: {samples}")
    print(f"parpadeos: {blinks}")
    print(f"umbral: {args.threshold}")


if __name__ == "__main__":
    main()
