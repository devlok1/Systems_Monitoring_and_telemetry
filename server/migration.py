import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Tuple

from server.database import get_db, init_db, get_db_path

def migrate_legacy_db(
    old_db_path: Path = Path(__file__).resolve().parent.parent / "telemetry_old.db",
    target_db_path: Path = None,
) -> Tuple[int, int]:
    """
    Migrate records from legacy telemetry_old.db into canonical telemetry.db.
    Returns (migrated_count, skipped_count).
    """
    if target_db_path is None:
        target_db_path = get_db_path()

    init_db(target_db_path)

    if not old_db_path.exists():
        print(f"Old database {old_db_path} does not exist. Skipping migration.")
        return 0, 0

    old_conn = sqlite3.connect(str(old_db_path))
    old_conn.row_factory = sqlite3.Row
    old_cursor = old_conn.cursor()

    try:
        old_cursor.execute("SELECT * FROM telemetry")
        rows = old_cursor.fetchall()
    except sqlite3.OperationalError as e:
        print(f"Error querying legacy database: {e}")
        old_conn.close()
        return 0, 0

    migrated = 0
    skipped = 0

    with get_db(target_db_path) as conn:
        cursor = conn.cursor()

        for row in rows:
            ts = float(row["timestamp"])
            hostname = row["hostname"] or "legacy-host"

            # Check if record already exists
            cursor.execute(
                "SELECT id FROM telemetry WHERE hostname = ? AND abs(timestamp - ?) < 0.001",
                (hostname, ts),
            )
            if cursor.fetchone():
                skipped += 1
                continue

            iso_ts = datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
            cpu_pct = float(row["cpu_percent"]) if row["cpu_percent"] is not None else 0.0
            mem_pct = float(row["memory_percent"]) if row["memory_percent"] is not None else 0.0
            disk_pct = float(row["disk_percent"]) if row["disk_percent"] is not None else 0.0
            bytes_sent = int(row["bytes_sent"]) if row["bytes_sent"] is not None else 0
            bytes_recv = int(row["bytes_received"]) if row["bytes_received"] is not None else 0

            cpu_data = json.dumps({
                "percent": cpu_pct,
                "logical_cores": None,
                "physical_cores": None,
                "per_core": [],
                "frequency": None,
            })
            memory_data = json.dumps({
                "percent": mem_pct,
                "total": None,
                "used": None,
                "available": None,
                "swap": None,
            })
            disk_data = json.dumps({
                "percent": disk_pct,
                "total": None,
                "used": None,
                "free": None,
                "partitions": [],
            })
            network_data = json.dumps({
                "bytes_sent": bytes_sent,
                "bytes_received": bytes_recv,
                "interfaces": [],
            })
            processes_data = json.dumps([])

            cursor.execute("""
                INSERT INTO telemetry (
                    host_id, hostname, os, os_version, architecture, agent_version,
                    timestamp, timestamp_utc, uptime,
                    cpu_percent, cpu_data,
                    memory_percent, memory_data,
                    disk_percent, disk_data,
                    network_bytes_sent, network_bytes_recv, network_data,
                    processes_data
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                "local", hostname, "Unknown", None, None, "legacy",
                ts, iso_ts, None,
                cpu_pct, cpu_data,
                mem_pct, memory_data,
                disk_pct, disk_data,
                bytes_sent, bytes_recv, network_data,
                processes_data
            ))
            migrated += 1

    old_conn.close()
    print(f"Migration complete: {migrated} records migrated, {skipped} records skipped.")
    return migrated, skipped


if __name__ == "__main__":
    migrate_legacy_db()
