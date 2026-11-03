import time
import logging
from typing import Dict, Any, Optional
import requests

from agent.config import config
from agent.collector import collect_system_telemetry
from agent.collectors import (
    collect_cpu as _collect_cpu,
    collect_memory as _collect_memory,
    collect_disk as _collect_disk,
    collect_network as _collect_network,
    collect_processes as _collect_processes,
)
from agent.platform import detect_platform_info

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("syswatch.agent")

# Backwards compatible collection functions
def collect_system() -> Dict[str, Any]:
    info = detect_platform_info()
    return {
        "os": info["os"],
        "hostname": info["hostname"],
        "uptime": info["uptime_seconds"],
        "version": info["os_version"],
    }

def collect_cpu() -> Dict[str, Any]:
    return _collect_cpu()

def collect_memory() -> Dict[str, Any]:
    return _collect_memory()

def collect_disk() -> Dict[str, Any]:
    return _collect_disk()

def collect_network() -> Dict[str, Any]:
    return _collect_network()

def collect_processes() -> list:
    return _collect_processes(limit=config.top_processes_count)

def collect_metrics() -> Dict[str, Any]:
    """Canonical cross-platform metrics collector."""
    return collect_system_telemetry()

def display_metrics(metrics: Dict[str, Any]) -> None:
    """Formatted console output for manual agent inspection."""
    ts = metrics.get("timestamp") or metrics.get("timestamp_epoch")
    host = metrics.get("host", {})
    cpu = metrics.get("cpu", {})
    mem = metrics.get("memory", {})
    disk = metrics.get("disk", {})
    net = metrics.get("network", {})
    procs = metrics.get("processes", [])

    print(f"\n================ SYSWATCH TELEMETRY ({ts}) ================")
    print(f"Host:     {host.get('hostname')} | OS: {host.get('os')} ({host.get('os_version')})")
    uptime = host.get("uptime_seconds", 0)
    print(f"Uptime:   {int(uptime // 86400)}d {int((uptime % 86400) // 3600)}h {int((uptime % 3600) // 60)}m")
    print(f"CPU:      {cpu.get('percent')}% (Cores: {cpu.get('logical_cores')} logical, {cpu.get('physical_cores')} physical)")
    print(f"Memory:   {mem.get('percent')}% (Used: {mem.get('used', 0) // (1024**2)} MB / Total: {mem.get('total', 0) // (1024**2)} MB)")
    print(f"Disk:     {disk.get('percent')}% (Used: {disk.get('used', 0) // (1024**3)} GB / Total: {disk.get('total', 0) // (1024**3)} GB)")
    print(f"Network:  Sent: {net.get('bytes_sent', 0) // 1024} KB | Recv: {net.get('bytes_received', 0) // 1024} KB")

    print("\n--- Top Processes ---")
    for p in procs[:5]:
        print(f"  PID {p['pid']:>6} | {p['name']:<22} | CPU: {p['cpu_percent']:>5.1f}% | RAM: {p['memory_percent']:>5.1f}%")
    print("============================================================\n")

def send_telemetry(metrics: Dict[str, Any], endpoint_url: Optional[str] = None, timeout: Optional[float] = None) -> bool:
    """
    Transmit telemetry payload to FastAPI backend with configurable retries
    and exponential backoff.
    """
    url = endpoint_url or f"{config.backend_url}/telemetry"
    req_timeout = timeout or config.timeout

    for attempt in range(1, config.max_retries + 1):
        try:
            response = requests.post(url, json=metrics, timeout=req_timeout)
            if response.status_code in (200, 201):
                logger.info("Telemetry transmitted successfully to %s (status %d)", url, response.status_code)
                return True
            else:
                logger.warning(
                    "Backend returned non-success HTTP status %d: %s (attempt %d/%d)",
                    response.status_code, response.text, attempt, config.max_retries
                )
        except requests.exceptions.RequestException as exc:
            logger.warning(
                "Failed to send telemetry on attempt %d/%d: %s",
                attempt, config.max_retries, exc
            )

        if attempt < config.max_retries:
            backoff = config.retry_delay * (2 ** (attempt - 1))
            time.sleep(backoff)

    logger.error("Could not transmit telemetry after %d attempts.", config.max_retries)
    return False

def run_agent(interval: Optional[float] = None, max_iterations: Optional[int] = None) -> None:
    """
    Continuous agent loop collecting and transmitting system metrics.
    """
    poll_interval = interval or config.interval
    logger.info("Starting SYSWATCH Agent (interval: %.1fs, backend: %s)", poll_interval, config.backend_url)

    iterations = 0
    try:
        while True:
            metrics = collect_metrics()
            send_telemetry(metrics)
            iterations += 1
            if max_iterations is not None and iterations >= max_iterations:
                break
            time.sleep(poll_interval)
    except KeyboardInterrupt:
        logger.info("SYSWATCH Agent stopped by user.")

if __name__ == "__main__":
    run_agent()
