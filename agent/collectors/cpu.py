import psutil
from typing import Dict, Any, List
from agent.platform import get_cpu_temperature

def collect_cpu(sample_interval: float = 0.1) -> Dict[str, Any]:
    """
    Collect comprehensive cross-platform CPU telemetry.
    Returns:
        total percent, per-core percent list, logical/physical core counts,
        frequency details, and CPU temperature where supported.
    """
    # Sample CPU over small non-blocking interval for responsive collection
    total_percent = psutil.cpu_percent(interval=sample_interval)
    per_core: List[float] = psutil.cpu_percent(interval=None, percpu=True)
    if not per_core:
        per_core = [total_percent]

    freq = psutil.cpu_freq()
    freq_data = None
    if freq:
        freq_data = {
            "current": round(float(freq.current), 2) if freq.current is not None else None,
            "min": round(float(freq.min), 2) if freq.min is not None else None,
            "max": round(float(freq.max), 2) if freq.max is not None else None,
        }

    return {
        "percent": round(float(total_percent), 2),
        "per_core": [round(float(c), 2) for c in per_core],
        "logical_cores": psutil.cpu_count(logical=True),
        "physical_cores": psutil.cpu_count(logical=False),
        "frequency": freq_data,
        "temperature": get_cpu_temperature(),
    }

