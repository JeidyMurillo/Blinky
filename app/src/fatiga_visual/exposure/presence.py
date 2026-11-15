"""Detección de presencia del usuario frente a la pantalla.

Qué va aquí:
- Convertir landmarks/rostro detectado en presencia estable con histéresis.
- Evitar contar ausencias de 1-2 segundos como pausas.

Pendiente:
- Alimentar desde vision.face_landmarks y emitir cambios por EventBus.
"""


class PresenceTracker:
    def __init__(self, absent_after_seconds=20):
        self.absent_after_seconds = absent_after_seconds
        self.present = False
        self._last_seen = None

    def update(self, face_found, now):
        if face_found:
            self._last_seen = now
            self.present = True
        elif self._last_seen is not None:
            self.present = (now - self._last_seen).total_seconds() < self.absent_after_seconds
        return self.present
