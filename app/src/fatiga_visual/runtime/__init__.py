"""Fuentes de datos que conectan cámara, sensores y motor de decisión.

- pipeline.py: fuente real (cámara + visión + motor).
- simulated.py: fuente demo (mismos eventos EventBus, sin hardware).
"""

from fatiga_visual.runtime.pipeline import RuntimePipeline
from fatiga_visual.runtime.simulated import SimulatedPipeline

__all__ = ["RuntimePipeline", "SimulatedPipeline"]
