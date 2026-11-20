import os
from dataclasses import dataclass

@dataclass
class AgentConfig:
    backend_url: str = (
        os.environ.get("SYSWATCH_BACKEND_URL")
        or os.environ.get("BACKEND_URL")
        or "http://127.0.0.1:8000"
    ).rstrip("/")
    interval: float = float(
        os.environ.get("SYSWATCH_INTERVAL")
        or os.environ.get("COLLECTION_INTERVAL")
        or "3.0"
    )
    timeout: float = float(os.environ.get("SYSWATCH_TIMEOUT", "5.0"))
    max_retries: int = int(os.environ.get("SYSWATCH_MAX_RETRIES", "3"))
    retry_delay: float = float(os.environ.get("SYSWATCH_RETRY_DELAY", "1.0"))
    top_processes_count: int = int(os.environ.get("SYSWATCH_TOP_PROCESSES", "10"))
    agent_version: str = "1.0.0"

config = AgentConfig()
