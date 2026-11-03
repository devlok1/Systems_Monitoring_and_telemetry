import os
import platform
import psutil
from typing import Dict, Any, Optional

def get_linux_info() -> Dict[str, Any]:
    """Collect Linux-specific distribution and kernel information."""
    distro_name = "Linux"
    distro_version = ""

    # Attempt to read freedesktop os-release (standard on modern Linux)
    if hasattr(platform, "freedesktop_os_release"):
        try:
            os_rel = platform.freedesktop_os_release()
            distro_name = os_rel.get("PRETTY_NAME", os_rel.get("NAME", "Linux"))
            distro_version = os_rel.get("VERSION_ID", "")
        except Exception:
            pass

    if not distro_version and os.path.exists("/etc/os-release"):
        try:
            with open("/etc/os-release", "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("PRETTY_NAME="):
                        distro_name = line.strip().split("=", 1)[1].strip('"')
                    elif line.startswith("VERSION_ID=") and not distro_version:
                        distro_version = line.strip().split("=", 1)[1].strip('"')
        except Exception:
            pass

    return {
        "os": "Linux",
        "distro": distro_name,
        "version": distro_version or platform.release(),
        "kernel": platform.release(),
        "architecture": platform.machine(),
    }

def get_linux_temperature() -> Optional[float]:
    """Collect CPU temperature on Linux via psutil sensors or /sys/class/thermal."""
    try:
        if hasattr(psutil, "sensors_temperatures"):
            temps = psutil.sensors_temperatures()
            if temps:
                # Prefer coretemp, k10temp, cpu_thermal, acpitz
                for key in ["coretemp", "k10temp", "cpu_thermal", "acpitz", "cpu-thermal"]:
                    if key in temps and temps[key]:
                        for entry in temps[key]:
                            if entry.current is not None:
                                return float(entry.current)
                # Fallback to any sensor
                for entries in temps.values():
                    for entry in entries:
                        if entry.current is not None:
                            return float(entry.current)
    except Exception:
        pass
    return None
