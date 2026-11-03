import platform
import psutil
from typing import Dict, Any, Optional

def get_windows_info() -> Dict[str, Any]:
    """Collect Windows-specific host information."""
    win_ver = platform.win32_ver()
    return {
        "os": "Windows",
        "release": win_ver[0] or platform.release(),
        "version": win_ver[1] or platform.version(),
        "build": win_ver[1],
        "csd": win_ver[2],
        "architecture": platform.machine(),
    }

def get_windows_temperature() -> Optional[float]:
    """
    CPU temperature collection on Windows.
    Standard psutil does not support sensors_temperatures on Windows;
    returns None cleanly without crashing.
    """
    try:
        if hasattr(psutil, "sensors_temperatures"):
            temps = psutil.sensors_temperatures()
            if temps:
                for name, entries in temps.items():
                    for entry in entries:
                        if entry.current is not None:
                            return float(entry.current)
    except Exception:
        pass
    return None
