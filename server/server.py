import json
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware

from server.database import get_db, init_db, cleanup_old_records
from server.schemas.telemetry import (
    TelemetryPayload,
    TelemetryRecord,
    HealthResponse,
    HistoryResponse,
    StatsResponse,
    AggregatedMetric,
    LogEntry,
    AlertEntry,
)
from server.services.stats_service import calculate_network_throughputs

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("syswatch.server")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables and indexes on server startup
    logger.info("Initializing SYSWATCH database...")
    init_db()
    yield
    logger.info("Shutting down SYSWATCH server.")


app = FastAPI(
    title="SYSWATCH Telemetry API",
    description="Cross-Platform System Monitoring & Telemetry Engine (Windows & Linux)",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _safe_json_parse(raw_value: Any, default: Any) -> Any:
    """Safely decode JSON string or return default structure if invalid/empty."""
    if raw_value is None:
        return default
    if isinstance(raw_value, (dict, list)):
        return raw_value
    try:
        return json.loads(raw_value)
    except Exception:
        return default


def _row_to_record(row) -> Dict[str, Any]:
    """Transform an SQLite Row into a parsed telemetry dictionary."""
    return {
        "id": row["id"],
        "host_id": row["host_id"] if "host_id" in row.keys() else "local",
        "hostname": row["hostname"],
        "os": row["os"],
        "os_version": row["os_version"] if "os_version" in row.keys() else None,
        "architecture": row["architecture"] if "architecture" in row.keys() else None,
        "agent_version": row["agent_version"] if "agent_version" in row.keys() else None,
        "timestamp": float(row["timestamp"]),
        "timestamp_utc": row["timestamp_utc"] if "timestamp_utc" in row.keys() else None,
        "uptime": float(row["uptime"]) if row["uptime"] is not None else None,
        "cpu_percent": float(row["cpu_percent"]) if row["cpu_percent"] is not None else None,
        "memory_percent": float(row["memory_percent"]) if row["memory_percent"] is not None else None,
        "disk_percent": float(row["disk_percent"]) if row["disk_percent"] is not None else None,
        "network_bytes_sent": int(row["network_bytes_sent"]) if "network_bytes_sent" in row.keys() and row["network_bytes_sent"] is not None else None,
        "network_bytes_recv": int(row["network_bytes_recv"]) if "network_bytes_recv" in row.keys() and row["network_bytes_recv"] is not None else None,
        "cpu": _safe_json_parse(row["cpu_data"], {}),
        "memory": _safe_json_parse(row["memory_data"], {}),
        "disk": _safe_json_parse(row["disk_data"], {}),
        "network": _safe_json_parse(row["network_data"], {}),
        "processes": _safe_json_parse(row["processes_data"], []),
    }


@app.get("/", tags=["System"])
def root():
    return {
        "message": "SYSWATCH telemetry server is running.",
        "status": "online",
        "version": "1.0.0",
    }


@app.get("/health", response_model=HealthResponse, tags=["System"])
def get_health():
    now_iso = datetime.now(timezone.utc).isoformat()
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT count(*) FROM telemetry")
            count = cursor.fetchone()[0]
        return HealthResponse(
            status="healthy",
            timestamp=now_iso,
            database="connected",
            total_records=count,
            version="1.0.0",
        )
    except Exception as exc:
        logger.error("Health check database failure: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database check failed: {exc}",
        )


@app.post("/telemetry", status_code=status.HTTP_201_CREATED, tags=["Telemetry"])
def receive_telemetry(payload: TelemetryPayload):
    """
    Ingest standardized telemetry snapshot from Windows or Linux agent.
    """
    try:
        host = payload.host
        cpu = payload.cpu
        mem = payload.memory
        disk = payload.disk
        net = payload.network
        procs = payload.processes

        with get_db() as conn:
            cursor = conn.cursor()
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
                "local",
                host.hostname,
                host.os,
                host.os_version,
                host.architecture,
                host.agent_version,
                payload.timestamp_epoch,
                payload.timestamp,
                host.uptime_seconds,
                cpu.percent,
                json.dumps(cpu.model_dump()),
                mem.percent,
                json.dumps(mem.model_dump()),
                disk.percent,
                json.dumps(disk.model_dump()),
                net.bytes_sent,
                net.bytes_received,
                json.dumps(net.model_dump()),
                json.dumps([p.model_dump() for p in procs]),
            ))
            inserted_id = cursor.lastrowid

        return {"status": "Telemetry received", "id": inserted_id}
    except Exception as exc:
        logger.error("Failed to persist telemetry payload: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to persist telemetry: {exc}",
        )


