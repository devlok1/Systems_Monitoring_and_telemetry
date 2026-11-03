import os
import psutil
from typing import Dict, Any, List

def collect_disk() -> Dict[str, Any]:
    """
    Collect cross-platform disk usage across logical drives (Windows)
    and mounted partitions (Linux). Handles inaccessible or removable drives gracefully.
    """
    partitions_data: List[Dict[str, Any]] = []
    total_bytes = 0
    used_bytes = 0
    free_bytes = 0

    seen_devices = set()

    try:
        partitions = psutil.disk_partitions(all=False)
    except Exception:
        partitions = []

    for part in partitions:
        mount = part.mountpoint
        device = part.device or mount

        # Avoid duplicate drive letters or loop mounts
        if device in seen_devices:
            continue

        try:
            usage = psutil.disk_usage(mount)
            part_info = {
                "device": device,
                "mountpoint": mount,
                "fstype": part.fstype,
                "total": int(usage.total),
                "used": int(usage.used),
                "free": int(usage.free),
                "percent": round(float(usage.percent), 2),
            }
            partitions_data.append(part_info)
            seen_devices.add(device)

            total_bytes += int(usage.total)
            used_bytes += int(usage.used)
            free_bytes += int(usage.free)
        except (PermissionError, OSError, FileNotFoundError):
            # Inaccessible drive (e.g. unready CD-ROM, network share timeout)
            continue

    # Fallback to root or current working drive if partitions enumeration yielded nothing
    if not partitions_data:
        try:
            root_path = "C:\\" if os.name == "nt" else "/"
            usage = psutil.disk_usage(root_path)
            total_bytes = int(usage.total)
            used_bytes = int(usage.used)
            free_bytes = int(usage.free)
            partitions_data.append({
                "device": root_path,
                "mountpoint": root_path,
                "fstype": "unknown",
                "total": total_bytes,
                "used": used_bytes,
                "free": free_bytes,
                "percent": round(float(usage.percent), 2),
            })
        except Exception:
            pass

    overall_percent = round((used_bytes / total_bytes * 100.0), 2) if total_bytes > 0 else 0.0

    return {
        "percent": overall_percent,
        "total": total_bytes,
        "used": used_bytes,
        "free": free_bytes,
        "partitions": partitions_data,
    }
