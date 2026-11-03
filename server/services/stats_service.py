from typing import List, Dict, Any, Optional

def calculate_network_throughputs(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Given a list of chronological telemetry records (sorted ascending by timestamp),
    calculate upload (TX) and download (RX) throughput in Bytes/sec, KB/s, and MB/s.

    Handles:
    - First measurement (throughput = 0.0)
    - Reboots / counter resets (negative difference -> reset to 0.0)
    - Zero or negligible time differences (dt <= 0)
    """
    if not records:
        return []

    enriched = []
    prev_record: Optional[Dict[str, Any]] = None

    for rec in records:
        rec_copy = dict(rec)
        current_ts = float(rec.get("timestamp") or 0.0)
        current_rx = int(rec.get("network_bytes_recv") or 0)
        current_tx = int(rec.get("network_bytes_sent") or 0)

        rx_bytes_sec = 0.0
        tx_bytes_sec = 0.0

        if prev_record is not None:
            prev_ts = float(prev_record.get("timestamp") or 0.0)
            prev_rx = int(prev_record.get("network_bytes_recv") or 0)
            prev_tx = int(prev_record.get("network_bytes_sent") or 0)

            dt = current_ts - prev_ts
            if dt > 0.05:  # Avoid division by zero or jitter
                diff_rx = current_rx - prev_rx
                diff_tx = current_tx - prev_tx

                if diff_rx >= 0:
                    rx_bytes_sec = diff_rx / dt
                if diff_tx >= 0:
                    tx_bytes_sec = diff_tx / dt

        rec_copy["throughput"] = {
            "rx_bytes_sec": round(rx_bytes_sec, 2),
            "tx_bytes_sec": round(tx_bytes_sec, 2),
            "rx_kb_sec": round(rx_bytes_sec / 1024.0, 2),
            "tx_kb_sec": round(tx_bytes_sec / 1024.0, 2),
            "rx_mb_sec": round(rx_bytes_sec / (1024.0 ** 2), 3),
            "tx_mb_sec": round(tx_bytes_sec / (1024.0 ** 2), 3),
        }

        enriched.append(rec_copy)
        prev_record = rec

    return enriched
