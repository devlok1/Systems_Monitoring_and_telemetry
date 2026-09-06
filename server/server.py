import sqlite3


from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from server.database import get_connection

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods= ["*"],
    allow_headers=["*"]
)


@app.get ("/")
def root():
    return {"message: System telemetry server is running."}

@app.post("/telemetry")
def receive_telemetry(data: dict):
    print("\n Received telemetry:")
    print(data)

    
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO telemetry (
            hostname,
            timestamp,
            cpu_percent,
            memory_percent,
            disk_percent,
            bytes_sent,
            bytes_received
        )
        VALUES (?,?,?,?,?,?,?)
    """, (
        data["system"]["hostname"],
        data["timestamp"],
        data["cpu"],
        data["memory"]["percent"],
        data["disk"]["percent"],
        data["network"]["bytes_sent"],
        data["network"]["bytes_received"]
    ))    

    connection.commit()
    connection.close()

    return{"status": "received"}


@app.get("/telemetry")
def get_telemetry():
    connection = get_connection()
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    

    cursor.execute("""
        SELECT * FROM telemetry 
        ORDER BY timestamp DESC
        LIMIT 20 
    """)

    rows = cursor.fetchall()

    connection.close()

    telemetry = []

    for row in rows:
        telemetry.append({
            "id":row["id"],
            "hostname":row["hostname"],
            "timestamp":row["timestamp"],
            "cpu_percent":row["cpu_percent"],
            "memory_percent":row["memory_percent"],
            "disk_percent":row["disk_percent"],
            "bytes_sent":row["bytes_sent"],
            "bytes_received":row["bytes_received"]
            })

    return telemetry


@app.get("/telemetry/latest")
def get_latest_telemtry():
    connection = get_connection()
    connection.row_factory = sqlite3.Row

    cursor = connection.cursor()

    cursor.execute("""
        SELECT * FROM telemetry
        ORDER BY timestamp DESC
        LIMIT 1
    """)

    row = cursor.fetchone()

    connection.close()

    if row is None:
        return {"message": "No telemetry available"}

    return {
        "id":row["id"],
        "hostname":row["hostname"],
        "timestamp":row["timestamp"],
        "cpu_percent":row["cpu_percent"],
        "memory_percent":row["memory_percent"],
        "disk_percent":row["disk_percent"],
        "bytes_sent":row["bytes_sent"],
        "bytes_received":row["bytes_received"]
    }
