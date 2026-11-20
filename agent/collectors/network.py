import socket
import psutil
from typing import Dict, Any, List

def collect_network() -> Dict[str, Any]:
    """
    Collect network cumulative I/O counters and individual interface statistics.
    Handles Windows and Linux interface configurations cleanly.
    """
    try:
        total_io = psutil.net_io_counters()
    except Exception:
        total_io = None

    try:
        if_stats = psutil.net_if_stats()
    except Exception:
        if_stats = {}

    try:
        if_addrs = psutil.net_if_addrs()
    except Exception:
        if_addrs = {}

    try:
        pernic_io = psutil.net_io_counters(pernic=True)
    except Exception:
        pernic_io = {}

    interfaces: List[Dict[str, Any]] = []

    for name, stats in if_stats.items():
        ips: List[str] = []
        for addr in if_addrs.get(name, []):
            if addr.family == socket.AF_INET:
                ips.append(addr.address)

        io = pernic_io.get(name)
        iface_sent = int(io.bytes_sent) if io else 0
        iface_recv = int(io.bytes_recv) if io else 0

        interfaces.append({
            "name": name,
            "is_up": bool(stats.isup),
            "mtu": int(stats.mtu) if stats.mtu else 0,
            "addresses": ips,
            "bytes_sent": iface_sent,
            "bytes_received": iface_recv,
            "speed_mbps": int(stats.speed) if stats.speed and stats.speed > 0 else None,
        })

    return {
        "bytes_sent": int(total_io.bytes_sent) if total_io else 0,
        "bytes_received": int(total_io.bytes_recv) if total_io else 0,
        "packets_sent": int(total_io.packets_sent) if total_io else 0,
        "packets_received": int(total_io.packets_recv) if total_io else 0,
        "interfaces": interfaces,
    }

