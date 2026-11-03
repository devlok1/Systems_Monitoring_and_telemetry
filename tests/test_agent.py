from unittest.mock import patch, MagicMock
import requests
from agent.collectors import (
    collect_cpu,
    collect_memory,
    collect_disk,
    collect_network,
    collect_processes,
)
from agent.collector import collect_system_telemetry
from agent.telemetry_schema import TelemetryPayload
from agent.agent import send_telemetry

def test_cpu_collector():
    cpu = collect_cpu(sample_interval=0.01)
    assert "percent" in cpu
    assert isinstance(cpu["percent"], float)
    assert "per_core" in cpu
    assert isinstance(cpu["per_core"], list)
    assert len(cpu["per_core"]) >= 1
    assert cpu["logical_cores"] is not None
    assert cpu["logical_cores"] >= 1

def test_memory_collector():
    mem = collect_memory()
    assert mem["total"] > 0
    assert mem["used"] >= 0
    assert mem["available"] >= 0
    assert 0.0 <= mem["percent"] <= 100.0
    assert "swap" in mem
    assert "percent" in mem["swap"]

def test_disk_collector():
    disk = collect_disk()
    assert disk["total"] > 0
    assert 0.0 <= disk["percent"] <= 100.0
    assert "partitions" in disk
    assert isinstance(disk["partitions"], list)
    assert len(disk["partitions"]) >= 1
    # Check that each partition has device, mountpoint, total, used
    p0 = disk["partitions"][0]
    assert "device" in p0
    assert "mountpoint" in p0
    assert p0["total"] > 0

def test_network_collector():
    net = collect_network()
    assert net["bytes_sent"] >= 0
    assert net["bytes_received"] >= 0
    assert "interfaces" in net
    assert isinstance(net["interfaces"], list)

def test_process_collector():
    procs = collect_processes(limit=5)
    assert isinstance(procs, list)
    if procs:
        p0 = procs[0]
        assert "pid" in p0
        assert "name" in p0
        assert "cpu_percent" in p0
        assert "memory_percent" in p0

def test_full_agent_telemetry_schema_validation():
    data = collect_system_telemetry()
    # Validate that payload strictly conforms to TelemetryPayload Pydantic schema
    payload = TelemetryPayload(**data)
    assert payload.host.hostname
    assert payload.host.os in ("Windows", "Linux", "Darwin")
    assert payload.cpu.percent >= 0.0
    assert payload.memory.total > 0
    assert payload.disk.total > 0

def test_send_telemetry_retry_on_failure():
    # Test retry mechanism when requests fail
    with patch("requests.post") as mock_post:
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection refused")
        result = send_telemetry({"test": 1}, endpoint_url="http://invalid.local/telemetry")
        assert result is False
        assert mock_post.call_count >= 2
