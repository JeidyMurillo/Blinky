"""Reglas independientes del motor.

Qué va aquí:
- Cada regla es una función pura: entradas -> Recommendation | None.
- Los umbrales llegan desde settings.yaml, no se escriben aquí.

Para añadir una regla: función nueva + incluirla en engine.RULES.
"""

from fatiga_visual.decision import recommendations


def _reliable(blink, thresholds):
    return getattr(blink, "confidence", 1.0) >= thresholds.get("min_confidence", 0.35)


def _ambient_data(ambient):
    """Solo lecturas vigentes del nodo IoT; nunca valores viejos ni inventados."""
    return ambient is not None and getattr(ambient, "connected", True)


def low_blink_rate(blink, exposure, ambient, thresholds):
    if blink is None or not _reliable(blink, thresholds):
        return None
    warmup = thresholds.get("blink_warmup_seconds", 20)
    elapsed = getattr(blink, "elapsed_seconds", 0.0)
    # Durante el arranque hay pocos datos; 0 significa "sin información".
    if 0 < elapsed < warmup:
        return None
    limit = thresholds.get("blink_rate_low", 10)
    if blink.blink_rate < limit:
        return recommendations.low_blink_rate(blink.blink_rate)
    return None


def prolonged_eye_closure(blink, exposure, ambient, thresholds):
    if blink is None or not _reliable(blink, thresholds):
        return None
    perclos_limit = thresholds.get("perclos_high", 0.15)
    long_limit = thresholds.get("long_closures_per_minute", 3)
    if blink.perclos >= perclos_limit or blink.long_closures >= long_limit:
        return recommendations.prolonged_eye_closure(
            blink.perclos, blink.long_closures
        )
    return None


def continuous_exposure(blink, exposure, ambient, thresholds):
    if exposure is None:
        return None
    limit = thresholds.get("continuous_minutes", 20)
    if exposure.continuous_seconds >= limit * 60:
        return recommendations.long_exposure(exposure.continuous_seconds / 60)
    return None


def ambient_light(blink, exposure, ambient, thresholds):
    if not _ambient_data(ambient):
        return None
    lux_min = thresholds.get("lux_min", 300)
    lux_max = thresholds.get("lux_max", 1000)
    if ambient.lux < lux_min:
        return recommendations.lighting_out_of_range(ambient.lux, low=True)
    if ambient.lux > lux_max:
        return recommendations.lighting_out_of_range(ambient.lux, low=False)
    return None


def ambient_temperature(blink, exposure, ambient, thresholds):
    if not _ambient_data(ambient):
        return None
    temperature_min = thresholds.get("temperature_min", 18)
    temperature_max = thresholds.get("temperature_max", 26)
    if ambient.temperature_c < temperature_min:
        return recommendations.temperature_out_of_range(ambient.temperature_c, low=True)
    if ambient.temperature_c > temperature_max:
        return recommendations.temperature_out_of_range(ambient.temperature_c, low=False)
    return None


def ambient_humidity(blink, exposure, ambient, thresholds):
    if not _ambient_data(ambient):
        return None
    humidity_min = thresholds.get("humidity_min", 30)
    humidity_max = thresholds.get("humidity_max", 60)
    if ambient.humidity < humidity_min:
        return recommendations.humidity_out_of_range(ambient.humidity, low=True)
    if ambient.humidity > humidity_max:
        return recommendations.humidity_out_of_range(ambient.humidity, low=False)
    return None


def combined_blink_light(blink, exposure, ambient, thresholds):
    """Poco parpadeo + luz inadecuada: aviso mas especifico que uno solo (HU-13)."""
    if blink is None or not _reliable(blink, thresholds):
        return None
    warmup = thresholds.get("blink_warmup_seconds", 20)
    elapsed = getattr(blink, "elapsed_seconds", 0.0)
    if 0 < elapsed < warmup:
        return None
    if not _ambient_data(ambient):
        return None
    if blink.blink_rate >= thresholds.get("blink_rate_low", 10):
        return None
    lux_min = thresholds.get("lux_min", 300)
    lux_max = thresholds.get("lux_max", 1000)
    if ambient.lux < lux_min:
        return recommendations.combined_low_blink_bad_light(blink.blink_rate, ambient.lux, low=True)
    if ambient.lux > lux_max:
        return recommendations.combined_low_blink_bad_light(blink.blink_rate, ambient.lux, low=False)
    return None
