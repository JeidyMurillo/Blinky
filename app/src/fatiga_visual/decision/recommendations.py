"""Catálogo de textos y fábricas de recomendaciones.

Qué va aquí:
- Mensajes reutilizables (20-20-20, ventilar, ajustar luz).
- No evaluar umbrales aquí; eso pertenece a rules.py.
"""

from datetime import datetime

from fatiga_visual.core.models import Recommendation


def low_blink_rate(blink_rate):
    return Recommendation(
        id="blink-low",
        title="Tus ojos necesitan una pausa",
        message=(
            f"Tu frecuencia de parpadeo es de {blink_rate:.0f} por minuto. "
            "Una rutina breve puede ayudarte a relajar la vista."
        ),
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
            f"Llevas {minutes:.0f} minutos frente a la pantalla. Mira durante 20 segundos "
            "un objeto a 6 metros de distancia."
        ),
        severity="medium",
        action="Ver recomendaciones",
        created_at=datetime.now(),
    )


def lighting_out_of_range(lux, low=True):
    if low:
        title = "Aumenta la iluminacion"
        message = f"La luz actual es de {lux:.0f} lux. Evita trabajar con poca luz para reducir la fatiga."
    else:
        title = "Reduce el brillo del entorno"
        message = f"La luz actual es de {lux:.0f} lux. Puede producir deslumbramiento."
    return Recommendation(
        id="light-low" if low else "light-high",
        title=title,
        message=message,
        severity="medium",
        created_at=datetime.now(),
    )


def ventilate(temperature, humidity):
    return Recommendation(
        id="ventilate",
        title="Ventila el espacio",
        message=(
            f"Temperatura {temperature:.1f} C y humedad {humidity:.0f} %. "
            "Renueva el aire para mantener una atmosfera comoda."
        ),
        severity="low",
        created_at=datetime.now(),
    )
