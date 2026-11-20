import time
from datetime import datetime, timezone
from typing import Dict, Any

from agent.platform import detect_platform_info
from agent.collectors import (
    collect_cpu,
    collect_memory,
    collect_disk,
    collect_network,
    collect_processes,
)
from agent.config import config

def collect_system_telemetry() -> Dict[str, Any]:
    """
    Collect a complete cross-platform telemetry snapshot.
    Conforms strictly to the canonical SYSWATCH telemetry schema.
    """
    now = datetime.now(timezone.utc)
    epoch_ts = time.time()
    iso_ts = now.isoformat()

    host_info = detect_platform_info()
    host_info["agent_version"] = config.agent_version

    cpu_info = collect_cpu()
    mem_info = collect_memory()
    disk_info = collect_disk()
    net_info = collect_network()
    proc_info = collect_processes(limit=config.top_processes_count)

    # Backward compatible "system" block
    system_compat = {
        "hostname": host_info["hostname"],
        "os": host_info["os"],
        "uptime": host_info["uptime_seconds"],
        "version": host_info["os_version"],
    }

    return {
        "timestamp": iso_ts,
        "timestamp_epoch": epoch_ts,
        "host": host_info,
        "system": system_compat,
        "cpu": cpu_info,
        "memory": mem_info,
        "disk": disk_info,
        "network": net_info,
        "processes": proc_info,
    }

