from server.services.stats_service import calculate_network_throughputs
from tests.test_server import sample_payload

def test_throughput_calculation_logic():
    samples = [
        {"timestamp": 1000.0, "network_bytes_sent": 10000, "network_bytes_recv": 50000},
        {"timestamp": 1005.0, "network_bytes_sent": 15000, "network_bytes_recv": 60000},  # dt = 5s, diff_tx=5000 (1000 B/s), diff_rx=10000 (2000 B/s)
    ]
    enriched = calculate_network_throughputs(samples)
    assert len(enriched) == 2
    assert enriched[0]["throughput"]["rx_bytes_sec"] == 0.0
    assert enriched[1]["throughput"]["rx_bytes_sec"] == 2000.0
    assert enriched[1]["throughput"]["tx_bytes_sec"] == 1000.0

def test_throughput_reset_on_reboot():
    samples = [
        {"timestamp": 1000.0, "network_bytes_sent": 100000, "network_bytes_recv": 500000},
        {"timestamp": 1005.0, "network_bytes_sent": 1000, "network_bytes_recv": 2000},  # Counter reset / reboot
    ]
    enriched = calculate_network_throughputs(samples)
    assert enriched[1]["throughput"]["rx_bytes_sec"] == 0.0
    assert enriched[1]["throughput"]["tx_bytes_sec"] == 0.0

def test_history_and_stats_api(client):
    host = "stats-node"
    # Insert series of samples: t=1000, 1010, 1020
    p1 = sample_payload(hostname=host, cpu_pct=20.0, ts=1000.0)
    p1["network"]["bytes_sent"] = 10000
    p1["network"]["bytes_received"] = 20000
    client.post("/telemetry", json=p1)

    p2 = sample_payload(hostname=host, cpu_pct=40.0, ts=1010.0)
    p2["network"]["bytes_sent"] = 20000
    p2["network"]["bytes_received"] = 40000
    client.post("/telemetry", json=p2)

    p3 = sample_payload(hostname=host, cpu_pct=60.0, ts=1020.0)
    p3["network"]["bytes_sent"] = 35000
    p3["network"]["bytes_received"] = 70000
    client.post("/telemetry", json=p3)

    # History
    h_res = client.get(f"/telemetry/history?hostname={host}&start=990&end=1030")
    assert h_res.status_code == 200
    hist = h_res.json()
    assert hist["count"] == 3
    # Check that data is sorted ascending
    assert hist["data"][0]["timestamp"] == 1000.0
    assert hist["data"][1]["timestamp"] == 1010.0
    assert hist["data"][2]["timestamp"] == 1020.0
    # Check throughput computed
    assert hist["data"][1]["throughput"]["tx_bytes_sec"] == 1000.0  # (20000 - 10000)/10s

    # Stats
    s_res = client.get(f"/telemetry/stats?hostname={host}&start=990&end=1030")
    assert s_res.status_code == 200
    stats = s_res.json()
    assert stats["sample_count"] == 3
    assert stats["cpu"]["min"] == 20.0
    assert stats["cpu"]["max"] == 60.0
    assert stats["cpu"]["avg"] == 40.0
    assert stats["network"]["total_bytes_sent"] == 25000  # 35000 - 10000
    assert stats["network"]["total_bytes_received"] == 50000  # 70000 - 20000

