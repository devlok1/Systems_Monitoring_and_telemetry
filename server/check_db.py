import json
from server.database import get_db, init_db

def inspect_latest_telemetry():
    init_db()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM telemetry
            ORDER BY timestamp DESC
            LIMIT 1
        """)
        row = cursor.fetchone()

    if not row:
        print("No telemetry records found in database.")
        return

    print("=" * 60)
    print("LATEST SYSWATCH TELEMETRY RECORD")
    print("=" * 60)
    print(f"Record ID:   {row['id']}")
    print(f"Host ID:     {row['host_id'] if 'host_id' in row.keys() else 'local'}")
    print(f"Hostname:    {row['hostname']}")
    print(f"OS:          {row['os']} ({row['os_version'] if 'os_version' in row.keys() else 'N/A'})")
    print(f"Arch:        {row['architecture'] if 'architecture' in row.keys() else 'N/A'}")
    print(f"Timestamp:   {row['timestamp']} ({row['timestamp_utc'] if 'timestamp_utc' in row.keys() else 'N/A'})")
    print(f"Uptime:      {row['uptime']} seconds")
    print(f"CPU %:       {row['cpu_percent']}%")
    print(f"Memory %:    {row['memory_percent']}%")
    print(f"Disk %:      {row['disk_percent']}%")

    print("\n--- CPU Data ---")
    try:
        print(json.dumps(json.loads(row["cpu_data"]), indent=2))
    except Exception:
        print(row["cpu_data"])

    print("\n--- Memory Data ---")
    try:
        print(json.dumps(json.loads(row["memory_data"]), indent=2))
    except Exception:
        print(row["memory_data"])

    print("\n--- Disk Data ---")
    try:
        print(json.dumps(json.loads(row["disk_data"]), indent=2))
    except Exception:
        print(row["disk_data"])

    print("\n--- Network Data ---")
    try:
        print(json.dumps(json.loads(row["network_data"]), indent=2))
    except Exception:
        print(row["network_data"])

    print("\n--- Processes Data ---")
    try:
        print(json.dumps(json.loads(row["processes_data"]), indent=2))
    except Exception:
        print(row["processes_data"])
    print("=" * 60)

if __name__ == "__main__":
    inspect_latest_telemetry()