@app.get("/telemetry/latest", response_model=TelemetryRecord, tags=["Telemetry"])
def get_latest_telemetry(hostname: Optional[str] = None):
    """
    Retrieve the single most recent telemetry snapshot.
    Calculates real-time network throughput against the preceding snapshot if available.
    """
    with get_db() as conn:
        cursor = conn.cursor()
        query = "SELECT * FROM telemetry "
        params: List[Any] = []
        if hostname:
            query += "WHERE hostname = ? "
            params.append(hostname)
        query += "ORDER BY timestamp DESC LIMIT 2"

        cursor.execute(query, params)
        rows = cursor.fetchall()

    if not rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No telemetry available",
        )

    # If we have 2 records, calculate throughput
    parsed_records = [_row_to_record(r) for r in reversed(rows)]
    enriched = calculate_network_throughputs(parsed_records)
    latest_enriched = enriched[-1]

    return latest_enriched


@app.get("/telemetry", response_model=List[TelemetryRecord], tags=["Telemetry"])
def get_telemetry_list(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    hostname: Optional[str] = None,
):
    """
    Paginated retrieval of recent telemetry records.
    """
    with get_db() as conn:
        cursor = conn.cursor()
        query = "SELECT * FROM telemetry "
        params: List[Any] = []
        if hostname:
            query += "WHERE hostname = ? "
            params.append(hostname)
        query += "ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor.execute(query, params)
        rows = cursor.fetchall()

    records = [_row_to_record(r) for r in rows]
    # Calculate throughputs in chronological order
    chrono = list(reversed(records))
    enriched = calculate_network_throughputs(chrono)
    return list(reversed(enriched))


@app.get("/telemetry/history", response_model=HistoryResponse, tags=["Telemetry"])
def get_telemetry_history(
    start: Optional[float] = Query(default=None, description="Start timestamp in epoch seconds"),
    end: Optional[float] = Query(default=None, description="End timestamp in epoch seconds"),
    hostname: Optional[str] = Query(default=None, description="Filter by hostname"),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
):
    """
    Historical time-range query for charts and trend analysis.
    Returns chronologically sorted records with computed network throughputs.
    """
    with get_db() as conn:
        cursor = conn.cursor()
        clauses = []
        params: List[Any] = []

        if hostname:
            clauses.append("hostname = ?")
            params.append(hostname)
        if start is not None:
            clauses.append("timestamp >= ?")
            params.append(start)
        if end is not None:
            clauses.append("timestamp <= ?")
            params.append(end)

        where_str = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        query = f"SELECT * FROM telemetry {where_str} ORDER BY timestamp ASC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor.execute(query, params)
        rows = cursor.fetchall()

    records = [_row_to_record(r) for r in rows]
    enriched = calculate_network_throughputs(records)

    return HistoryResponse(
        count=len(enriched),
        limit=limit,
        offset=offset,
        start=start,
        end=end,
        data=enriched,
    )


@app.get("/telemetry/stats", response_model=StatsResponse, tags=["Telemetry"])
def get_telemetry_stats(
    start: Optional[float] = Query(default=None, description="Start epoch seconds"),
    end: Optional[float] = Query(default=None, description="End epoch seconds"),
    hostname: Optional[str] = Query(default=None, description="Filter by hostname"),
):
    """
    Aggregate statistical evaluation (CPU avg/min/max, Memory avg/min/max,
    Disk avg/min/max, Network transfer volume) across requested time window.
    """
    with get_db() as conn:
        cursor = conn.cursor()
        clauses = []
        params: List[Any] = []

        if hostname:
            clauses.append("hostname = ?")
            params.append(hostname)
        if start is not None:
            clauses.append("timestamp >= ?")
            params.append(start)
        if end is not None:
            clauses.append("timestamp <= ?")
            params.append(end)

        where_str = f"WHERE {' AND '.join(clauses)}" if clauses else ""

        # Aggregate SQL query for numerical fields
        agg_sql = f"""
            SELECT
                count(*) as sample_count,
                min(timestamp) as min_ts,
                max(timestamp) as max_ts,
                avg(cpu_percent) as avg_cpu,
                min(cpu_percent) as min_cpu,
                max(cpu_percent) as max_cpu,
                avg(memory_percent) as avg_mem,
                min(memory_percent) as min_mem,
                max(memory_percent) as max_mem,
                avg(disk_percent) as avg_disk,
                min(disk_percent) as min_disk,
                max(disk_percent) as max_disk,
                min(network_bytes_sent) as min_sent,
                max(network_bytes_sent) as max_sent,
                min(network_bytes_recv) as min_recv,
                max(network_bytes_recv) as max_recv
            FROM telemetry
            {where_str}
        """
        cursor.execute(agg_sql, params)
        agg = cursor.fetchone()

    sample_count = agg["sample_count"] or 0
    if sample_count == 0:
        return StatsResponse(
            hostname=hostname,
            sample_count=0,
            period_start=start,
            period_end=end,
            period_duration_seconds=0.0,
            cpu=AggregatedMetric(),
            memory=AggregatedMetric(),
            disk=AggregatedMetric(),
            network={"total_bytes_sent": 0, "total_bytes_recv": 0},
        )

    min_ts = agg["min_ts"] or 0.0
    max_ts = agg["max_ts"] or 0.0
    duration = max_ts - min_ts

    total_sent = max(0, (agg["max_sent"] or 0) - (agg["min_sent"] or 0))
    total_recv = max(0, (agg["max_recv"] or 0) - (agg["min_recv"] or 0))

    return StatsResponse(
        hostname=hostname,
        sample_count=sample_count,
        period_start=min_ts,
        period_end=max_ts,
        period_duration_seconds=round(duration, 2),
        cpu=AggregatedMetric(
            avg=round(float(agg["avg_cpu"] or 0.0), 2),
            min=round(float(agg["min_cpu"] or 0.0), 2),
            max=round(float(agg["max_cpu"] or 0.0), 2),
        ),
        memory=AggregatedMetric(
            avg=round(float(agg["avg_mem"] or 0.0), 2),
            min=round(float(agg["min_mem"] or 0.0), 2),
            max=round(float(agg["max_mem"] or 0.0), 2),
        ),
        disk=AggregatedMetric(
            avg=round(float(agg["avg_disk"] or 0.0), 2),
            min=round(float(agg["min_disk"] or 0.0), 2),
            max=round(float(agg["max_disk"] or 0.0), 2),
        ),
        network={
            "total_bytes_sent": total_sent,
            "total_bytes_received": total_recv,
            "avg_upload_kb_sec": round((total_sent / duration / 1024.0), 2) if duration > 0 else 0.0,
            "avg_download_kb_sec": round((total_recv / duration / 1024.0), 2) if duration > 0 else 0.0,
        },
    )


