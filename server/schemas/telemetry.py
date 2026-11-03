from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

# Re-export TelemetryPayload from canonical agent schema
from agent.telemetry_schema import TelemetryPayload, HostInfo, CpuMetrics, MemoryMetrics, DiskMetrics, NetworkMetrics, ProcessInfo

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    database: str
    total_records: int
    version: str = "1.0.0"

class ThroughputInfo(BaseModel):
    rx_bytes_sec: float = 0.0
    tx_bytes_sec: float = 0.0
    rx_kb_sec: float = 0.0
    tx_kb_sec: float = 0.0
    rx_mb_sec: float = 0.0
    tx_mb_sec: float = 0.0

class TelemetryRecord(BaseModel):
    id: int
    host_id: Optional[str] = "local"
    hostname: str
    os: str
    os_version: Optional[str] = None
    architecture: Optional[str] = None
    agent_version: Optional[str] = None
    timestamp: float
    timestamp_utc: Optional[str] = None
    uptime: Optional[float] = None
    cpu_percent: Optional[float] = None
    memory_percent: Optional[float] = None
    disk_percent: Optional[float] = None
    network_bytes_sent: Optional[int] = None
    network_bytes_recv: Optional[int] = None
    cpu: Dict[str, Any] = Field(default_factory=dict)
    memory: Dict[str, Any] = Field(default_factory=dict)
    disk: Dict[str, Any] = Field(default_factory=dict)
    network: Dict[str, Any] = Field(default_factory=dict)
    processes: List[Dict[str, Any]] = Field(default_factory=list)
    throughput: Optional[ThroughputInfo] = None

class HistoryResponse(BaseModel):
    count: int
    limit: int
    offset: int
    start: Optional[float] = None
    end: Optional[float] = None
    data: List[TelemetryRecord]

class AggregatedMetric(BaseModel):
    avg: float = 0.0
    min: float = 0.0
    max: float = 0.0

class StatsResponse(BaseModel):
    hostname: Optional[str] = None
    sample_count: int
    period_start: Optional[float] = None
    period_end: Optional[float] = None
    period_duration_seconds: float = 0.0
    cpu: AggregatedMetric
    memory: AggregatedMetric
    disk: AggregatedMetric
    network: Dict[str, Any]

class LogEntry(BaseModel):
    id: int
    timestamp: float
    timestamp_utc: Optional[str] = None
    hostname: Optional[str] = None
    level: str
    source: Optional[str] = None
    message: str

class AlertEntry(BaseModel):
    id: int
    timestamp: float
    timestamp_utc: Optional[str] = None
    hostname: Optional[str] = None
    severity: str
    source: Optional[str] = None
    detail: Optional[str] = None
    dismissed: int = 0
