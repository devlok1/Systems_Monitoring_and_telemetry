import sqlite3


def get_connection():
    return sqlite3.connect("telemetry.db")

print("Database connected")


connection = get_connection()


cursor = connection.cursor()


cursor.execute("""
CREATE TABLE IF NOT EXISTS telemetry (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hostname TEXT,
    timestamp REAL,
    cpu_percent REAL,
    memory_percent REAL,
    disk_percent REAL,
    bytes_sent INTEGER,
    bytes_received INTEGER
)
""")

connection.commit()
connection.close()

print("Telemetry table created.")

