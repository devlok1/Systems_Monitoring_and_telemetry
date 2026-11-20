# SYSWATCH — Database Schema & Migration Reference

**Database Engine:** SQLite 3  
**Default Path:** `<repo_root>/telemetry.db` (configurable via `SYSWATCH_DB_PATH`)  
**Journal Mode:** WAL (Write-Ahead Logging)  
**Synchronous:** NORMAL  
**Foreign Keys:** ON  

---

## 1. Canonical Tables

### 1.1 `telemetry`
Primary storage for periodic system telemetry snapshots received from Windows and Linux agents.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Unique record ID |
| `host_id` | TEXT | DEFAULT 'local' | Machine identifier |
| `hostname` | TEXT | NOT NULL | Machine network hostname |
| `os` | TEXT | NOT NULL | Operating system name (`Windows`, `Linux`, `Darwin`) |
| `os_version` | TEXT | NULLABLE | OS distribution or build number |
| `architecture` | TEXT | NULLABLE | System architecture (e.g. `x86_64`, `AMD64`, `aarch64`) |
| `agent_version` | TEXT | NULLABLE | Telemetry agent version string |
| `timestamp` | REAL | NOT NULL | Collection timestamp (Unix epoch in float seconds) |
| `timestamp_utc` | TEXT | NULLABLE | ISO-8601 UTC timestamp string |
| `uptime` | REAL | NULLABLE | Host uptime in seconds |
| `cpu_percent` | REAL | NULLABLE | Total CPU utilization percentage |
| `cpu_data` | TEXT | NULLABLE | JSON object: per-core %, frequency, core counts |
| `memory_percent` | REAL | NULLABLE | RAM utilization percentage |
| `memory_data` | TEXT | NULLABLE | JSON object: used, available, total, swap, buffers, cached |
| `disk_percent` | REAL | NULLABLE | Primary/aggregate disk utilization percentage |
| `disk_data` | TEXT | NULLABLE | JSON object: total, used, free, partitions/mountpoints |
| `network_bytes_sent` | INTEGER | NULLABLE | Cumulative bytes transmitted across all interfaces |
| `network_bytes_recv` | INTEGER | NULLABLE | Cumulative bytes received across all interfaces |
| `network_data` | TEXT | NULLABLE | JSON object: cumulative I/O, per-interface statistics |
| `processes_data` | TEXT | NULLABLE | JSON array: top processes (pid, name, cpu %, mem %, user) |

### 1.2 `logs`
System, daemon, and audit logs.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Unique log ID |
| `timestamp` | REAL | NOT NULL | Event timestamp (Unix epoch) |
| `timestamp_utc` | TEXT | NULLABLE | ISO-8601 UTC timestamp |
| `hostname` | TEXT | NULLABLE | Originating hostname |
| `level` | TEXT | NOT NULL | Severity level (`INFO`, `WARN`, `ERROR`, `DEBUG`) |
| `source` | TEXT | NULLABLE | Log source or service name |
| `message` | TEXT | NOT NULL | Log message content |

### 1.3 `alerts`
System alerts, threshold breaches, and security notices.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Unique alert ID |
| `timestamp` | REAL | NOT NULL | Event timestamp (Unix epoch) |
| `timestamp_utc` | TEXT | NULLABLE | ISO-8601 UTC timestamp |
| `hostname` | TEXT | NULLABLE | Originating hostname |
| `severity` | TEXT | NOT NULL | Severity (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`) |
| `source` | TEXT | NULLABLE | Detector or monitor name |
| `detail` | TEXT | NULLABLE | Detailed description of alert condition |
| `dismissed` | INTEGER | DEFAULT 0 | 0 = Active, 1 = Dismissed |

---

## 2. Performance Indexes

The following indexes ensure $O(\log N)$ lookups during real-time polling, history time-range queries, and aggregate statistical evaluations:

- `idx_telemetry_timestamp`: `CREATE INDEX idx_telemetry_timestamp ON telemetry(timestamp DESC)`
- `idx_telemetry_host_ts`: `CREATE INDEX idx_telemetry_host_ts ON telemetry(hostname, timestamp DESC)`
- `idx_logs_timestamp`: `CREATE INDEX idx_logs_timestamp ON logs(timestamp DESC)`
- `idx_alerts_timestamp`: `CREATE INDEX idx_alerts_timestamp ON alerts(timestamp DESC)`

---

## 3. Retention & Maintenance Policy

- **Default Retention:** 7 days.
- **Configurable via:** `SYSWATCH_RETENTION_DAYS` environment variable.
- **Cleanup Routine:** `cleanup_old_records(retention_days)` executes `DELETE FROM telemetry WHERE timestamp < :cutoff_epoch`.
- **Integrity Guarantee:** Never removes records within active retention window.

---

## 4. Legacy Migration (`telemetry_old.db` -> `telemetry.db`)

Legacy records were structured with flat numerical columns:
`id`, `hostname`, `timestamp`, `cpu_percent`, `memory_percent`, `disk_percent`, `bytes_sent`, `bytes_received`.

Migration strategy (`server/migration.py`):
1. Safely checks for duplicates using `(hostname, timestamp)` matching within 1ms tolerance.
2. Synthesizes valid, standardized JSON payloads for `cpu_data`, `memory_data`, `disk_data`, and `network_data`.
3. Populates `network_bytes_sent` and `network_bytes_recv` indexed columns.
4. Preserves historical timestamps and calculates ISO-8601 UTC representations.
5. Preserves `telemetry_old.db` and backup files untouched.

