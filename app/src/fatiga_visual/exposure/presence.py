"""Detección de presencia del usuario frente a la pantalla.

Convierte la detección de rostro/landmarks en estado presente/ausente con
histéresis para evitar falsos cambios por pérdidas breves.
"""

from datetime import datetime

from fatiga_visual.core.models import PresenceEvent


class PresenceTracker:
    def __init__(self, absent_after_seconds=20):
        self.absent_after_seconds = max(0.0, float(absent_after_seconds))
        self.present = False
        self._last_seen = None
        self._initialized = False
        self._last_confidence = 0.0

    def update(self, face_found, now, confidence=1.0):
        """Actualiza presencia y retorna PresenceEvent solo cuando cambia."""
        now = now if isinstance(now, datetime) else datetime.now()
        previous = self.present
        conf = confidence

        if face_found:
            self._last_seen = now
            self.present = True
            self._last_confidence = max(0.0, min(1.0, float(confidence)))
        elif self._last_seen is not None:
            self.present = (
                now - self._last_seen
            ).total_seconds() < self.absent_after_seconds
            if not self.present:
                self._last_confidence = 0.0
        else:
            self.present = False
            self._last_confidence = 0.0

        changed = (not self._initialized) or (previous != self.present)
        self._initialized = True
        if not changed:
            return None
        return PresenceEvent(
            timestamp=now,
            present=self.present,
            confidence=self._last_confidence if self.present else 0.0,
        )
