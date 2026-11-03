# SYSWATCH — Codebase Audit & System Assessment
**Date:** 2026-11-03  
**Status:** Completed  
**Auditor:** Senior Systems Engineer & Distributed Systems Developer  

---

## 1. Executive Summary

A comprehensive architectural and code-level audit was conducted on the SYSWATCH (Systems Monitoring & Telemetry) repository. SYSWATCH is designed as a single-machine (with future multi-machine capability) system monitoring platform providing real-time telemetry collection, storage, analytical history, and visualization across both Microsoft Windows and Linux distributions.

The codebase currently exhibits a working conceptual prototype with critical implementation gaps, syntax and runtime bugs, schema fragmentation across database files, duplicated frontend directories, and entirely mock-driven dashboard views.

---

## 2. Inventory of Repository Components

| Path | Purpose / Description | Status / Issues Identified |
|---|---|---|
| `agent/agent.py` | Telemetry collection agent using `psutil`, `platform`, `requests` | Functional baseline, but has metric bugs (e.g., `per_core` misses `percpu=True`, single disk root `/` only, hardcoded backend URL, no retries). |
| `server/server.py` | FastAPI backend server | Severe runtime bugs (`json.laods`, misspelled `telemtry`, invalid dictionary syntax on root endpoint), lacks validation, pagination, history endpoints. |
| `server/database.py` | SQLite connection and DDL setup | Executes table DDL at module import time; relative database path sensitive to CWD; no indexes. |
| `server/check_db.py` | Ad-hoc SQLite inspector script | Reads latest record and prints JSON fields. |
| `telemetry.db` | Active SQLite database | Schema matches modern format with JSON fields, but holds 0 rows. |
| `telemetry_old.db` | Legacy SQLite database | Holds 13 historical records from host `Arx_369` with flat columnar schema. Needs non-destructive migration. |
| `dashboard/` | Default starter frontend | Contains boilerplate React+Vite starter (`hero.png`, default counter); does NOT contain the SYSWATCH application. |
| `Duplicate Home Page/` | Actual SYSWATCH UI prototype | Contains complete dark industrial SYSWATCH UI (`HomePage`, `CpuPage`, `MemoryPage`, `NetworkPage`, `LogsPage`, `AlertsPage`), but with 100% hardcoded mock data and Figma-generation scaffolding. |
| `requirements.txt` | Python dependencies list | Lists `psutil`, `fastapi`, `uvicorn`, `requests`, `sqlite3`. Needs test tooling (`pytest`, `httpx`). |

---

## 3. Detailed Component Audit

### 3.1 Telemetry Agent (`agent/agent.py`)

1. **CPU Collection (`collect_cpu`)**:
   - `psutil.cpu_percent(interval=1)` is called, followed by `psutil.cpu_percent(interval=0)`. The second call is assigned to `"per_core"`, but lacks `percpu=True`. Consequently, `"per_core"` is a single float rather than a list of individual core utilization percentages.
   - Frequency retrieval handles `None`, but `current`, `min`, `max` can be unsupported in certain virtualized or Linux/Windows environments without fallback documentation.
