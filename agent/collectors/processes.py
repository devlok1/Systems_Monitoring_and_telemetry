import psutil
from typing import List, Dict, Any

def collect_processes(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Collect top processes by CPU and memory utilization.
    Gracefully handles Windows/Linux access denied, protected PIDs, and terminating processes.
    """
    processes: List[Dict[str, Any]] = []

    attrs = ["pid", "name", "cpu_percent", "memory_percent", "memory_info", "username", "status"]

    for proc in psutil.process_iter(attrs):
        try:
            info = proc.info
            mem_info = info.pop("memory_info", None)
            rss = int(mem_info.rss) if mem_info and hasattr(mem_info, "rss") else 0

            cpu_val = float(info.get("cpu_percent") or 0.0)
            mem_val = float(info.get("memory_percent") or 0.0)

            processes.append({
                "pid": int(info["pid"]),
                "name": str(info.get("name") or "unknown"),
                "cpu_percent": round(cpu_val, 2),
                "memory_percent": round(mem_val, 2),
                "memory_bytes": rss,
                "username": info.get("username"),
                "status": str(info.get("status") or "unknown"),
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
        except Exception:
            continue

    # Sort descending by CPU utilization, secondary sort by RAM
    processes.sort(key=lambda p: (p["cpu_percent"], p["memory_percent"]), reverse=True)
    return processes[:limit]