@app.post("/maintenance/cleanup", tags=["Maintenance"])
def perform_cleanup(retention_days: int = Query(default=7, ge=1)):
    """
    Safely purge telemetry records older than retention threshold.
    """
    deleted = cleanup_old_records(retention_days=retention_days)
    return {
        "status": "success",
        "retention_days": retention_days,
        "deleted_records": deleted,
    }


# Logs & Alerts endpoints
@app.get("/logs", response_model=List[LogEntry], tags=["Logs"])
def get_logs(
    level: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = Query(default=50, ge=1, le=500),
):
    with get_db() as conn:
        cursor = conn.cursor()
        clauses = []
        params: List[Any] = []
        if level and level.upper() != "ALL":
            clauses.append("level = ?")
            params.append(level.upper())
        if search:
            clauses.append("(message LIKE ? OR source LIKE ?)")
            params.extend([f"%{search}%", f"%{search}%"])

        where_str = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        cursor.execute(f"SELECT * FROM logs {where_str} ORDER BY timestamp DESC LIMIT ?", (*params, limit))
        rows = cursor.fetchall()

    return [
        LogEntry(
            id=r["id"],
            timestamp=r["timestamp"],
            timestamp_utc=r["timestamp_utc"],
            hostname=r["hostname"],
            level=r["level"],
            source=r["source"],
            message=r["message"],
        )
        for r in rows
    ]


@app.post("/logs", status_code=status.HTTP_201_CREATED, tags=["Logs"])
def create_log(entry: Dict[str, Any]):
    now_ts = datetime.now(timezone.utc).timestamp()
    iso_ts = datetime.now(timezone.utc).isoformat()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO logs (timestamp, timestamp_utc, hostname, level, source, message)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            entry.get("timestamp", now_ts),
            entry.get("timestamp_utc", iso_ts),
            entry.get("hostname", "local"),
            entry.get("level", "INFO").upper(),
            entry.get("source", "system"),
            entry.get("message", ""),
        ))
        inserted_id = cursor.lastrowid
    return {"status": "created", "id": inserted_id}


@app.get("/alerts", response_model=List[AlertEntry], tags=["Alerts"])
def get_alerts(active_only: bool = True):
    with get_db() as conn:
        cursor = conn.cursor()
        where = "WHERE dismissed = 0" if active_only else ""
        cursor.execute(f"SELECT * FROM alerts {where} ORDER BY timestamp DESC")
        rows = cursor.fetchall()

    return [
        AlertEntry(
            id=r["id"],
            timestamp=r["timestamp"],
            timestamp_utc=r["timestamp_utc"],
            hostname=r["hostname"],
            severity=r["severity"],
            source=r["source"],
            detail=r["detail"],
            dismissed=r["dismissed"],
        )
        for r in rows
    ]


@app.post("/alerts/{alert_id}/dismiss", tags=["Alerts"])
def dismiss_alert(alert_id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE alerts SET dismissed = 1 WHERE id = ?", (alert_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Alert not found")
    return {"status": "dismissed", "id": alert_id}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server.server:app", host="0.0.0.0", port=8000, reload=True)
