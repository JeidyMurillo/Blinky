"""Carga de configuración desde app/config/settings.yaml.

Qué va aquí:
- Lectura y validación de umbrales, tópicos MQTT y cámara.
- Acceso por ruta con valores por defecto para no tocar código.

Ejemplo:
    settings = load_settings()
    settings.get("thresholds.blink_rate_low", 10)
"""

from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

try:
    from ruamel.yaml import YAML
except ImportError:
    YAML = None

DEFAULTS = {
    "camera": {"index": 0, "width": 1280, "height": 720, "fps": 30},
    "session": {
        "initial_seconds": 0,
        "initial_blinks": 0,
        "blink_rate": 0,
        "initial_continuous_seconds": 0,
        "initial_breaks": 0,
    },
    "vision": {
        "ear_threshold": 0.21,
        "reopen_margin": 0.02,
        "min_closed_frames": 2,
        "max_closed_frames": 15,
        "min_blink_duration_ms": 0.0,
        "max_blink_duration_ms": 800.0,
        "long_closure_seconds": 1.5,
        "blink_window_seconds": 60,
        "min_rate_window_seconds": 10.0,
        "calibration_seconds": 4.0,
        "calibration_min_samples": 24,
        "calibration_ratio": 0.60,
        "calibration_floor": 0.06,
        "calibration_ceiling": 0.28,
        "calibration_path": "",
        "auto_calibrate": True,
        "smoothing_alpha": 0.65,
        "processing_width": 640,
        "use_blendshapes": True,
        "blink_score_threshold": 0.65,
        "blink_cooldown_seconds": 0.06,
        "face_grace_seconds": 0.4,
        "min_confidence": 0.35,
        "model_path": "",
        "allow_model_download": True,
    },
    "exposure": {"absent_after_seconds": 20},
    "thresholds": {
        "blink_rate_low": 15,
        "blink_warmup_seconds": 20,
        "perclos_high": 0.15,
        "long_closures_per_minute": 3,
        "continuous_minutes": 20,
        "lux_min": 300,
        "lux_max": 1000,
        "temperature_min": 18,
        "temperature_max": 26,
        "humidity_min": 30,
        "humidity_max": 60,
    },
    "mqtt": {
        "enabled": True,
        "host": "127.0.0.1",
        "port": 1883,
        "keepalive": 30,
        "qos": 0,
        "topics": {
            "ambient": "fatiga/ambient",
            "status": "fatiga/ambient/status",
            "blink": "fatiga/blink",
        },
    },
    "ambient": {"stale_after_seconds": 15},
    "runtime": {
        "source": "real",
        "publish_seconds": 0.5,
        "frame_interval_ms": 40,
        "auto_start_camera": False,
        "simulated": {"blink_rate": 18.0, "ambient_seconds": 5.0, "jitter": 2.0},
    },
    "storage": {"enabled": True, "path": "", "retention_days": 90},
}


def settings_path():
    return Path(__file__).resolve().parents[3] / "config" / "settings.yaml"


class Settings:
    def __init__(self, values=None, path=None):
        self.path = Path(path) if path else settings_path()
        self._values = values if values is not None else {}

    def get(self, dotted_key, default=None):
        node = self._values
        for part in dotted_key.split("."):
            if not isinstance(node, dict) or part not in node:
                fallback = DEFAULTS
                for fallback_part in dotted_key.split("."):
                    if not isinstance(fallback, dict) or fallback_part not in fallback:
                        return default
                    fallback = fallback[fallback_part]
                return fallback
            node = node[part]
        return node

    def section(self, name):
        value = self._values.get(name, {})
        return dict(DEFAULTS.get(name, {}), **value) if isinstance(value, dict) else {}


def _parse_yaml(text):
    if yaml is not None:
        return yaml.safe_load(text) or {}
    if YAML is not None:
        return YAML(typ="safe").load(text) or {}
    return {}


def load_settings(path=None):
    target = Path(path) if path else settings_path()
    if not target.exists():
        return Settings({}, target)
    with target.open("r", encoding="utf-8") as file:
        values = _parse_yaml(file.read())
    return Settings(values, target)
