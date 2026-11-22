"""Lógica de pausas y rutina 20-20-20.

Qué va aquí:
- Decidir cuándo sugerir pausa y durante cuánto tiempo.
- Detectar ausencias lo bastante largas para contar como pausa válida.
- Registrar pausas completadas para estadísticas.
"""

from fatiga_visual.core.models import BreakEvent


class BreakDetector:
    """Convierte la detección de rostro en pausas válidas.

    Una ausencia corta no cuenta (HU-07): solo se valida cuando supera
    `min_break_seconds`. En ese momento devuelve un evento ``started`` (el
    contador continuo debe reiniciarse) y, cuando vuelve el rostro, un evento
    ``finished`` con la duración real de la pausa (HU-08).
    """

    def __init__(self, min_break_seconds=20):
        self.min_break_seconds = max(0.0, float(min_break_seconds))
        self.absent_since = None
        self.started_at = None
        self.active = False
        self._continuous_before = 0.0

    def update(self, face_found, now, continuous_seconds=0.0):
        """Actualiza el detector y devuelve un `BreakEvent` o None."""
        if face_found:
            if self.active:
                duration = max(0.0, (now - self.started_at).total_seconds())
                event = BreakEvent(
                    timestamp=now,
                    started_at=self.started_at,
                    kind="finished",
                    duration_seconds=duration,
                    continuous_before_seconds=self._continuous_before,
                )
                self.active = False
                self.absent_since = None
                self.started_at = None
                return event
            self.absent_since = None
            return None

        if self.absent_since is None:
            self.absent_since = now
            return None
        if self.active:
            return None
        if (now - self.absent_since).total_seconds() < self.min_break_seconds:
            return None

        self.active = True
        self.started_at = self.absent_since
        self._continuous_before = continuous_seconds
        return BreakEvent(
            timestamp=now,
            started_at=self.started_at,
            kind="started",
            continuous_before_seconds=continuous_seconds,
        )

    def reset(self):
        """Descarta la ausencia en curso sin registrar ninguna pausa."""
        self.absent_since = None
        self.started_at = None
        self.active = False
        self._continuous_before = 0.0


class BreakScheduler:
    def __init__(self, interval_minutes=20, duration_seconds=20):
        self.interval_seconds = interval_minutes * 60
        self.duration_seconds = duration_seconds
        self._next_break = self.interval_seconds

    def update(self, continuous_seconds):
        if continuous_seconds >= self._next_break:
            self._next_break = continuous_seconds + self.interval_seconds
            return True
        return False

    def take_break(self):
        self._next_break = self.interval_seconds
