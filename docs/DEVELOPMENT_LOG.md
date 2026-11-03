# SYSWATCH — Engineering & Development Log

**Project:** Systems Monitoring & Telemetry (SYSWATCH v1.0)  
**Milestone:** Stages 1–3 Implementation, Cross-Platform Architecture, Full Stabilization  

---

## Stage 1: Stabilization & Repository Engineering

### 1. Initial State Assessment & Code Audit
- Audited repository root, `agent/`, `server/`, `Duplicate Home Page/`, `dashboard/`, `telemetry.db`, `telemetry_old.db`.
- Confirmed critical runtime bugs in backend (`json.laods`, undefined variable `telemtry`, set return type instead of dict on root endpoint).
- Confirmed agent metric collection bugs: `per_core` CPU called without `percpu=True`; disk collection hardcoded to single root `/`; network IPv4 check hardcoded to numeric family `2`.
- Found schema fragmentation: `telemetry_old.db` had 13 rows in flat format; `telemetry.db` had modern columns but 0 rows.
- Found frontend duplication: `dashboard/` contained bare default Vite starter, while `Duplicate Home Page/` contained actual dark industrial SYSWATCH UI with 100% mock data.
- Created `docs/CODE_AUDIT.md`.
- Staged all uncommitted working files and established initial Git checkpoint.

### 2. Database Engineering & Non-Destructive Migration
- Created backups: `telemetry.db.bak` and `telemetry_old.db.bak`.
- Engineered `server/database.py`:
  - Configurable path via `SYSWATCH_DB_PATH` with stable absolute resolution via `pathlib.Path`.
  - Removed top-level import side-effects.
  - Implemented dynamic column migration (`PRAGMA table_info`) to evolve schemas without dropping data.
  - Enabled SQLite WAL (Write-Ahead Logging) mode and foreign keys.
  - Created indexes on `timestamp` and `hostname`.
- Built `server/migration.py`:
  - Migrated 13 historical records from host `Arx_369` from `telemetry_old.db` into `telemetry.db`.
  - Converted float epoch timestamps into ISO-8601 UTC strings.
  - Synthesized structured JSON records for cpu, memory, disk, and network data.
  - Guaranteed idempotency (subsequent runs skip existing records).

### 3. Modular Cross-Platform Agent
- Formulated modular architecture:
  - `agent/config.py`: Environment variable configuration (`SYSWATCH_BACKEND_URL`, `SYSWATCH_INTERVAL`, `SYSWATCH_TIMEOUT`, `SYSWATCH_MAX_RETRIES`).
  - `agent/telemetry_schema.py`: Canonical cross-platform Pydantic data models.
  - `agent/platform/`: OS detection (`windows.py` and `linux.py`) gathering OS version, release, architecture, uptime, and safe thermal fallbacks.
  - `agent/collectors/`: Discrete metric collectors for `cpu.py`, `memory.py`, `disk.py`, `network.py`, `processes.py`.
  - `agent/collector.py`: Cohesive telemetry aggregator generating ISO timestamps.
  - `agent/agent.py`: Robust collection loop with exponential backoff and timeout recovery.

### 4. FastAPI Backend Stabilization
- Repaired all fatal bugs in `server/server.py`.
- Enforced Pydantic validation via `TelemetryPayload`.
- Implemented `GET /health` with database probe.
- Implemented `GET /telemetry/latest` with instantaneous throughput calculation.
- Implemented `GET /telemetry` with pagination parameters.

---

## Stage 2: Real-Time Monitoring & Dashboard Integration

### 1. Frontend Consolidation
- Cleaned up boilerplate from `dashboard/`.
- Consolidated the genuine dark industrial SYSWATCH design from `Duplicate Home Page/` into `dashboard/`.
- Removed `Duplicate Home Page/` duplicate directory, leaving `Duplicate Home Page.zip` untouched.
- Configured Vite with Tailwind CSS v4 (`@tailwindcss/vite`).

### 2. Removal of Mock Data
- Removed hardcoded constants:
  - `cpuHistory` and `memHistory` arrays.
  - Fake `CORES` array.
  - Mock `tempHistory`.
  - Mock `PROCESSES` table.
  - Mock `INTERFACES` and `CONNS` list.
  - Hardcoded demonstration uptime and statistics.
- Replaced all views with live telemetry state sourced from backend API.

### 3. Real-Time Telemetry Hook & API Client
- Built `dashboard/src/services/api.ts` with typed fetch wrappers.
- Built `dashboard/src/hooks/useTelemetry.ts` polling `/telemetry/latest` and `/telemetry/history` every 3 seconds.
- Added in-flight request guard to prevent request pileup.
- Added connection state management (`CONNECTED`, `STALE`, `DISCONNECTED`).
- Implemented disconnections and stale data warning banners.

---

## Stage 3: Historical Telemetry & Analytics

### 1. Historical Endpoints
- Implemented `GET /telemetry/history`: Time-window filtered chronological queries with computed upload/download rates.
- Implemented `GET /telemetry/stats`: Mathematically rigorous aggregate calculations (CPU min/max/avg, Memory min/max/avg, Disk min/max/avg, total network bytes transferred, average throughput).

### 2. Network Throughput Calculation
- Implemented `server/services/stats_service.py`:
  - $\text{Throughput} = (\text{Bytes}_2 - \text{Bytes}_1) / (t_2 - t_1)$.
  - Handled reboots and negative counter differentials.
  - Computed KB/s and MB/s.

### 3. Multi-Range Selectable Charts
- Added `TimeRangeSelector` component: 5M, 15M, 1H, 6H, 24H.
- Wired interactive time range selection into `HomePage`, `CpuPage`, `MemoryPage`, and `NetworkPage`.

### 4. Database Retention Policy
- Added `cleanup_old_records()` in `server/database.py` (default 7 days).
- Exposed `POST /maintenance/cleanup`.

---

## Stage 4: Testing & Cross-Platform CI

- Authored 22 automated test cases spanning:
  - Agent collectors (CPU, memory, disk, network, processes).
  - Telemetry schema serialization & Pydantic validation.
  - Agent network retry and failure resilience.
  - Database initialization, indexing, and retention pruning.
  - Mathematical network throughput and reboot rollover handling.
  - Historical queries and aggregate statistical computations.
  - Windows and Linux platform detector mocks.
  - Safe thermal fallback checks.
  - End-to-end full pipeline verification.
- Verified test suite: 22 passed in 8.60s.
- Verified React dashboard production build: `npm run build` succeeds in 497ms with zero errors.
- Created `.github/workflows/ci.yml` providing automated Windows and Ubuntu CI workflows.
