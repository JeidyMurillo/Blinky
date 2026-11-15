"""Calibración del umbral de EAR por usuario.

El EAR de ojo abierto cambia con la persona, las gafas, la distancia a la
cámara y la iluminación. En vez de usar 0.21 para todos:

1. Se recogen muestras de ojo abierto durante unos segundos.
2. Se descarta la cola de valores bajos (parpadeos) y se usa el percentil 75.
3. El umbral queda en una fracción de ese valor, con límites de seguridad.

El umbral aprendido se puede guardar en JSON para la siguiente sesión, pero
cada inicio de sesión vuelve a calibrar para adaptarse a la luz actual.
"""

import json
import math
import statistics
import time
from datetime import datetime
from pathlib import Path


def _seconds(timestamp):
    if timestamp is None:
        return time.monotonic()
    if isinstance(timestamp, (int, float)):
        return float(timestamp)
    if isinstance(timestamp, datetime):
        return timestamp.timestamp()
    return float(timestamp)


def _percentile(values, fraction):
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * min(1.0, max(0.0, fraction))
    lower = int(math.floor(position))
    upper = int(math.ceil(position))
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


class EarCalibration:
    def __init__(
        self,
        seconds=5.0,
        min_samples=30,
        fallback=0.21,
        ratio=0.60,
        floor=0.06,
        ceiling=0.28,
        deviation_factor=1.5,
    ):
        self.seconds = max(0.0, float(seconds))
        self.min_samples = max(1, int(min_samples))
        self.fallback = float(fallback)
        self.ratio = min(0.95, max(0.3, float(ratio)))
        self.floor = float(floor)
        self.ceiling = float(ceiling)
        self.deviation_factor = max(0.0, float(deviation_factor))

        self._samples = []
        self._started_at = None
        self._last_timestamp = None
        self._ready = False
        self._threshold = self.fallback
        self._stats = {}

    @property
    def ready(self):
        return self._ready

    @property
    def count(self):
        return len(self._samples)

    @property
    def threshold_value(self):
        return self._threshold

    @property
    def stats(self):
        return dict(self._stats)

    def start(self, timestamp=None):
        self._samples.clear()
        self._started_at = _seconds(timestamp)
        self._last_timestamp = self._started_at
        self._ready = False
        self._threshold = self.fallback
        self._stats = {}

    def add(self, ear, timestamp=None):
        if ear is None:
            return
        try:
            ear = float(ear)
        except (TypeError, ValueError):
            return
        if not math.isfinite(ear) or ear <= 0.0 or ear >= 1.0:
            return

        now = _seconds(timestamp)
        if self._started_at is None:
            self._started_at = now
        self._last_timestamp = now

        # Durante la calibración se pide mirada al frente. Solo se descartan
        # ojos prácticamente cerrados; un umbral relativo descartaría a
        # personas con ojos pequeños. También se descartan lecturas
        # imposibles (rostro parcialmente fuera de cuadro o landmarks malos):
        # un ojo abierto real no supera ~0.45 de EAR.
        if ear < 0.05 or ear > 0.50:
            return

        self._samples.append(ear)
        if self.ready:
            return
        elapsed = max(0.0, now - self._started_at)
        if len(self._samples) >= self.min_samples and elapsed >= self.seconds:
            self._calculate(elapsed)

    def _calculate(self, elapsed):
        values = sorted(self._samples)
        # Recorta el 10% inferior (parpadeos) y el 10% superior (lecturas
        # ruidosas por rostro parcialmente fuera de cuadro). Calcular el p75
        # sobre el núcleo evita que un par de outliers inflen el umbral.
        lower = int(len(values) * 0.10)
        upper = max(lower + 1, int(len(values) * 0.90))
        core = values[lower:upper]
        median = statistics.median(core)
        open_ear = _percentile(core, 0.75)
        deviation = statistics.pstdev(core) if len(core) > 1 else 0.0

        statistical = median - max(0.02, self.deviation_factor * deviation)
        # El umbral es una fracción del EAR de ojo abierto. La fracción 0.60
        # separa el ruido normal (que no baja del ~75% del valor abierto) de un
        # parpadeo real, también en usuarios con ojos pequeños o cámara lejos.
        threshold = min(open_ear * self.ratio, statistical)
        threshold = max(self.floor, min(self.ceiling, threshold))

        self._threshold = round(threshold, 4)
        self._ready = True
        self._stats = {
            "samples": len(values),
            "elapsed_seconds": round(elapsed, 2),
            "median": round(median, 4),
            "open_ear_p75": round(open_ear, 4),
            "deviation": round(deviation, 4),
            "threshold": self._threshold,
        }

    def threshold(self):
        """Umbral actual; devuelve el fallback mientras no haya calibración."""
        return self._threshold if self._ready else self.fallback

    def progress(self, timestamp=None):
        if self.ready:
            return 1.0
        if self._started_at is None:
            return 0.0
        now = _seconds(timestamp) if timestamp is not None else time.monotonic()
        elapsed = max(0.0, now - self._started_at)
        by_time = elapsed / self.seconds if self.seconds > 0 else 1.0
        by_samples = len(self._samples) / self.min_samples
        # La calibración termina solo cuando se cumplen AMBOS requisitos, así
        # que el progreso real es el mínimo. Nunca muestra 100% antes de estar
        # lista (importante cuando el rostro aparece de forma intermitente).
        return round(min(0.99, min(by_time, by_samples)), 3)

    def reset(self):
        self._samples.clear()
        self._started_at = None
        self._last_timestamp = None
        self._ready = False
        self._threshold = self.fallback
        self._stats = {}

    def as_dict(self):
        return {
            "threshold": self._threshold if self._ready else self.fallback,
            "ready": self._ready,
            "stats": self.stats,
            "updated_at": datetime.now().isoformat(timespec="seconds"),
        }

    def save(self, path):
        try:
            path = Path(path)
            path.parent.mkdir(parents=True, exist_ok=True)
            temporary = path.with_suffix(path.suffix + ".tmp")
            temporary.write_text(json.dumps(self.as_dict(), indent=2), encoding="utf-8")
            temporary.replace(path)
        except OSError:
            return False
        return True

    def load(self, path):
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                return False
            threshold = float(data.get("threshold", self.fallback))
            stats = data.get("stats", {})
            if not isinstance(stats, dict):
                stats = {}
            median = float(stats.get("median", threshold))
        except (OSError, ValueError, TypeError):
            return False
        # Descarta calibraciones corruptas (p. ej. guardadas cuando el rostro
        # estaba parcialmente fuera de cuadro y el EAR medía >0.5).
        if not 0.05 <= threshold <= 0.45:
            return False
        if not 0.05 <= median <= 0.50:
            return False
        self._threshold = threshold
        self._ready = bool(data.get("ready", True))
        self._stats = dict(stats)
        return True
