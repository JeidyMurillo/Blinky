"""Suavizado de la señal EAR.

El EAR de MediaPipe tiembla incluso con el ojo quieto. Un filtro exponencial
(EMA) reduce ese ruido sin añadir la latencia de una ventana grande, algo
importante porque un parpadeo dura 100-400 ms.

`alpha` alto = menos suavizado (más reactivo). `alpha=1.0` desactiva el filtro.
"""


class ExponentialSmoother:
    def __init__(self, alpha=0.65):
        try:
            alpha = float(alpha)
        except (TypeError, ValueError):
            alpha = 0.65
        self.alpha = min(1.0, max(0.05, alpha))
        self._value = None

    @property
    def value(self):
        return self._value

    def update(self, value):
        if value is None:
            return self._value
        value = float(value)
        if self._value is None:
            self._value = value
        else:
            self._value = self.alpha * value + (1.0 - self.alpha) * self._value
        return self._value

    def reset(self):
        self._value = None
