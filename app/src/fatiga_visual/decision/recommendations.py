"""Catálogo de textos y fábricas de recomendaciones.

Qué va aquí:
- Mensajes reutilizables (20-20-20, ventilar, ajustar luz).
- No evaluar umbrales aquí; eso pertenece a rules.py.
"""

from datetime import datetime

from fatiga_visual.core.models import Recommendation


def low_blink_rate(blink_rate, threshold=None, sustained_seconds=None):
    message = (
        f"Tu frecuencia de parpadeo es de {blink_rate:.0f} por minuto. "
        "Una rutina breve puede ayudarte a relajar la vista."
    )
    if threshold is not None and sustained_seconds is not None:
        message = (
            f"Lleva {sustained_seconds:.0f} s con {blink_rate:.0f} parpadeos por minuto, "
            f"por debajo del umbral de {threshold:.0f}. "
            "Una rutina breve puede ayudarte a relajar la vista."
        )
    return Recommendation(
        id="blink-low",
        title="Tus ojos necesitan una pausa",
        message=message,
        severity="high",
        action="Ver recomendaciones",
        created_at=datetime.now(),
    )


def prolonged_eye_closure(perclos, long_closures):
    percent = max(0.0, perclos) * 100.0
    return Recommendation(
        id="eye-closure",
        title="Descansa la vista ahora",
        message=(
            f"Detectamos cierres oculares prolongados ({long_closures} en el ultimo minuto; "
            f"{percent:.0f}% del tiempo con los ojos cerrados). "
            "Mira un punto lejano durante 20 segundos y parpadea de forma consciente."
        ),
        severity="high",
        action="Ver recomendaciones",
        created_at=datetime.now(),
    )


def long_exposure(minutes):
    return Recommendation(
        id="break-20",
        title="Aplica la regla 20-20-20",
        message=(
            f"Llevas {minutes:.0f} minutos frente a la pantalla. Mira a 20 pies "
            "(6 m) durante 20 segundos para relajar la vista."
        ),
        severity="medium",
        action="Ver recomendaciones",
        created_at=datetime.now(),
    )


def lighting_out_of_range(lux, low=True):
    if low:
        title = "Aumenta la iluminacion"
        message = (
            f"Hay {lux:.0f} lux en tu espacio. Enciende una lampara o abre una cortina "
            "para trabajar con luz suficiente y reducir el esfuerzo visual."
        )
    else:
        title = "Reduce el brillo del entorno"
        message = (
            f"Hay {lux:.0f} lux en tu espacio. Cierra una cortina o baja el brillo "
            "de la pantalla para evitar deslumbramiento."
        )
    return Recommendation(
        id="light-low" if low else "light-high",
        title=title,
        message=message,
        severity="medium",
        created_at=datetime.now(),
    )


def temperature_out_of_range(temperature, low=True):
    if low:
        title = "Sube la temperatura del espacio"
        message = (
            f"La temperatura es de {temperature:.1f} C. Ajusta la calefaccion o abrigate "
            "para trabajar en un ambiente confortable."
        )
    else:
        title = "Baja la temperatura del espacio"
        message = (
            f"La temperatura es de {temperature:.1f} C. Ventila la habitacion o baja "
            "la calefaccion para evitar el aire calido."
        )
    return Recommendation(
        id="temperature-low" if low else "temperature-high",
        title=title,
        message=message,
        severity="low",
        created_at=datetime.now(),
    )


def humidity_out_of_range(humidity, low=True):
    if low:
        title = "El aire esta muy seco"
        message = (
            f"La humedad es de {humidity:.0f} %. Toma agua, ventila y aleja el flujo "
            "directo del aire acondicionado para no resecar tus ojos."
        )
    else:
        title = "El aire esta muy humedo"
        message = (
            f"La humedad es de {humidity:.0f} %. Ventila el espacio para mantener "
            "un ambiente comodo."
        )
    return Recommendation(
        id="humidity-low" if low else "humidity-high",
        title=title,
        message=message,
        severity="medium" if low else "low",
        created_at=datetime.now(),
    )


def combined_low_blink_bad_light(blink_rate, lux, low=True):
    """Recomendacion especifica cuando se combinan poco parpadeo y mala luz (HU-13)."""
    condition = "poca luz" if low else "exceso de luz"
    fix = "Enciende una lampara" if low else "Cierra una cortina o baja el brillo"
    return Recommendation(
        id="blink-light",
        title="Corrige la luz y descansa la vista",
        message=(
            f"Parpadeas {blink_rate:.0f} veces por minuto y hay {condition} ({lux:.0f} lux). "
            f"{fix}, y mira un punto lejano durante 20 segundos."
        ),
        severity="high",
        action="Ver recomendaciones",
        created_at=datetime.now(),
    )
