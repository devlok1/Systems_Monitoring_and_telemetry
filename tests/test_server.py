import time
from datetime import datetime, timezone

def sample_payload(hostname="test-node", cpu_pct=42.0, ts=None):
    now_epoch = ts or time.time()
    now_iso = datetime.fromtimestamp(now_epoch, tz=timezone.utc).isoformat()
    return {
        "timestamp": now_iso,
        "timestamp_epoch": now_epoch,
        "host": {
            "hostname": hostname,
            "os": "Windows",
            "os_version": "Windows 11 (Build 22631)",
            "os_release": "11",
            "architecture": "AMD64",
            "boot_time": now_epoch - 3600,
            "uptime_seconds": 3600.0,
            "python_version": "3.14.7",
            "agent_version": "1.0.0",
        },
        "cpu": {
            "percent": cpu_pct,
            "per_core": [40.0, 44.0],
            "logical_cores": 2,
            "physical_cores": 2,
            "frequency": {"current": 3200.0, "min": 1600.0, "max": 4000.0},
            "temperature": None,
        },
        "memory": {
            "total": 16000000000,
            "used": 8000000000,
            "available": 8000000000,
            "percent": 50.0,
            "cached": 1000000,
            "buffers": 500000,
            "swap": {"total": 4000000000, "used": 500000000, "free": 3500000000, "percent": 12.5},
        },
        "disk": {
            "percent": 55.0,
            "total": 500000000000,
            "used": 275000000000,
            "free": 225000000000,
            "partitions": [
                {
                    "device": "C:\\",
                    "mountpoint": "C:\\",
                    "fstype": "NTFS",
                    "total": 500000000000,
                    "used": 275000000000,
                    "free": 225000000000,
                    "percent": 55.0,
                }
            ],
        },
        "network": {
            "bytes_sent": 1000000,
            "bytes_received": 5000000,
            "packets_sent": 1000,
            "packets_received": 2000,
            "interfaces": [
                {
                    "name": "Ethernet",
                    "is_up": True,
                    "mtu": 1500,
                    "addresses": ["192.168.1.50"],
                    "bytes_sent": 1000000,
                    "bytes_received": 5000000,
                    "speed_mbps": 1000,
                }
            ],
        },
        "processes": [
            {
                "pid": 1234,
                "name": "python.exe",
                "cpu_percent": 12.5,
                "memory_percent": 1.2,
                "memory_bytes": 104857600,
                "username": "user",
                "status": "running",
            }
        ],
    }

def test_root_and_health(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "SYSWATCH" in r.json()["message"]

    h = client.get("/health")
    assert h.status_code == 200
    data = h.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"
    assert "total_records" in data

def test_telemetry_post_and_latest(client):
    payload = sample_payload(hostname="test-node-1", cpu_pct=35.5)
    r = client.post("/telemetry", json=payload)
    assert r.status_code == 201
    assert r.json()["status"] == "Telemetry received"
    rec_id = r.json()["id"]
    assert rec_id > 0

    # Retrieve latest
    latest_r = client.get("/telemetry/latest?hostname=test-node-1")
    assert latest_r.status_code == 200
    latest = latest_r.json()
    assert latest["hostname"] == "test-node-1"
    assert latest["cpu_percent"] == 35.5
    assert latest["cpu"]["logical_cores"] == 2
    assert latest["memory"]["percent"] == 50.0
    assert len(latest["disk"]["partitions"]) == 1
    assert len(latest["processes"]) == 1

def test_telemetry_pagination(client):
    client.post("/telemetry", json=sample_payload(hostname="node-page", ts=100.0))
    client.post("/telemetry", json=sample_payload(hostname="node-page", ts=200.0))
    client.post("/telemetry", json=sample_payload(hostname="node-page", ts=300.0))

    r = client.get("/telemetry?hostname=node-page&limit=2&offset=0")
    assert r.status_code == 200
    items = r.json()
    assert len(items) == 2
    assert items[0]["timestamp"] > items[1]["timestamp"]  # Descending order

def test_telemetry_invalid_payload(client):
    bad_payload = {"invalid_key": "data"}
    r = client.post("/telemetry", json=bad_payload)
    assert r.status_code == 422  # Pydantic validation error

def test_logs_and_alerts_endpoints(client):
    log_res = client.post("/logs", json={"level": "WARN", "source": "test", "message": "warning test"})
    assert log_res.status_code == 201

    logs = client.get("/logs?level=WARN")
    assert logs.status_code == 200
    assert len(logs.json()) >= 1
    assert logs.json()[0]["level"] == "WARN"

    # Alerts
    al_res = client.get("/alerts")
    assert al_res.status_code == 200

