"""Conexión SQLite y esquema del histórico de Blinky.

Qué guarda:
- Sesiones, muestras de parpadeo, exposición, ambiente y recomendaciones.
- Dos vistas listas para estadísticas: v_daily_blinks y v_daily_ambient.

La base vive por defecto en app/blinky.db. Se puede cambiar con
`storage.path` en settings.yaml.
"""

import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path

SCHEMA_VERSION = 2
DEFAULT_DB_NAME = "blinky.db"

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS schema_meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TEXT NOT NULL,
    ended_at TEXT,
    source TEXT NOT NULL DEFAULT 'unknown'
);

CREATE TABLE IF NOT EXISTS blink_samples (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER,
    ts TEXT NOT NULL,
    blinks INTEGER NOT NULL,
    blink_rate REAL NOT NULL,
    eyes_closed INTEGER NOT NULL DEFAULT 0 CHECK (eyes_closed IN (0, 1)),
    ear REAL NOT NULL DEFAULT 0,
    mean_blink_duration_ms REAL NOT NULL DEFAULT 0,
    inter_blink_seconds REAL NOT NULL DEFAULT 0,
    perclos REAL NOT NULL DEFAULT 0,
    long_closures INTEGER NOT NULL DEFAULT 0,
    confidence REAL NOT NULL DEFAULT 1,
    source TEXT NOT NULL DEFAULT '',
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS ambient_samples (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER,
    ts TEXT NOT NULL,
    lux REAL NOT NULL,
    temperature_c REAL NOT NULL,
    humidity REAL NOT NULL,
    connected INTEGER NOT NULL DEFAULT 1 CHECK (connected IN (0, 1)),
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS exposure_samples (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER,
    ts TEXT NOT NULL,
    session_seconds INTEGER NOT NULL,
    continuous_seconds INTEGER NOT NULL,
    breaks_taken INTEGER NOT NULL,
    break_due INTEGER NOT NULL DEFAULT 0 CHECK (break_due IN (0, 1)),
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS recommendations (
    id TEXT NOT NULL,
    session_id INTEGER,
    created_at TEXT NOT NULL,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    severity TEXT NOT NULL,
    active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0, 1)),
    PRIMARY KEY (id, created_at),
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_blink_ts ON blink_samples(ts);
CREATE INDEX IF NOT EXISTS idx_ambient_ts ON ambient_samples(ts);
CREATE INDEX IF NOT EXISTS idx_exposure_ts ON exposure_samples(ts);
CREATE INDEX IF NOT EXISTS idx_recommendations_created ON recommendations(created_at);
"""

# Las vistas se recrean en cada arranque para que una actualización del esquema
# no deje columnas nuevas fuera de las estadísticas.
VIEWS_SQL = """
DROP VIEW IF EXISTS v_daily_blinks;
DROP VIEW IF EXISTS v_daily_ambient;

CREATE VIEW v_daily_blinks AS
SELECT
    date(ts) AS day,
    COUNT(*) AS samples,
    ROUND(AVG(blink_rate), 1) AS avg_blink_rate,
    MIN(blink_rate) AS min_blink_rate,
    MAX(blink_rate) AS max_blink_rate,
    MAX(blinks) AS max_blinks,
    ROUND(AVG(mean_blink_duration_ms), 0) AS avg_blink_duration_ms,
    ROUND(AVG(perclos), 3) AS avg_perclos,
    MAX(long_closures) AS max_long_closures
FROM blink_samples
GROUP BY date(ts);

CREATE VIEW v_daily_ambient AS
SELECT
    date(ts) AS day,
    COUNT(*) AS samples,
    ROUND(AVG(lux), 0) AS avg_lux,
    MIN(lux) AS min_lux,
    MAX(lux) AS max_lux,
    ROUND(AVG(temperature_c), 1) AS avg_temperature_c,
    ROUND(AVG(humidity), 0) AS avg_humidity
FROM ambient_samples
GROUP BY date(ts);
"""

BLINK_COLUMN_MIGRATIONS = {
    "mean_blink_duration_ms": "REAL NOT NULL DEFAULT 0",
    "inter_blink_seconds": "REAL NOT NULL DEFAULT 0",
    "perclos": "REAL NOT NULL DEFAULT 0",
    "long_closures": "INTEGER NOT NULL DEFAULT 0",
    "confidence": "REAL NOT NULL DEFAULT 1",
    "source": "TEXT NOT NULL DEFAULT ''",
}


def default_database_path():
    """app/blinky.db, sin crear carpetas nuevas en la raíz del repo."""
    return Path(__file__).resolve().parents[3] / DEFAULT_DB_NAME


class Database:
    def __init__(self, path=None):
        self.path = Path(path) if path else default_database_path()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._connection = sqlite3.connect(str(self.path), check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA foreign_keys = ON")
        self._connection.execute("PRAGMA journal_mode = WAL")
        self._initialize()

    def _initialize(self):
        with self._lock:
            self._connection.executescript(SCHEMA_SQL)
            self._migrate()
            self._connection.executescript(VIEWS_SQL)
            self._connection.execute(
                """
                INSERT INTO schema_meta (key, value) VALUES ('version', ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
                """,
                (str(SCHEMA_VERSION),),
            )
            self._connection.commit()

    def _migrate(self):
        columns = {
            row[1]
            for row in self._connection.execute("PRAGMA table_info(blink_samples)")
        }
        for name, definition in BLINK_COLUMN_MIGRATIONS.items():
            if name not in columns:
                self._connection.execute(
                    f"ALTER TABLE blink_samples ADD COLUMN {name} {definition}"
                )

    @contextmanager
    def transaction(self):
        with self._lock:
            try:
                yield self._connection
                self._connection.commit()
            except Exception:
                self._connection.rollback()
                raise

    def execute(self, sql, params=()):
        with self.transaction() as connection:
            cursor = connection.execute(sql, params)
            return cursor.lastrowid

    def executemany(self, sql, rows):
        with self.transaction() as connection:
            cursor = connection.executemany(sql, rows)
            return cursor.rowcount

    def query(self, sql, params=()):
        with self._lock:
            cursor = self._connection.execute(sql, params)
            return [dict(row) for row in cursor.fetchall()]

    def query_one(self, sql, params=()):
        with self._lock:
            row = self._connection.execute(sql, params).fetchone()
            return dict(row) if row is not None else None

    def scalar(self, sql, params=()):
        with self._lock:
            row = self._connection.execute(sql, params).fetchone()
            return row[0] if row is not None else None

    def close(self):
        with self._lock:
            if self._connection is not None:
                self._connection.close()
                self._connection = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        self.close()
