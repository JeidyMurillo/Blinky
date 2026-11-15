"""Contador de tiempo frente a la pantalla y pausas.

Qué va aquí:
- Acumular sesión y tiempo continuo.
- Marcar cuándo toca una pausa (por defecto, cada 20 minutos).
- Producir ExposureMetrics para decisión y UI.
"""

from datetime import datetime

from fatiga_visual.core.models import ExposureMetrics


class ExposureTimer:
    def __init__(self, break_after_minutes=20):
        self.break_after = break_after_minutes * 60
        self.session_seconds = 0
        self.continuous_seconds = 0
        self.breaks_taken = 0

    def tick(self, seconds=1, present=True):
        """Avanza el reloj. El tiempo continuo solo corre con el usuario presente."""
        self.session_seconds += seconds
        if present:
            self.continuous_seconds += seconds

    def take_break(self):
        self.breaks_taken += 1
        self.continuous_seconds = 0

    def reset_session(self):
        self.session_seconds = 0
        self.continuous_seconds = 0
        self.breaks_taken = 0

    @property
    def break_due(self):
        return self.continuous_seconds >= self.break_after

    def snapshot(self):
        return ExposureMetrics(
            timestamp=datetime.now(),
            session_seconds=int(self.session_seconds),
            continuous_seconds=int(self.continuous_seconds),
            breaks_taken=int(self.breaks_taken),
            break_due=self.break_due,
        )
