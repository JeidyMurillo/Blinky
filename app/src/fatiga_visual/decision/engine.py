"""Motor que evalúa reglas y emite recomendaciones.

Qué va aquí:
- Ejecutar todas las reglas en orden de prioridad.
- Confirmar la tasa de parpadeo baja durante una ventana entre evaluaciones.
- Evitar repetir la misma alerta antes del cooldown.
- Publicar "decision.recommendation" en el EventBus.

Uso:
    engine = DecisionEngine(settings, bus)
    engine.evaluate(blink_metrics, exposure_metrics, ambient_reading)
"""

from datetime import datetime, timedelta

from fatiga_visual.decision import rules


class DecisionEngine:
    def __init__(self, settings, bus=None, cooldown_seconds=300):
        self.settings = settings
        self.bus = bus
        self.cooldown = timedelta(seconds=cooldown_seconds)
        self._last_emitted = {}
        self._low_blink_rate = rules.SustainedLowBlinkRate()

    def _rules(self):
        return (
            rules.combined_blink_light,
            self._low_blink_rate,
            rules.prolonged_eye_closure,
            rules.continuous_exposure,
            rules.ambient_light,
            rules.ambient_temperature,
            rules.ambient_humidity,
        )

    def evaluate(self, blink=None, exposure=None, ambient=None, now=None):
        thresholds = self.settings.section("thresholds") if self.settings else {}
        now = now or datetime.now()
        results = []
        for rule in self._rules():
            if rule is self._low_blink_rate:
                recommendation = rule(blink, exposure, ambient, thresholds, now=now)
            else:
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
