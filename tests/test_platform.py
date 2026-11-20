from unittest.mock import patch
from agent.platform import is_windows, is_linux, detect_platform_info, get_cpu_temperature
from agent.platform.windows import get_windows_info
from agent.platform.linux import get_linux_info

def test_platform_detection_current_host():
    info = detect_platform_info()
    assert info["hostname"]
    assert info["os"] in ("Windows", "Linux", "Darwin")
    assert info["architecture"]
    assert info["boot_time"] > 0
    assert info["uptime_seconds"] >= 0
    assert info["python_version"]

def test_windows_info_mock():
    with patch("platform.system", return_value="Windows"), \
         patch("platform.win32_ver", return_value=("11", "10.0.22631", "SP0", "Multiprocessor Free")):
        win_info = get_windows_info()
        assert win_info["os"] == "Windows"
        assert win_info["release"] == "11"
        assert win_info["build"] == "10.0.22631"

def test_linux_info_mock():
    with patch("platform.system", return_value="Linux"), \
         patch("platform.release", return_value="6.1.0-21-amd64"):
        linux_info = get_linux_info()
        assert linux_info["os"] == "Linux"
        assert linux_info["kernel"] == "6.1.0-21-amd64"

def test_temperature_safe_fallback():
    # Verify that get_cpu_temperature never raises an unhandled exception
    temp = get_cpu_temperature()
    assert temp is None or isinstance(temp, float)