2. **Disk Collection (`collect_disk`)**:
   - Calls `psutil.disk_usage("/")`. On Windows, `/` maps only to the current working volume (typically `C:\`), ignoring other logical partitions (e.g. `D:\`, `E:\`). On Linux, this only monitors root filesystem and ignores mount points.
   - Returns a single object rather than an array of partitions/mount points and an aggregate total.
3. **Network Collection (`collect_network`)**:
   - Hardcodes IPv4 check as `address.family == 2`. While socket.AF_INET is 2 on Windows and Linux, referencing `socket.AF_INET` explicitly prevents subtle platform bugs.
   - Does not collect packet counters (`packets_sent`, `packets_recv`), error counters, or drop counters.
   - Interface status (`is_up`, `mtu`) is gathered, but interface operational throughput (KB/s, MB/s) is not calculated over time.
4. **Process Collection (`collect_processes`)**:
   - Iterates processes catching only `(psutil.NoSuchProcess, psutil.AccessDenied)`. `psutil.ZombieProcess` and general collection exceptions are unhandled.
   - Missing username attribute.
5. **System / Host Information (`collect_system`)**:
   - Only records `os`, `hostname`, and `uptime`.
   - Missing required fields: `os_version`, `os_release`, `architecture`, `agent_version`, `python_version`, `boot_time`.
6. **Network Reliability & Configuration**:
   - Target URL `"http://127.0.0.1:8000/telemetry"` and interval `5` are hardcoded.
   - Lacks retry loop, exponential backoff, request timeout recovery, and logging.
7. **Timestamps**:
   - Uses `time.time()` float epoch. Needs standardized ISO-8601 UTC strings alongside numerical epoch for deterministic cross-platform handling.

### 3.2 FastAPI Backend (`server/server.py` & `server/database.py`)

1. **Critical Syntax & Runtime Bugs**:
   - **Line 23**: `return {"message: System telemetry server is running."}` defines a Python `set` of a single string rather than a dictionary `{"message": "..."}`.
   - **Line 101 & 136**: `json.laods(row["memory_percent"])` contains two bugs:
     - Typo `json.laods` raises `AttributeError: module 'json' has no attribute 'laods'`.
     - `row["memory_percent"]` is a numeric `REAL` column, not a JSON string, causing a TypeError when parsed. The intended column is `row["memory_data"]`.
   - **Line 107**: `return telemtry` raises `NameError: name 'telemtry' is not defined`.
2. **Missing Endpoints**:
   - `GET /health` is absent.
   - `GET /telemetry/history` with query parameters (`start`, `end`, `interval`, `limit`, `offset`) is absent.
   - `GET /telemetry/stats` with aggregate calculations is absent.
3. **Request & Response Validation**:
   - `POST /telemetry` accepts untyped `dict` with direct dictionary lookups (`data["system"]["hostname"]`, etc.). Any missing key raises an unhandled HTTP 500 error.
   - Lacks Pydantic request models (`TelemetryPayload`, `HostInfo`, `CpuMetrics`, etc.).
4. **Database Management**:
   - DDL statements execute on file import in `server/database.py`.
   - Hardcoded database path `"telemetry.db"` uses relative resolution, breaking if executed from a different directory.
   - Queries lack pagination parameters and time-window filtering.
   - Missing database indexes on `timestamp` and `hostname`.

### 3.3 Database Audit (`telemetry.db` vs `telemetry_old.db`)

1. **Schema Discrepancy**:
   - **`telemetry_old.db`**: 
     - Columns: `id`, `hostname`, `timestamp`, `cpu_percent`, `memory_percent`, `disk_percent`, `bytes_sent`, `bytes_received`.
     - Records: 13 historical entries from host `Arx_369`.
   - **`telemetry.db`**:
     - Columns: `id`, `hostname`, `os`, `timestamp`, `uptime`, `cpu_percent`, `cpu_data`, `memory_percent`, `memory_data`, `disk_percent`, `disk_data`, `network_data`, `processes_data`.
     - Records: 0 entries.
2. **Data Preservation & Migration Plan**:
   - The 13 records in `telemetry_old.db` must not be discarded.
   - Migration required: Create a non-destructive migration script that transforms flat records into the canonical telemetry schema, populating JSON columns with valid fallback structures, preserving original timestamps, and copying to `telemetry.db`.
   - Both databases must be backed up prior to migration.

### 3.4 Frontend Audit (`dashboard/` vs `Duplicate Home Page/`)

1. **Directory Duplication**:
   - `dashboard/`: Bare Vite React scaffolding (`hero.png`, sample counter).
   - `Duplicate Home Page/`: Contains the actual SYSWATCH implementation:
     - `App.tsx`: Industrial dark theme header, status badge, navigation sidebar (`HOME`, `CPU`, `MEMORY`, `NETWORK`, `LOGS`, `ALERTS`).
     - SVG Components: `LineChart`, `DonutChart`, `BarMeter`, `Panel`.
     - Page Views: `HomePage`, `CpuPage`, `MemoryPage`, `NetworkPage`, `LogsPage`, `AlertsPage`.
     - Artifacts from Figma export (`.figma/`, `AGENTS.md`, `CLAUDE.md`, `.mise.toml`).
2. **Mock Data Analysis**:
   - Every single page contains hardcoded mock arrays and objects (`cpuHistory`, `memHistory`, `CORES`, `tempHistory`, `PROCESSES`, `INTERFACES`, `CONNS`, `LOGS`, `INITIAL_ALERTS`).
   - Zero API integration or HTTP request logic exists.
3. **Consolidation Strategy**:
   - Consolidate the actual SYSWATCH components into `dashboard/src`.
   - Keep Tailwind CSS integration and React 19 setup.
   - Establish typed API services (`src/services/api.ts`, `src/types/telemetry.ts`).
   - Connect live polling and historical range fetching to backend endpoints.

---

## 4. Cross-Platform Gap Analysis (Windows vs Linux)

| Feature | Windows Requirements | Linux Requirements | Current Status |
|---|---|---|---|
| OS Detection | Windows build, edition, arch | Distro, version, kernel, arch | Partial (`platform.system()`) |
| CPU Cores | Physical & logical cores, per-core % | Physical & logical cores, per-core % | Broken (`per_core` single float) |
| CPU Freq / Temp | WMI / psutil freq; temp often unavailable | `/sys/class/thermal` or `psutil.sensors_temperatures()` | Temperature mock only; freq basic |
| Disk Metrics | Logical drive letters (`C:`, `D:`) | Mount points (`/`, `/home`, etc.) | Broken (`/` only) |
| Network | Net interfaces, IP, cumulative I/O | Net interfaces, IP, operational state | Interfaces collected, no throughput |
| Processes | Handle `AccessDenied` on System PIDs | Handle root/kernel thread permissions | Partial handling |
| Database Path | Portable `pathlib.Path` | Portable `pathlib.Path` | Vulnerable relative path |

---

## 5. Remediation Roadmap

1. **Checkpoint & Repository Hygiene**:
   - Stage existing modifications and initialize a clean Git checkpoint.
   - Configure `.gitignore` to prevent committing virtualenvs, temporary caches, and raw database locks.
2. **Database Migration & Canonical Schema**:
   - Back up `telemetry.db` and `telemetry_old.db`.
   - Implement migration script migrating the 13 records into canonical schema.
   - Establish index on `timestamp` and `hostname`.
3. **Modular Cross-Platform Telemetry Agent**:
   - Implement canonical schema definition (`telemetry_schema.py`).
   - Implement platform detection (`platform/windows.py`, `platform/linux.py`).
   - Implement collectors for CPU, Memory, Disk (all drives/mounts), Network (with throughput calc), Processes.
   - Add retries, backoff, and configurable environment variables (`SYSWATCH_BACKEND_URL`, `SYSWATCH_INTERVAL`).
4. **Backend API Stabilization & Expansion**:
   - Fix all syntax and variable bugs in `server/server.py`.
   - Implement Pydantic request and response schemas.
   - Add `GET /health`, `GET /telemetry`, `GET /telemetry/latest`, `GET /telemetry/history`, `GET /telemetry/stats`.
   - Add database retention management (`DELETE FROM telemetry WHERE timestamp < :cutoff`).
5. **Dashboard Consolidation & Real-Time / Historical Integration**:
   - Migrate actual SYSWATCH UI into `dashboard/`.
   - Implement `api.ts` and `types/telemetry.ts`.
   - Replace all mock data across `HomePage`, `CpuPage`, `MemoryPage`, `NetworkPage`, `LogsPage`, `AlertsPage` with real telemetry.
   - Add auto-refresh polling with stale indicator and backend disconnection handling.
   - Wire historical time-range filters (5m, 15m, 1h, 6h, 24h) to `/telemetry/history`.
6. **Automated Testing & Cross-Platform CI**:
   - Unit and integration tests using `pytest` and `fastapi.testclient.TestClient`.
   - Agent collector unit tests with platform mocking.
   - GitHub Actions CI workflow covering Windows and Linux (Ubuntu).
7. **Documentation**:
   - Complete `README.md`, `ARCHITECTURE.md`, `API_REFERENCE.md`, `DATABASE_SCHEMA.md`, `DEVELOPMENT_LOG.md`.
