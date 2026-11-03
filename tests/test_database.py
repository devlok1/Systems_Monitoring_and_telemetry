import sqlite3
import tempfile
import os
from pathlib import Path
from server.database import get_db, init_db, cleanup_old_records

def test_database_initialization():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = Path(tmp.name)

    try:
        init_db(db_path)
        with get_db(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = {row["name"] for row in cursor.fetchall()}
            assert "telemetry" in tables
            assert "logs" in tables
            assert "alerts" in tables

            # Verify indexes
            cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
            indexes = {row["name"] for row in cursor.fetchall()}
            assert "idx_telemetry_timestamp" in indexes
            assert "idx_telemetry_host_ts" in indexes
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)

def test_retention_cleanup():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = Path(tmp.name)

    try:
        init_db(db_path)
        with get_db(db_path) as conn:
            cursor = conn.cursor()
            # Insert 1 recent record (1 hour ago) and 1 old record (10 days ago)
            recent_ts = 1793700000.0
            old_ts = 1793700000.0 - (10 * 86400)
            cursor.execute("""
                INSERT INTO telemetry (hostname, os, timestamp, cpu_percent)
                VALUES ('host1', 'Linux', ?, 10.0)
            """, (recent_ts,))
            cursor.execute("""
                INSERT INTO telemetry (hostname, os, timestamp, cpu_percent)
                VALUES ('host1', 'Linux', ?, 20.0)
            """, (old_ts,))

        # Run retention with 7 days
        deleted = cleanup_old_records(retention_days=7, db_path=db_path)
        assert deleted == 1

        with get_db(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT count(*) FROM telemetry")
            remaining = cursor.fetchone()[0]
            assert remaining == 1
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)
