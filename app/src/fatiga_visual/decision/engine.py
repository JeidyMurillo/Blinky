"""Motor que evalúa reglas y emite recomendaciones.

Qué va aquí:
- Ejecutar todas las reglas en orden de prioridad.
- Confirmar la tasa de parpadeo baja durante una ventana entre evaluaciones.
- Evitar repetir la misma alerta antes del cooldown configurado.
- Publicar "decision.recommendation" en el EventBus.

Uso:
    engine = DecisionEngine(settings, bus)
    engine.evaluate(blink_metrics, exposure_metrics, ambient_reading)

Los umbrales (incluido `cooldown_seconds`) se leen de settings.yaml, sección
`thresholds:`. El argumento `cooldown_seconds` solo sirve para inyectar un
valor en pruebas; si se omite, se toma de la configuración.
"""

from datetime import datetime, timedelta

from fatiga_visual.core.config import DEFAULTS
from fatiga_visual.decision import rules


def _thresholds(settings):
    return (
        settings.section("thresholds")
        if settings is not None
        else dict(DEFAULTS["thresholds"])
    )


class DecisionEngine:
    def __init__(self, settings, bus=None, cooldown_seconds=None):
        self.settings = settings
        self.bus = bus
        seconds = (
            _thresholds(settings)["cooldown_seconds"]
            if cooldown_seconds is None
            else cooldown_seconds
        )
        self.cooldown = timedelta(seconds=float(seconds))
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
        thresholds = _thresholds(self.settings)
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
