"""Bus de eventos en proceso.

Qué va aquí:
- Comunicación desacoplada entre visión, exposición, ambiente, decisión y UI.
- Temas sugeridos: "blink.metrics", "exposure.metrics", "ambient.reading",
  "decision.recommendation", "ui.navigate".

No usar para datos de alta frecuencia (frames): para eso se usa el último
fotograma compartido de vision.camera.
"""

import threading
from collections import defaultdict


class EventBus:
    def __init__(self):
        self._subscribers = defaultdict(list)
        self._lock = threading.Lock()

    def subscribe(self, topic, handler):
        with self._lock:
            self._subscribers[topic].append(handler)

    def unsubscribe(self, topic, handler):
        with self._lock:
            if handler in self._subscribers.get(topic, []):
                self._subscribers[topic].remove(handler)

    def publish(self, topic, payload=None):
        with self._lock:
            handlers = list(self._subscribers.get(topic, []))
        for handler in handlers:
            handler(payload)
