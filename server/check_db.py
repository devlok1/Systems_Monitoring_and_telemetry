import sqlite3
import json

connection = sqlite3.connect("telemetry.db")
connection.row_factory = sqlite3.Row

cursor = connection.cursor()

cursor.execute("""
SELECT *
FROM telemetry
ORDER BY timestamp DESC
LIMIT 1
""")

row = cursor.fetchone()

if row:
    print("hostname:", row["hostname"])
    print("os:", row["os"])
    print("timestamp:", row["timestamp"])
    print("uptime:", row["uptime"])

    print("\ncpu:")
    print(json.dumps(json.loads(row["cpu_data"]), indent=2))

    print("\nmemory:")
    print(json.dumps(json.loads(row["memory_data"]), indent=2))

    print("\ndisk:")
    print(json.dumps(json.loads(row["disk_data"]), indent=2))

    print("\nnetwork:")
    print(json.dumps(json.loads(row["network_data"]), indent=2))

    print("\nprocesses:")
    print(json.dumps(json.loads(row["processes_data"]), indent=2))

else:
    print("No telemetry available")

connection.close()
