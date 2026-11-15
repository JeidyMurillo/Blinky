"""Máquina de estados que convierte EAR en eventos de parpadeo.

Qué hace:
- Histéresis: cierra por debajo de `threshold` y vuelve a abrir por encima de
  `threshold + reopen_margin`. Así el ruido no genera parpadeos falsos.
- Exige `min_closed_frames` frames cerrados para confirmar un parpadeo.
- Clasifica por duración: parpadeo normal, cierre largo (fatiga) o descarte.
- Opcionalmente usa la blendshape `eyeBlink` de MediaPipe como señal auxiliar.

Contrato (compatible con el código anterior):
    detector.update(ear) -> "closed" | "opened" | "long_closure" | None

`update` acepta un timestamp (monótono o datetime) para medir duraciones. Si no
se pasa, se usa el reloj pero la clasificación se hace por frames, que es lo que
necesitan las pruebas antiguas.
"""

import time
from datetime import datetime


def _seconds(timestamp):
    if timestamp is None:
        return time.monotonic()
    if isinstance(timestamp, (int, float)):
        return float(timestamp)
    if isinstance(timestamp, datetime):
        return timestamp.timestamp()
    return float(timestamp)


class BlinkDetector:
    def __init__(
        self,
        threshold=0.21,
        min_closed_frames=2,
        max_closed_frames=15,
        reopen_margin=0.02,
        min_blink_duration_ms=0.0,
        max_blink_duration_ms=800.0,
        long_closure_seconds=1.5,
        blink_score_threshold=None,
        cooldown_seconds=0.0,
    ):
        self.threshold = float(threshold)
        self.min_closed_frames = max(1, int(min_closed_frames))
        self.max_closed_frames = int(max_closed_frames) if max_closed_frames else None
        self.reopen_margin = max(0.0, float(reopen_margin))
        self.min_blink_duration_ms = max(0.0, float(min_blink_duration_ms))
        self.max_blink_duration_ms = (
            max(0.0, float(max_blink_duration_ms))
            if max_blink_duration_ms is not None
            else None
        )
        self.long_closure_seconds = max(0.0, float(long_closure_seconds))
        self.blink_score_threshold = (
            float(blink_score_threshold) if blink_score_threshold is not None else None
        )
        self.cooldown_seconds = max(0.0, float(cooldown_seconds))

        self._closed_frames = 0
        self._in_closure = False
        self._confirmed = False
        self._closure_started = None
        self._last_ear = 0.0
        self._last_score = None

        self._last_event = None
        self._last_event_at = None
        self._last_duration_ms = 0.0
        self._last_blink_at = None
        self.blinks = 0
        self.long_closures = 0

    @property
    def reopen_threshold(self):
        return self.threshold + self.reopen_margin

    @property
    def is_closed(self):
        """Estado instantáneo (incluye el cierre aún no confirmado)."""
        return self._in_closure

    @property
    def confirmed_closed(self):
        """True desde que se confirma el cierre hasta que vuelve a abrir."""
        return self._confirmed

    @property
    def closed_frames(self):
        return self._closed_frames

    @property
    def last_event(self):
        return self._last_event

    @property
    def last_duration_ms(self):
        return self._last_duration_ms

    @property
    def last_blink_at(self):
        return self._last_blink_at

    @property
    def last_ear(self):
        return self._last_ear

    def set_threshold(self, threshold, reopen_margin=None):
        self.threshold = float(threshold)
        if reopen_margin is not None:
            self.reopen_margin = max(0.0, float(reopen_margin))

    def _score_closed(self, score):
        return (
            self.blink_score_threshold is not None
            and score is not None
            and score >= self.blink_score_threshold
        )

    def _is_closing(self, ear, score):
        return ear < self.threshold or self._score_closed(score)

    def _is_reopening(self, ear):
        # El EAR es la señal geométrica principal: si el ojo ya está abierto,
        # el cierre termina aunque la blendshape tarde en bajar. Así una
        # blendshape "atascada" no alarga un parpadeo ni lo convierte en cierre
        # largo por error.
        return ear >= self.reopen_threshold

    def update(self, ear, timestamp=None, blink_score=None):
        if ear is None and blink_score is None:
            return None
        timed = timestamp is not None
        now = _seconds(timestamp)
        if ear is None:
            ear = self._last_ear
        ear = float(ear)
        score = float(blink_score) if blink_score is not None else None
        self._last_ear = ear
        self._last_score = score

        if self._in_closure:
            if self._is_reopening(ear):
                return self._finish_closure(now, timed)
            self._closed_frames += 1
            if not self._confirmed and self._closed_frames >= self.min_closed_frames:
                self._confirmed = True
                return self._emit("closed", 0.0, now)
            return None

        if self._is_closing(ear, score):
            self._in_closure = True
            self._confirmed = False
            self._closed_frames = 1
            self._closure_started = now
            if self._closed_frames >= self.min_closed_frames:
                self._confirmed = True
                return self._emit("closed", 0.0, now)
            return None

        return None

    def _finish_closure(self, now, timed):
        closed_frames = self._closed_frames
        duration = 0.0
        if self._closure_started is not None:
            duration = max(0.0, now - self._closure_started)
        duration_ms = duration * 1000.0

        self._in_closure = False
        self._closed_frames = 0
        self._closure_started = None
        was_confirmed = self._confirmed
        self._confirmed = False
        self._last_duration_ms = duration_ms

        if not was_confirmed:
            return None

        if timed:
            if duration_ms < self.min_blink_duration_ms:
                return None
            limit_ms = None
            if self.max_blink_duration_ms is not None:
                limit_ms = self.max_blink_duration_ms
            if self.long_closure_seconds > 0:
                long_ms = self.long_closure_seconds * 1000.0
                limit_ms = long_ms if limit_ms is None else min(limit_ms, long_ms)
            if limit_ms is not None and duration_ms >= limit_ms:
                self.long_closures += 1
                return self._emit("long_closure", duration_ms, now)
        elif self.max_closed_frames is not None and closed_frames > self.max_closed_frames:
            self.long_closures += 1
            return self._emit("long_closure", duration_ms, now)

        if self.cooldown_seconds > 0 and self._last_blink_at is not None:
            if now - _seconds(self._last_blink_at) < self.cooldown_seconds:
                return None

        self.blinks += 1
        self._last_blink_at = now
        return self._emit("opened", duration_ms, now)

    def _emit(self, kind, duration_ms, now):
        self._last_event = kind
        self._last_event_at = now
        self._last_duration_ms = duration_ms
        return kind

    def reset(self):
        """Olvida el cierre en curso, pero conserva los contadores de sesión."""
        self._closed_frames = 0
        self._in_closure = False
        self._confirmed = False
        self._closure_started = None

    def reset_counters(self):
        self.blinks = 0
        self.long_closures = 0
        self._last_duration_ms = 0.0
        self._last_event = None
        self._last_event_at = None
        self._last_blink_at = None
