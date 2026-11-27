"""Repositorio: guarda muestras y consulta series para la UI e informes.

La UI no habla SQL: llama a estos métodos. Todas las escrituras están
protegidas por Database, así que MQTT y el pipeline pueden guardar a la vez.
"""

from datetime import datetime, timedelta

from fatiga_visual.storage.database import Database


def _iso(value):
    if isinstance(value, datetime):
        return value.isoformat(timespec="seconds")
    if value is None:
        return datetime.now().isoformat(timespec="seconds")
    return str(value)


_SESSION_AGGREGATES = """
    (SELECT COUNT(*) FROM blink_samples b WHERE b.session_id = s.id)
        AS blink_samples,
    (SELECT MAX(b.blinks) FROM blink_samples b WHERE b.session_id = s.id)
        AS blinks,
    (SELECT ROUND(AVG(b.blink_rate), 1) FROM blink_samples b
        WHERE b.session_id = s.id) AS avg_blink_rate,
    (SELECT ROUND(AVG(b.mean_blink_duration_ms), 0) FROM blink_samples b
        WHERE b.session_id = s.id) AS avg_blink_duration_ms,
    (SELECT ROUND(AVG(b.perclos), 3) FROM blink_samples b
        WHERE b.session_id = s.id) AS avg_perclos,
    (SELECT MAX(b.long_closures) FROM blink_samples b
        WHERE b.session_id = s.id) AS long_closures,
    (SELECT MAX(e.session_seconds) FROM exposure_samples e
        WHERE e.session_id = s.id) AS exposure_seconds,
    (SELECT MAX(e.continuous_seconds) FROM exposure_samples e
        WHERE e.session_id = s.id) AS max_continuous_seconds,
    (SELECT MAX(e.breaks_taken) FROM exposure_samples e
        WHERE e.session_id = s.id) AS breaks_taken
"""


