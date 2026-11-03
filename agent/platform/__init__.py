import platform
import psutil
import time
from typing import Dict, Any, Optional

from agent.platform.windows import get_windows_info, get_windows_temperature
from agent.platform.linux import get_linux_info, get_linux_temperature

def is_windows() -> bool:
    return platform.system() == "Windows"

def is_linux() -> bool:
    return platform.system() == "Linux"

def detect_platform_info() -> Dict[str, Any]:
    """Auto-detect operating system and return standardized host information."""
    system = platform.system()
    boot_time = psutil.boot_time()
    uptime_seconds = time.time() - boot_time

    if system == "Windows":
        details = get_windows_info()
        os_version = f"Windows {details.get('release', '')} (Build {details.get('build', '')})".strip()
        os_release = details.get("release", "")
    elif system == "Linux":
        details = get_linux_info()
        os_version = f"{details.get('distro', 'Linux')} {details.get('version', '')}".strip()
        os_release = details.get("kernel", platform.release())
    else:
        os_version = platform.version()
        os_release = platform.release()

    return {
        "hostname": platform.node(),
        "os": system,
        "os_version": os_version,
        "os_release": os_release,
        "architecture": platform.machine(),
        "boot_time": boot_time,
        "uptime_seconds": uptime_seconds,
        "python_version": platform.python_version(),
    }

def get_cpu_temperature() -> Optional[float]:
    """Retrieve CPU temperature across platforms, returning None if unavailable."""
    if is_windows():
        return get_windows_temperature()
    elif is_linux():
        return get_linux_temperature()
    return None
