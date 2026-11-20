import psutil
from typing import Dict, Any

def collect_memory() -> Dict[str, Any]:
    """
    Collect cross-platform RAM and Swap metrics.
    Works reliably on Windows (pagefile) and Linux (swap partition/file).
    """
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()

    return {
        "total": int(mem.total),
        "used": int(mem.used),
        "available": int(mem.available),
        "percent": round(float(mem.percent), 2),
        "cached": int(getattr(mem, "cached", 0)),
        "buffers": int(getattr(mem, "buffers", 0)),
        "swap": {
            "total": int(swap.total),
            "used": int(swap.used),
            "free": int(swap.free),
            "percent": round(float(swap.percent), 2),
        },
    }

