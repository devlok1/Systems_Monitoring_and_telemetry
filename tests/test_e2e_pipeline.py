from agent.agent import collect_metrics
from server.schemas.telemetry import TelemetryPayload

def test_full_pipeline_collection_to_api(client):
    """
    End-to-End Pipeline Verification:
    1. Agent collects real machine telemetry.
    2. Payload validates against canonical TelemetryPayload schema.
    3. Payload is transmitted to /telemetry via HTTP POST.
    4. Server persists telemetry in SQLite.
    5. Telemetry is queryable via /telemetry/latest.
    6. Historical records are queryable via /telemetry/history with calculated throughput.
    7. Statistical aggregations compute correctly via /telemetry/stats.
    """
    # 1. Collect real machine metrics
    raw_metrics = collect_metrics()
    assert raw_metrics["host"]["hostname"]
    assert raw_metrics["host"]["os"] in ("Windows", "Linux", "Darwin")

    # 2. Schema validation
    payload = TelemetryPayload(**raw_metrics)
    assert payload.cpu.percent >= 0.0

    # 3. Post to API
    post_res = client.post("/telemetry", json=payload.model_dump())
    assert post_res.status_code == 201
    inserted_id = post_res.json()["id"]
    assert inserted_id > 0

    # 4 & 5. Retrieve via /telemetry/latest
    latest_res = client.get("/telemetry/latest")
    assert latest_res.status_code == 200
    latest = latest_res.json()
    assert latest["hostname"] == raw_metrics["host"]["hostname"]
    assert latest["os"] == raw_metrics["host"]["os"]
    assert latest["cpu"]["percent"] == raw_metrics["cpu"]["percent"]

    # 6. Retrieve via /telemetry/history
    history_res = client.get(f"/telemetry/history?limit=10")
    assert history_res.status_code == 200
    history = history_res.json()
    assert history["count"] >= 1
    assert "throughput" in history["data"][0]

    # 7. Aggregate stats
    stats_res = client.get("/telemetry/stats")
    assert stats_res.status_code == 200
    stats = stats_res.json()
    assert stats["sample_count"] >= 1
    assert stats["cpu"]["avg"] >= 0.0
