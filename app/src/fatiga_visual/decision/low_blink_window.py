"""Ventana de confirmación temporal para la regla de tasa de parpadeo baja."""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class LowBlinkRateWindow:
    """Acumula muestras consecutivas con tasa de parpadeo bajo el umbral."""

    low_since: datetime | None = None
    last_sample_at: datetime | None = None
    samples: int = 0

    def update(
        self,
        low,
        now=None,
        window_seconds=60.0,
        min_samples=3,
        max_gap_seconds=None,
    ):
        now = now or datetime.now()
        gap_limit = window_seconds if max_gap_seconds is None else max_gap_seconds
        if not low:
            self.reset()
            return False
        if self.last_sample_at is not None:
            gap = (now - self.last_sample_at).total_seconds()
            if gap < 0 or gap > gap_limit:
                self.reset()
        if self.low_since is None:
            self.low_since = now
        self.last_sample_at = now
        self.samples += 1
        return (
            self.samples >= min_samples
            and (now - self.low_since).total_seconds() >= window_seconds
        )

    def elapsed(self, now=None):
        if self.low_since is None:
            return 0.0
        now = now or datetime.now()
        return max(0.0, (now - self.low_since).total_seconds())

    def reset(self):
        self.low_since = None
        self.last_sample_at = None
        self.samples = 0
