"""Último estado ambiental validado y su antigüedad.

Qué va aquí:
- Guardar la última lectura del ESP32 de forma segura entre hilos.
- Marcar la conexión como perdida si no llegan datos en N segundos.
"""

import threading
from datetime import datetime


class AmbientState:
    def __init__(self, stale_after_seconds=15):
        self.stale_after_seconds = stale_after_seconds
        self._reading = None
        self._received_at = None
        self._lock = threading.Lock()

    def update(self, reading):
        with self._lock:
            self._reading = reading
            self._received_at = datetime.now()

    def latest(self):
        with self._lock:
            reading = self._reading
            received = self._received_at
        if reading is None:
            return None
        connected = (datetime.now() - received).total_seconds() <= self.stale_after_seconds
        return reading.__class__(**{**reading.__dict__, "connected": connected})
