"""Publicación validada de eventos de exposición en el EventBus."""

from datetime import datetime

METRICS_TOPIC = "exposure.metrics"
BREAK_TOPIC = "exposure.break"


def _iso(value):
    return value.isoformat() if isinstance(value, datetime) else value


def metrics_payload(metrics):
    return {
        "event": METRICS_TOPIC,
        "timestamp": _iso(metrics.timestamp),
        "session_seconds": metrics.session_seconds,
        "continuous_seconds": metrics.continuous_seconds,
        "breaks_taken": metrics.breaks_taken,
        "break_due": metrics.break_due,
        "user_present": getattr(metrics, "user_present", False),
    }


def break_payload(event):
    return {
        "event": BREAK_TOPIC,
        "timestamp": _iso(event.timestamp),
        "started_at": _iso(event.started_at),
        "kind": event.kind,
        "duration_seconds": event.duration_seconds,
        "continuous_before_seconds": event.continuous_before_seconds,
    }


def _is_datetime(value):
    if not isinstance(value, str):
        return False
    try:
        datetime.fromisoformat(value)
    except ValueError:
        return False
    return True


def _is_non_negative_number(value):
    return (
        not isinstance(value, bool)
        and isinstance(value, (int, float))
        and value >= 0
    )


def is_valid(payload):
    """Comprueba el payload contra contracts/exposure.schema.json."""
    if not isinstance(payload, dict):
        return False
    event = payload.get("event")
    if event == METRICS_TOPIC:
        expected = {
            "event",
            "timestamp",
            "session_seconds",
            "continuous_seconds",
            "breaks_taken",
            "break_due",
            "user_present",
        }
        if set(payload) != expected or not _is_datetime(payload["timestamp"]):
            return False
        for key in ("session_seconds", "continuous_seconds", "breaks_taken"):
            value = payload[key]
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                return False
        return all(isinstance(payload[key], bool) for key in ("break_due", "user_present"))
    if event == BREAK_TOPIC:
        expected = {
            "event",
            "timestamp",
            "started_at",
            "kind",
            "duration_seconds",
            "continuous_before_seconds",
        }
        if set(payload) != expected:
            return False
        if not _is_datetime(payload["timestamp"]) or not _is_datetime(payload["started_at"]):
            return False
        if payload["kind"] not in ("started", "finished"):
            return False
        return all(
            _is_non_negative_number(payload[key])
            for key in ("duration_seconds", "continuous_before_seconds")
        )
    return False


class ExposureBusPublisher:
    """Publica exposición solo si el payload cumple el contrato."""

    def __init__(self, bus, settings=None):
        self.bus = bus
        self.metrics_topic = (
            settings.get("bus.topics.exposure_metrics", METRICS_TOPIC)
            if settings is not None
            else METRICS_TOPIC
        )
        self.break_topic = (
            settings.get("bus.topics.exposure_break", BREAK_TOPIC)
            if settings is not None
            else BREAK_TOPIC
        )

    def publish_metrics(self, metrics):
        payload = metrics_payload(metrics)
        if not is_valid(payload):
            return False
        if self.bus is not None:
            self.bus.publish(self.metrics_topic, metrics)
        return True

    def publish_break(self, event):
        payload = break_payload(event)
        if not is_valid(payload):
            return False
        if self.bus is not None:
            self.bus.publish(self.break_topic, event)
        return True
