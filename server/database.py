import sqlite3

DATABASE = "telemetry.db"

def get_connection():
    connection = sqlite3.connect("telemetry.db")
    connection.row_factory = sqlite3.Row
    return connection

#print("Database connected")


connection = get_connection()


cursor = connection.cursor()


cursor.execute("""
CREATE TABLE IF NOT EXISTS telemetry (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hostname TEXT NOT NULL,
    os TEXT,
    timestamp REAL NOT NULL,
    uptime REAL,

    cpu_percent REAL,
    cpu_data TEXT,

    memory_percent REAL,
    memory_data TEXT,

    disk_percent REAL,
    disk_data TEXT,

    network_data TEXT,
    processes_data TEXT
)
""")


cursor.execute("""
CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp REAL NOT NULL,
    hostname TEXT,
    level TEXT NOT NULL,
    source TEXT,
    message TEXT NOT NULL
)
""")


cursor.execute("""
CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp REAL NOT NULL,
    hostname TEXT,
    severity TEXT NOT NULL,
    source TEXT,
    detail TEXT,
    dismissed INTEGER DEFAULT 0
)
""")


connection.commit()
connection.close()

print("Database initialized.")

