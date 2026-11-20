from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class CpuFrequency(BaseModel):
    current: Optional[float] = None
    min: Optional[float] = None
    max: Optional[float] = None

class CpuMetrics(BaseModel):
    percent: float
    per_core: List[float] = Field(default_factory=list)
    logical_cores: Optional[int] = None
    physical_cores: Optional[int] = None
    frequency: Optional[CpuFrequency] = None
    temperature: Optional[float] = None

class SwapMemory(BaseModel):
    total: int = 0
    used: int = 0
    free: int = 0
    percent: float = 0.0

class MemoryMetrics(BaseModel):
    total: int
    used: int
    available: int
    percent: float
    swap: Optional[SwapMemory] = None
    cached: Optional[int] = 0
    buffers: Optional[int] = 0

class DiskPartition(BaseModel):
    device: str
    mountpoint: str
    fstype: str = ""
    total: int = 0
    used: int = 0
    free: int = 0
    percent: float = 0.0

class DiskMetrics(BaseModel):
    percent: float
    total: int = 0
    used: int = 0
    free: int = 0
    partitions: List[DiskPartition] = Field(default_factory=list)

class NetworkInterface(BaseModel):
    name: str
    is_up: bool = False
    mtu: int = 0
    addresses: List[str] = Field(default_factory=list)
    bytes_sent: int = 0
    bytes_received: int = 0
    speed_mbps: Optional[int] = None

class NetworkMetrics(BaseModel):
    bytes_sent: int
    bytes_received: int
    packets_sent: Optional[int] = 0
    packets_received: Optional[int] = 0
    interfaces: List[NetworkInterface] = Field(default_factory=list)

class ProcessInfo(BaseModel):
    pid: int
    name: str
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    memory_bytes: int = 0
    username: Optional[str] = None
    status: Optional[str] = None

class HostInfo(BaseModel):
    hostname: str
    os: str
    os_version: Optional[str] = None
    os_release: Optional[str] = None
    architecture: Optional[str] = None
    boot_time: Optional[float] = None
    uptime_seconds: Optional[float] = None
    python_version: Optional[str] = None
    agent_version: str = "1.0.0"

class TelemetryPayload(BaseModel):
    timestamp: str  # ISO-8601 UTC string
    timestamp_epoch: float
    host: HostInfo
    cpu: CpuMetrics
    memory: MemoryMetrics
    disk: DiskMetrics
    network: NetworkMetrics
    processes: List[ProcessInfo] = Field(default_factory=list)
    # Compatibility alias for existing server code:
    system: Optional[Dict[str, Any]] = None

    def model_post_init(self, __context: Any) -> None:
        if self.system is None and self.host is not None:
            self.system = {
                "hostname": self.host.hostname,
                "os": self.host.os,
                "uptime": self.host.uptime_seconds,
                "version": self.host.os_version,
            }

