import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional, Generator

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "telemetry.db"


def get_db_path() -> Path:
    """Return the configured or default database path."""
    env_path = os.environ.get("SYSWATCH_DB_PATH")
    if env_path:
        return Path(env_path).resolve()
    return DEFAULT_DB_PATH


def get_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """Open a SQLite connection configured with Row factory and WAL mode."""
    target_path = Path(db_path) if db_path else get_db_path()
    target_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(str(target_path), timeout=15.0)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA journal_mode = WAL;")
    connection.execute("PRAGMA synchronous = NORMAL;")
    connection.execute("PRAGMA foreign_keys = ON;")
    return connection


@contextmanager
def get_db(db_path: Optional[Path] = None) -> Generator[sqlite3.Connection, None, None]:
    """Context manager for managing SQLite connections and transactions."""
    conn = get_connection(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _ensure_columns(cursor: sqlite3.Cursor, table: str, required_cols: dict[str, str]) -> None:
    """Add any missing columns to existing SQLite table."""
    cursor.execute(f"PRAGMA table_info({table})")
    existing = {row["name"].lower() for row in cursor.fetchall()}
    for col_name, col_def in required_cols.items():
        if col_name.lower() not in existing:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_def}")


def init_db(db_path: Optional[Path] = None) -> None:
    """Initialize canonical tables, upgrade missing columns, and create indexes."""
    with get_db(db_path) as conn:
        cursor = conn.cursor()

        # Telemetry table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS telemetry (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            host_id TEXT DEFAULT 'local',
            hostname TEXT NOT NULL,
            os TEXT NOT NULL,
            os_version TEXT,
            architecture TEXT,
            agent_version TEXT,
            timestamp REAL NOT NULL,
            timestamp_utc TEXT,
            uptime REAL,

            cpu_percent REAL,
            cpu_data TEXT,

            memory_percent REAL,
            memory_data TEXT,

            disk_percent REAL,
            disk_data TEXT,

            network_bytes_sent INTEGER,
            network_bytes_recv INTEGER,
            network_data TEXT,

            processes_data TEXT
        )
        """)

        # Ensure all modern columns exist if table was created in an older schema
        _ensure_columns(cursor, "telemetry", {
            "host_id": "TEXT DEFAULT 'local'",
            "os_version": "TEXT",
            "architecture": "TEXT",
            "agent_version": "TEXT",
            "timestamp_utc": "TEXT",
            "network_bytes_sent": "INTEGER",
            "network_bytes_recv": "INTEGER"
        })

        # Logs table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp REAL NOT NULL,
            timestamp_utc TEXT,
            hostname TEXT,
            level TEXT NOT NULL,
            source TEXT,
            message TEXT NOT NULL
        )
        """)

        # Alerts table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp REAL NOT NULL,
            timestamp_utc TEXT,
            hostname TEXT,
            severity TEXT NOT NULL,
            source TEXT,
            detail TEXT,
            dismissed INTEGER DEFAULT 0
        )
        """)

        # Indexes for fast historical queries and time-range filtering
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_telemetry_timestamp
        ON telemetry(timestamp DESC)
        """)

        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_telemetry_host_ts
        ON telemetry(hostname, timestamp DESC)
        """)

        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_logs_timestamp
        ON logs(timestamp DESC)
        """)

        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_alerts_timestamp
        ON alerts(timestamp DESC)
        """)


def cleanup_old_records(retention_days: int = 7, db_path: Optional[Path] = None) -> int:
    """
    Delete telemetry records older than retention_days.
    Returns the number of deleted records.
    """
    cutoff_epoch = (datetime.now(timezone.utc) - timedelta(days=retention_days)).timestamp()
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM telemetry WHERE timestamp < ?", (cutoff_epoch,))
        deleted_count = cursor.rowcount
    return deleted_count
