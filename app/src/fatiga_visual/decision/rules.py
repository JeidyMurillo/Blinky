"""Reglas independientes del motor.

Qué va aquí:
- Cada regla es una función pura: entradas -> Recommendation | None.
- Los umbrales llegan desde settings.yaml (sección `thresholds:`). En este
  módulo no queda ningún valor fijo: core/config.py DEFAULTS es el espejo
  usado cuando no hay archivo YAML (por ejemplo, en las pruebas).

El parámetro `thresholds` es el mapping devuelto por
Settings.section("thresholds"), que ya incluye todos los valores por defecto.

Para añadir una regla: función nueva + incluirla en engine.RULES.
"""

from fatiga_visual.decision import recommendations


def _reliable(blink, thresholds):
    return getattr(blink, "confidence", 1.0) >= thresholds["min_confidence"]


def _ambient_data(ambient):
    """Solo lecturas vigentes del nodo IoT; nunca valores viejos ni inventados."""
    return ambient is not None and getattr(ambient, "connected", True)


def low_blink_rate(blink, exposure, ambient, thresholds):
    if blink is None or not _reliable(blink, thresholds):
        return None
    warmup = thresholds["blink_warmup_seconds"]
    elapsed = getattr(blink, "elapsed_seconds", 0.0)
    # Durante el arranque hay pocos datos; 0 significa "sin información".
    if 0 < elapsed < warmup:
        return None
    limit = thresholds["blink_rate_low"]
    if blink.blink_rate < limit:
        return recommendations.low_blink_rate(blink.blink_rate)
    return None


def prolonged_eye_closure(blink, exposure, ambient, thresholds):
    if blink is None or not _reliable(blink, thresholds):
        return None
    perclos_limit = thresholds["perclos_high"]
    long_limit = thresholds["long_closures_per_minute"]
    if blink.perclos >= perclos_limit or blink.long_closures >= long_limit:
        return recommendations.prolonged_eye_closure(
            blink.perclos, blink.long_closures
        )
    return None


def continuous_exposure(blink, exposure, ambient, thresholds):
    if exposure is None:
        return None
    limit = thresholds["continuous_minutes"]
    if exposure.continuous_seconds >= limit * 60:
        return recommendations.long_exposure(exposure.continuous_seconds / 60)
    return None


def ambient_light(blink, exposure, ambient, thresholds):
    if not _ambient_data(ambient):
        return None
    lux_min = thresholds["lux_min"]
    lux_max = thresholds["lux_max"]
    if ambient.lux < lux_min:
        return recommendations.lighting_out_of_range(ambient.lux, low=True)
    if ambient.lux > lux_max:
        return recommendations.lighting_out_of_range(ambient.lux, low=False)
    return None


def ambient_temperature(blink, exposure, ambient, thresholds):
    if not _ambient_data(ambient):
        return None
    temperature_min = thresholds["temperature_min"]
    temperature_max = thresholds["temperature_max"]
    if ambient.temperature_c < temperature_min:
        return recommendations.temperature_out_of_range(ambient.temperature_c, low=True)
    if ambient.temperature_c > temperature_max:
        return recommendations.temperature_out_of_range(ambient.temperature_c, low=False)
    return None


def ambient_humidity(blink, exposure, ambient, thresholds):
    if not _ambient_data(ambient):
        return None
    humidity_min = thresholds["humidity_min"]
    humidity_max = thresholds["humidity_max"]
    if ambient.humidity < humidity_min:
        return recommendations.humidity_out_of_range(ambient.humidity, low=True)
    if ambient.humidity > humidity_max:
        return recommendations.humidity_out_of_range(ambient.humidity, low=False)
    return None


def combined_blink_light(blink, exposure, ambient, thresholds):
    """Poco parpadeo + luz inadecuada: aviso mas especifico que uno solo (HU-13)."""
    if blink is None or not _reliable(blink, thresholds):
        return None
    warmup = thresholds["blink_warmup_seconds"]
    elapsed = getattr(blink, "elapsed_seconds", 0.0)
    if 0 < elapsed < warmup:
        return None
    if not _ambient_data(ambient):
        return None
    if blink.blink_rate >= thresholds["blink_rate_low"]:
        return None
    lux_min = thresholds["lux_min"]
    lux_max = thresholds["lux_max"]
    if ambient.lux < lux_min:
        return recommendations.combined_low_blink_bad_light(blink.blink_rate, ambient.lux, low=True)
    if ambient.lux > lux_max:
        return recommendations.combined_low_blink_bad_light(blink.blink_rate, ambient.lux, low=False)
    return None
