"""Lógica de pausas y rutina 20-20-20.

Qué va aquí:
- Decidir cuándo sugerir pausa y durante cuánto tiempo.
- Registrar pausas completadas para estadísticas.
"""


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
