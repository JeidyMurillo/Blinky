"""Motor que evalúa reglas y emite recomendaciones.

Qué va aquí:
- Ejecutar todas las reglas en orden de prioridad.
- Evitar repetir la misma alerta antes del cooldown.
- Publicar "decision.recommendation" en el EventBus.

Uso:
    engine = DecisionEngine(settings, bus)
    engine.evaluate(blink_metrics, exposure_metrics, ambient_reading)
"""

from datetime import datetime, timedelta

from fatiga_visual.decision import rules

RULES = (
    rules.combined_blink_light,
    rules.low_blink_rate,
    rules.prolonged_eye_closure,
    rules.continuous_exposure,
    rules.ambient_light,
    rules.ambient_temperature,
    rules.ambient_humidity,
)


class DecisionEngine:
    def __init__(self, settings, bus=None, cooldown_seconds=300):
        self.settings = settings
        self.bus = bus
        self.cooldown = timedelta(seconds=cooldown_seconds)
        self._last_emitted = {}

    def evaluate(self, blink=None, exposure=None, ambient=None):
        thresholds = self.settings.section("thresholds") if self.settings else {}
        now = datetime.now()
        results = []
        for rule in RULES:
            recommendation = rule(blink, exposure, ambient, thresholds)
            if recommendation is None:
                continue
            previous = self._last_emitted.get(recommendation.id)
            if previous is not None and now - previous < self.cooldown:
                continue
            self._last_emitted[recommendation.id] = now
            results.append(recommendation)
            if self.bus is not None:
                self.bus.publish("decision.recommendation", recommendation)
        return results
