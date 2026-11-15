"""Modelos de datos compartidos por todo el sistema.

Qué va aquí:
- Contratos que cruzan módulos: visión -> decisión -> UI.
- Dataclasses inmutables para evitar acoplamientos y facilitar pruebas.

Flujo:
    Camera -> vision.blink_metrics -> BlinkMetrics -> decision.engine
    ESP32 -> MQTT -> ambient.mqtt_client -> AmbientReading -> decision.engine
    decision.engine -> Recommendation -> ui.state -> las 3 interfaces
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class BlinkMetrics:
    """Resultado del análisis de parpadeo de una ventana de tiempo.

    `blinks` es el acumulado de la sesión; el resto describe la ventana móvil.
    Los campos nuevos tienen valores por defecto para no romper a los
    consumidores que solo conocen los cuatro originales.
    """

    timestamp: datetime
    blinks: int
    blink_rate: float
    eyes_closed: bool = False
    ear: float = 0.0
    confidence: float = 1.0
    mean_blink_duration_ms: float = 0.0
    last_blink_duration_ms: float = 0.0
    inter_blink_seconds: float = 0.0
    perclos: float = 0.0
    long_closures: int = 0
    elapsed_seconds: float = 0.0
    calibration_progress: float = 1.0
    source: str = ""


@dataclass(frozen=True)
class ExposureMetrics:
    """Tiempo frente a la pantalla y pausas recomendadas."""

    timestamp: datetime
    session_seconds: int
    continuous_seconds: int
    breaks_taken: int
    break_due: bool = False


@dataclass(frozen=True)
class AmbientReading:
    """Lectura validada del ESP32 recibida por MQTT."""

    timestamp: datetime
    lux: float
    temperature_c: float
    humidity: float
    connected: bool = True


@dataclass(frozen=True)
class Recommendation:
    """Alerta o recomendación generada por el motor de reglas."""

    id: str
    title: str
    message: str
    severity: str
    action: str = "Ver recomendaciones"
    created_at: datetime = field(default_factory=datetime.now)
    active: bool = True


@dataclass(frozen=True)
class VisionFrame:
    """Fotograma + landmarks listos para el detector de parpadeo.

    `blink_score` viene de las blendshapes de MediaPipe (eyeBlinkLeft/Right)
    y se usa como señal auxiliar del EAR. Puede ser None si el backend no las
    produce.
    """

    timestamp: datetime
    image: Any
    landmarks: Any = None
    blink_score: float | None = None
    confidence: float = 1.0


@dataclass(frozen=True)
class BlinkEvent:
    """Evento puntual de parpadeo o cierre prolongado."""

    timestamp: datetime
    kind: str
    ear: float
    duration_ms: float = 0.0
    confidence: float = 1.0


@dataclass(frozen=True)
class VisionStatus:
    """Estado del detector de visión para mostrarlo en la UI."""

    timestamp: datetime
    backend: str
    available: bool
    face_found: bool
    calibrating: bool = False
    calibration_progress: float = 1.0
    threshold: float = 0.21
    message: str = ""