class Repository:
    def __init__(self, database=None, path=None):
        self.db = database if database is not None else Database(path)
        self._session_id = None

    @property
    def session_id(self):
        return self._session_id

    def start_session(self, source="runtime"):
        self._session_id = self.db.execute(
            "INSERT INTO sessions (started_at, source) VALUES (?, ?)",
            (_iso(datetime.now()), str(source)),
        )
        return self._session_id

    def end_session(self, session_id=None):
        target = session_id if session_id is not None else self._session_id
        if target is None:
            return
        self.db.execute(
            "UPDATE sessions SET ended_at = ? WHERE id = ? AND ended_at IS NULL",
            (_iso(datetime.now()), target),
        )
        if target == self._session_id:
            self._session_id = None

    def _sid(self, session_id=None):
        return session_id if session_id is not None else self._session_id

    def record_blink(self, metrics, session_id=None):
        if metrics is None:
            return None
        return self.db.execute(
            """
            INSERT INTO blink_samples
                (session_id, ts, blinks, blink_rate, eyes_closed, ear,
                 mean_blink_duration_ms, inter_blink_seconds, perclos,
                 long_closures, confidence, source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                self._sid(session_id),
                _iso(metrics.timestamp),
                int(metrics.blinks),
                float(metrics.blink_rate),
                1 if metrics.eyes_closed else 0,
                float(metrics.ear),
                float(getattr(metrics, "mean_blink_duration_ms", 0.0)),
                float(getattr(metrics, "inter_blink_seconds", 0.0)),
                float(getattr(metrics, "perclos", 0.0)),
                int(getattr(metrics, "long_closures", 0)),
                float(getattr(metrics, "confidence", 1.0)),
                str(getattr(metrics, "source", "")),
            ),
        )

    def record_ambient(self, reading, session_id=None):
        if reading is None:
            return None
        return self.db.execute(
            """
            INSERT INTO ambient_samples
                (session_id, ts, lux, temperature_c, humidity, connected)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                self._sid(session_id),
                _iso(reading.timestamp),
                float(reading.lux),
                float(reading.temperature_c),
                float(reading.humidity),
                1 if reading.connected else 0,
            ),
        )

    def record_exposure(self, metrics, session_id=None):
        if metrics is None:
            return None
        return self.db.execute(
            """
            INSERT INTO exposure_samples
                (session_id, ts, session_seconds, continuous_seconds, breaks_taken, break_due)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                self._sid(session_id),
                _iso(metrics.timestamp),
                int(metrics.session_seconds),
                int(metrics.continuous_seconds),
                int(metrics.breaks_taken),
                1 if metrics.break_due else 0,
            ),
        )

    def record_recommendation(self, recommendation, session_id=None):
        if recommendation is None:
            return None
        return self.db.execute(
            """
            INSERT OR IGNORE INTO recommendations
                (id, session_id, created_at, title, message, severity, active)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                recommendation.id,
                self._sid(session_id),
                _iso(recommendation.created_at),
                recommendation.title,
                recommendation.message,
                recommendation.severity,
                1 if recommendation.active else 0,
            ),
        )

    def blink_series(self, session_id=None, limit=1000):
        target = self._sid(session_id)
        rows = self.db.query(
            """
            SELECT id, session_id, ts, blinks, blink_rate, eyes_closed, ear,
                   mean_blink_duration_ms, inter_blink_seconds, perclos,
                   long_closures, confidence, source
            FROM blink_samples
            WHERE (? IS NULL OR session_id = ?)
            ORDER BY ts DESC
            LIMIT ?
            """,
            (target, target, int(limit)),
        )
        return list(reversed(rows))

    def ambient_series(self, session_id=None, limit=1000):
        target = self._sid(session_id)
        rows = self.db.query(
            """
            SELECT id, session_id, ts, lux, temperature_c, humidity, connected
            FROM ambient_samples
            WHERE (? IS NULL OR session_id = ?)
            ORDER BY ts DESC
            LIMIT ?
            """,
            (target, target, int(limit)),
        )
        return list(reversed(rows))

    def exposure_series(self, session_id=None, limit=1000):
        target = self._sid(session_id)
        rows = self.db.query(
            """
            SELECT id, session_id, ts, session_seconds, continuous_seconds,
                   breaks_taken, break_due
            FROM exposure_samples
            WHERE (? IS NULL OR session_id = ?)
            ORDER BY ts DESC
            LIMIT ?
            """,
            (target, target, int(limit)),
        )
        return list(reversed(rows))

    def daily_blinks(self, days=7):
        rows = self.db.query(
            "SELECT * FROM v_daily_blinks ORDER BY day DESC LIMIT ?",
            (int(days),),
        )
        return list(reversed(rows))

    def daily_ambient(self, days=7):
        rows = self.db.query(
            "SELECT * FROM v_daily_ambient ORDER BY day DESC LIMIT ?",
            (int(days),),
        )
        return list(reversed(rows))

    def session_summary(self, session_id=None):
        target = self._sid(session_id)
        if target is None:
            return None
        return self.db.query_one(
            f"""
            SELECT
                s.id,
                s.started_at,
                s.ended_at,
                s.source,
                {_SESSION_AGGREGATES}
            FROM sessions s
            WHERE s.id = ?
            """,
            (target,),
        )

    def session_history(self, limit=20):
        rows = self.db.query(
            f"""
            SELECT
                s.id,
                s.started_at,
                s.ended_at,
                s.source,
                {_SESSION_AGGREGATES},
                (SELECT COUNT(*) FROM recommendations r
                    WHERE r.session_id = s.id) AS alerts
            FROM sessions s
            ORDER BY s.started_at DESC, s.id DESC
            LIMIT ?
            """,
            (int(limit),),
        )
        for row in rows:
            row["current"] = row["id"] == self._session_id
        return rows

    def session_alert_count(self, session_id=None):
        target = self._sid(session_id)
        if target is None:
            return 0
        return (
            self.db.scalar(
                "SELECT COUNT(*) FROM recommendations WHERE session_id = ?", (target,)
            )
            or 0
        )

    def latest_recommendations(self, limit=20):
        return self.db.query(
            """
            SELECT id, session_id, created_at, title, message, severity, active
            FROM recommendations
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (int(limit),),
        )

    def purge_older_than(self, days=90):
        cutoff = (datetime.now() - timedelta(days=int(days))).isoformat(timespec="seconds")
        with self.db.transaction() as connection:
            deleted = 0
            for table in (
                "blink_samples",
                "ambient_samples",
                "exposure_samples",
                "recommendations",
            ):
                column = "created_at" if table == "recommendations" else "ts"
                deleted += connection.execute(
                    f"DELETE FROM {table} WHERE {column} < ?", (cutoff,)
                ).rowcount
        return deleted

    def close(self):
        self.db.close()
