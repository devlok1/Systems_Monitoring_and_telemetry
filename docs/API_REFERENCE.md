# SYSWATCH — REST API Reference Manual

**Base URL:** `http://127.0.0.1:8000`  
**Protocol:** HTTP/1.1  
**Content-Type:** `application/json`  

---

## 1. System Endpoints

### 1.1 Root Status
- **Endpoint:** `GET /`
- **Description:** Basic service availability probe.
- **Response `200 OK`:**
```json
{
  "message": "SYSWATCH telemetry server is running.",
  "status": "online",
  "version": "1.0.0"
}
```

### 1.2 Health Check
- **Endpoint:** `GET /health`
- **Description:** Deep health probe verifying database connectivity and record counts.
- **Response `200 OK`:**
```json
{
  "status": "healthy",
  "timestamp": "2026-11-03T14:30:00.000000Z",
  "database": "connected",
  "total_records": 1420,
  "version": "1.0.0"
}
```

---

## 2. Telemetry Ingestion & Retrieval

### 2.1 Ingest Telemetry
- **Endpoint:** `POST /telemetry`
- **Description:** Ingest a standardized telemetry snapshot from an agent.
- **Request Body:**
```json
{
  "timestamp": "2026-11-03T14:30:00.000000Z",
  "timestamp_epoch": 1793716200.0,
  "host": {
    "hostname": "Arx_369",
    "os": "Windows",
    "os_version": "Windows 11 (Build 22631)",
    "architecture": "AMD64",
    "boot_time": 1793694600.0,
    "uptime_seconds": 21600.0,
    "python_version": "3.14.7",
    "agent_version": "1.0.0"
  },
  "cpu": {
    "percent": 32.5,
    "per_core": [28.0, 37.0],
    "logical_cores": 24,
    "physical_cores": 16,
    "frequency": { "current": 3200.0, "min": 1600.0, "max": 4800.0 },
    "temperature": null
  },
  "memory": {
    "total": 16868679680,
    "used": 11808075776,
    "available": 5060603904,
    "percent": 70.0,
    "cached": 0,
    "buffers": 0,
    "swap": { "total": 4294967296, "used": 524288000, "free": 3770679296, "percent": 12.2 }
  },
  "disk": {
    "percent": 50.8,
    "total": 509251842048,
    "used": 258700935168,
    "free": 250550906880,
    "partitions": [
      {
        "device": "C:\\",
        "mountpoint": "C:\\",
        "fstype": "NTFS",
        "total": 509251842048,
        "used": 258700935168,
        "free": 250550906880,
        "percent": 50.8
      }
    ]
  },
  "network": {
    "bytes_sent": 63704064,
    "bytes_received": 592975872,
    "packets_sent": 52300,
    "packets_received": 89400,
    "interfaces": [
      {
        "name": "Wi-Fi",
        "is_up": true,
        "mtu": 1500,
        "addresses": ["192.168.1.150"],
        "bytes_sent": 63704064,
        "bytes_received": 592975872,
        "speed_mbps": 866
      }
    ]
  },
  "processes": [
    {
      "pid": 18804,
      "name": "brave.exe",
      "cpu_percent": 3.2,
      "memory_percent": 2.9,
      "memory_bytes": 489291776,
      "username": "user",
      "status": "running"
    }
  ]
}
```
- **Response `201 Created`:**
```json
{
  "status": "Telemetry received",
  "id": 1421
}
```

### 2.2 Latest Telemetry
- **Endpoint:** `GET /telemetry/latest`
- **Query Parameters:**
  - `hostname` (optional string): Filter for a specific machine.
- **Description:** Returns the most recent record with calculated upload/download rates.
- **Response `200 OK`:** Full `TelemetryRecord` with parsed metrics and:
```json
"throughput": {
  "rx_bytes_sec": 128400.0,
  "tx_bytes_sec": 32100.0,
  "rx_kb_sec": 125.39,
  "tx_kb_sec": 31.35,
  "rx_mb_sec": 0.122,
  "tx_mb_sec": 0.031
}
```

### 2.3 Paginated Telemetry List
- **Endpoint:** `GET /telemetry`
- **Query Parameters:**
  - `limit` (default: 20, max: 100)
  - `offset` (default: 0)
  - `hostname` (optional string)
- **Response `200 OK`:** Array of `TelemetryRecord` items sorted descending by timestamp.

---

## 3. Historical Telemetry & Analytics

### 3.1 Historical Trend Queries
- **Endpoint:** `GET /telemetry/history`
- **Query Parameters:**
  - `start` (optional float): Epoch timestamp seconds.
  - `end` (optional float): Epoch timestamp seconds.
  - `limit` (default: 100, max: 1000)
  - `offset` (default: 0)
  - `hostname` (optional string)
- **Response `200 OK`:**
```json
{
  "count": 45,
  "limit": 100,
  "offset": 0,
  "start": 1793710000.0,
  "end": 1793713600.0,
  "data": [ ... ]
}
```

### 3.2 Aggregate Statistics
- **Endpoint:** `GET /telemetry/stats`
- **Query Parameters:**
  - `start` (optional float)
  - `end` (optional float)
  - `hostname` (optional string)
- **Response `200 OK`:**
```json
{
  "hostname": null,
  "sample_count": 120,
  "period_start": 1793710000.0,
  "period_end": 1793713600.0,
  "period_duration_seconds": 3600.0,
  "cpu": { "avg": 34.2, "min": 12.1, "max": 88.5 },
  "memory": { "avg": 68.4, "min": 65.0, "max": 72.3 },
  "disk": { "avg": 50.8, "min": 50.8, "max": 50.9 },
  "network": {
    "total_bytes_sent": 142058000,
    "total_bytes_received": 958204000,
    "avg_upload_kb_sec": 38.56,
    "avg_download_kb_sec": 260.1
  }
}
```

---

## 4. Maintenance & Log Endpoints

### 4.1 Retention Cleanup
- **Endpoint:** `POST /maintenance/cleanup`
- **Query Parameters:**
  - `retention_days` (default: 7, minimum: 1)
- **Response `200 OK`:**
```json
{
  "status": "success",
  "retention_days": 7,
  "deleted_records": 48
}
```

### 4.2 Query Logs
- **Endpoint:** `GET /logs?level=WARN&limit=50`
- **Response `200 OK`:** Array of `LogEntry` objects.

### 4.3 Query Alerts
- **Endpoint:** `GET /alerts?active_only=true`
- **Response `200 OK`:** Array of active `AlertEntry` objects.

### 4.4 Dismiss Alert
- **Endpoint:** `POST /alerts/{alert_id}/dismiss`
- **Response `200 OK`:** `{"status": "dismissed", "id": 12}`
