"""Agregación de parpadeos en métricas para decisión y UI.

Además de la tasa por minuto, calcula indicadores útiles de fatiga visual:

- `mean_blink_duration_ms`: duración media de los parpadeos de la ventana.
- `inter_blink_seconds`: intervalo medio entre parpadeos.
- `perclos`: fracción del tiempo con los ojos cerrados (PERCLOS).
- `long_closures`: cierres oculares prolongados dentro de la ventana.

La tasa usa una ventana móvil de 60 s y un mínimo de observación de 10 s para
no disparar alertas absurdas durante los primeros segundos.
"""

from collections import deque
from datetime import datetime, timedelta

from fatiga_visual.core.models import BlinkMetrics


class BlinkMetricsAggregator:
    def __init__(self, window_seconds=60, min_rate_window_seconds=10.0):
        self.window_seconds = max(1.0, float(window_seconds))
        self.window = timedelta(seconds=self.window_seconds)
        self.min_rate_window_seconds = max(1.0, float(min_rate_window_seconds))

        self._events = deque()
        self._long_closures = deque()
        self._closed_intervals = deque()
        self._total = 0
        self._long_total = 0
        self._eyes_closed = False
        self._closed_since = None
        self._started_at = None
        self._last_blink_at = None
        self._last_interval_seconds = 0.0
        self._last_duration_ms = 0.0

    @property
    def eyes_closed(self):
        return self._eyes_closed

    @property
    def total_blinks(self):
        return self._total

    @property
    def total_long_closures(self):
        return self._long_total

    def start(self, timestamp=None):
        self._started_at = timestamp or datetime.now()

    def add_blink(self, timestamp=None, ear=0.0, duration_ms=None):
        now = timestamp or datetime.now()
        if self._started_at is None:
            self._started_at = now
        if duration_ms is not None:
            self._last_duration_ms = max(0.0, float(duration_ms))
        if self._last_blink_at is not None:
            self._last_interval_seconds = max(
                0.0, (now - self._last_blink_at).total_seconds()
            )
        self._last_blink_at = now
        self._events.append((now, self._last_duration_ms))
        self._total += 1
        self._trim(now)

    def add_long_closure(self, timestamp=None, duration_ms=None):
        now = timestamp or datetime.now()
        if self._started_at is None:
            self._started_at = now
        if duration_ms is not None:
            self._last_duration_ms = max(0.0, float(duration_ms))
        self._long_closures.append(now)
        self._long_total += 1
        self._trim(now)

    def set_eyes_closed(self, closed, timestamp=None):
        now = timestamp or datetime.now()
        if self._started_at is None:
            self._started_at = now
        closed = bool(closed)
        if closed == self._eyes_closed:
            self._trim(now)
            return
        if closed:
            self._closed_since = now
        else:
            if self._closed_since is not None:
                self._closed_intervals.append((self._closed_since, now))
                self._closed_since = None
        self._eyes_closed = closed
        self._trim(now)

    def _trim(self, now):
        cutoff = now - self.window
        while self._events and self._events[0][0] < cutoff:
            self._events.popleft()
        while self._long_closures and self._long_closures[0] < cutoff:
            self._long_closures.popleft()
        while self._closed_intervals and self._closed_intervals[0][1] < cutoff:
            self._closed_intervals.popleft()

    def _closed_seconds(self, now):
        cutoff = now - self.window
        total = 0.0
        for start, end in self._closed_intervals:
            if end <= cutoff:
                continue
            total += max(0.0, (min(end, now) - max(start, cutoff)).total_seconds())
        if self._eyes_closed and self._closed_since is not None:
            total += max(0.0, (now - max(self._closed_since, cutoff)).total_seconds())
        return total

    def _inter_blink_seconds(self):
        if len(self._events) >= 2:
            gaps = [
                (self._events[index][0] - self._events[index - 1][0]).total_seconds()
                for index in range(1, len(self._events))
            ]
            gaps = [gap for gap in gaps if gap > 0]
            if gaps:
                return sum(gaps) / len(gaps)
        return self._last_interval_seconds

    def snapshot(
        self,
        ear=0.0,
        confidence=1.0,
        source="",
        calibration_progress=1.0,
        timestamp=None,
    ):
        now = timestamp or datetime.now()
        self._trim(now)

        elapsed = 0.0
        if self._started_at is not None:
            elapsed = max(0.0, (now - self._started_at).total_seconds())
        span = max(
            self.min_rate_window_seconds,
            min(elapsed, self.window_seconds),
        )
        rate = len(self._events) * (60.0 / span)
        rate = max(0.0, min(120.0, rate))

        durations = [duration for _, duration in self._events if duration > 0]
        mean_duration = sum(durations) / len(durations) if durations else 0.0
        observed = max(1.0, min(self.window_seconds, elapsed))
        perclos = max(0.0, min(1.0, self._closed_seconds(now) / observed))

        return BlinkMetrics(
            timestamp=now,
            blinks=self._total,
            blink_rate=round(rate, 1),
            eyes_closed=self._eyes_closed,
            ear=float(ear or 0.0),
            confidence=float(confidence),
            mean_blink_duration_ms=round(mean_duration, 1),
            last_blink_duration_ms=round(self._last_duration_ms, 1),
            inter_blink_seconds=round(self._inter_blink_seconds(), 2),
            perclos=round(perclos, 4),
            long_closures=len(self._long_closures),
            elapsed_seconds=round(elapsed, 1),
            calibration_progress=float(calibration_progress),
            source=source,
        )

    def reset(self):
        self._events.clear()
        self._long_closures.clear()
        self._closed_intervals.clear()
        self._total = 0
        self._long_total = 0
        self._eyes_closed = False
        self._closed_since = None
        self._started_at = None
        self._last_blink_at = None
        self._last_interval_seconds = 0.0
        self._last_duration_ms = 0.0
