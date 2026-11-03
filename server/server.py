import sqlite3
import json


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
    #print("\n Received telemetry:")
    #print(data)

    
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO telemetry (
            hostname,
            os,
            timestamp,
            uptime,
            cpu_percent,
            cpu_data,
            memory_percent,
            memory_data,
            disk_percent,
            network_data,
            processes_data
        )
        VALUES (?,?,?,?,?,?,?,?,?,?,?)
    """, (
        data["system"]["hostname"],
        data["system"]["os"],
        data["timestamp"],
        data["system"]["uptime"],
        
        data["cpu"]["percent"],
        json.dumps(data["cpu"]),

        data["memory"]["percent"],
        json.dumps(data["memory"]),

        data["disk"]["percent"],
        json.dumps(data["disk"]),

        json.dumps(data["network"]),
        json.dumps(data["processes"])
    ))    

    connection.commit()
    connection.close()

    return{"status": "Telemetry received"}


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
            "id": row["id"],
            "hostname": row["hostname"],
            "os": row["os"],
            "timestamp": row["timestamp"],
            "uptime": row["uptime"],
            "cpu": json.loads(row["cpu_data"]),
            "memory": json.laods(row["memory_percent"]),
            "disk": json.loads(row["disk_data"]),
            "network": json.loads(row["network_data"]),
            "processes": json.loads(row["processes_data"])
        })

    return telemtry


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
        return {"message" : "No telemetry available"}

    return {
        "id": row["id"],
        "hostname": row["hostname"],
        "os": row["os"],
        "timestamp": row["timestamp"],
        "uptime": row["uptime"],
        "cpu": json.loads(row["cpu_data"]),
        "memory": json.laods(row["memory_percent"]),
        "disk": json.loads(row["disk_data"]),
        "network": json.loads(row["network_data"]),
        "processes": json.loads(row["processes_data"])
    }
