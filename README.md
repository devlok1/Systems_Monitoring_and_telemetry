# SYSWATCH — Systems Monitoring & Telemetry Platform (v1.0)

A high-performance, cross-platform, single-machine system monitoring and telemetry platform engineered for **Microsoft Windows** (10/11, Windows Server) and **Linux** distributions (Debian, Ubuntu, Kali, and other mainstream environments).

SYSWATCH continuously collects host resource metrics, ingests and validates them through a FastAPI backend, persists them in an indexed SQLite database, and presents real-time and historical analytics through a dark industrial React dashboard.

---

## 1. Project Overview

SYSWATCH provides complete hardware and software resource visibility for individual workstations and servers. Operating with zero root/administrator privilege requirements for baseline monitoring, SYSWATCH runs a lightweight Python telemetry daemon alongside a resilient FastAPI backend and a responsive, monospace industrial dashboard.

---

## 2. Problem Statement

System administrators and developers frequently encounter monitoring tools that are either overly complex (requiring distributed clusters, Redis, or heavy agent daemons) or platform-biased (functioning well on Linux but failing on Windows, or vice versa). Furthermore, many existing monitoring dashboards either fabricate demonstration mock data or suffer from fragile database schemas and non-reproducible local environments.

SYSWATCH solves this by providing a unified, cross-platform telemetry schema, robust non-blocking metric collection, mathematical throughput calculation, and an authentic, real-time dashboard with zero mock data.

---

## 3. Project Objectives

- **True Cross-Platform Compatibility:** Single shared Python agent capable of auto-detecting Windows and Linux without code branching or separate builds.
- **Unified Telemetry Schema:** Identical JSON structure transmitted by both Windows and Linux agents to a unified FastAPI backend.
- **Mathematical Accuracy:** Precise throughput calculation ($\Delta \text{Bytes} / \Delta t$) handling reboots and counter rollovers without mistaking cumulative counters for bandwidth.
- **Historical Analysis:** Full temporal queries (5m, 15m, 1h, 6h, 24h) and aggregate statistical analysis (min, max, average).
- **Industrial Visual Clarity:** Dark monospace UI preserving the SYSWATCH identity with authentic live telemetry and explicit handling of unsupported sensors.

---

## 4. Architecture

```
                  SYSWATCH Architecture
                            │
                     Telemetry Agent
                            │
                    Platform Detection
                     /             \
                    /               \
                Windows            Linux
                    \               /
                     \             /
                   Shared Telemetry
                        Schema
                            │
                    HTTP POST /telemetry
                            │
                     FastAPI Backend
                            │
                     SQLite Database
                        (WAL Mode)
                            │
                     React Dashboard
```

Detailed architectural diagrams and component breakdowns are documented in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

---

## 5. Technology Stack

- **Agent:** Python 3.10+, `psutil`, `requests`, `pydantic`.
- **Backend:** FastAPI, Uvicorn, SQLite 3 (WAL mode), Pydantic v2.
- **Dashboard:** React 19, TypeScript 5, Vite 8, Tailwind CSS v4.
- **Testing:** Pytest, HTTPX, FastAPI TestClient.
- **CI/CD:** GitHub Actions (Windows + Ubuntu parallel test jobs).

---

## 6. System Requirements

- **Operating Systems:**
  - Microsoft Windows 10/11 or Windows Server 2016+
  - Linux (Debian 11+, Ubuntu 20.04+, Kali Linux 2022+, or RHEL/CentOS 8+)
- **Python:** Version 3.10 or higher.
- **Node.js:** Version 18.0 or higher (for frontend build and development).
- **Privileges:** Standard unprivileged user account.

---

## 7. Installation Instructions

### 7.1 Windows Setup (PowerShell)

```powershell
# Clone or navigate to the repository
cd C:\ARKSET\Github\Systems_Monitoring_and_telemetry

# Create and activate Python virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install Python backend and agent dependencies
pip install -r requirements.txt

# Install Dashboard dependencies
cd dashboard
npm install
cd ..
```

### 7.2 Linux Setup (Debian / Ubuntu / Kali)

```bash
# Clone or navigate to the repository
cd Systems_Monitoring_and_telemetry

# Create and activate Python virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install Python backend and agent dependencies
pip install -r requirements.txt

# Install Dashboard dependencies
cd dashboard
npm install
cd ..
```

### 7.3 Docker Containerized Deployment (Recommended)

Run the complete SYSWATCH stack (Backend + Production Nginx Dashboard) with a single command:

```bash
# 1. Create environment configuration
cp .env.example .env

# 2. Build and start backend and dashboard containers
docker compose up -d --build

# 3. Access dashboard in browser
# Dashboard (Nginx Production Build): http://localhost:3000
# Backend API: http://localhost:8000
# 4. (Optional) Run the containerized agent
docker compose --profile agent up -d
```

For complete Docker architecture, host-versus-container monitoring options, and troubleshooting, see [docs/DOCKER_DEPLOYMENT.md](docs/DOCKER_DEPLOYMENT.md).

---

## 8. Startup Instructions (Native / Bare-Metal)

To run the complete SYSWATCH stack, start the three services (Backend, Agent, Dashboard) in separate terminal tabs or background sessions:

### 8.1 Step 1 — Start the FastAPI Backend

**Windows:**
```powershell
.\.venv\Scripts\python.exe -m uvicorn server.server:app --host 127.0.0.1 --port 8000 --reload
```

**Linux:**
```bash
python3 -m uvicorn server.server:app --host 127.0.0.1 --port 8000 --reload
```

*The backend will initialize `telemetry.db`, run schema migrations, and expose Swagger docs at `http://127.0.0.1:8000/docs`.*

---

### 8.2 Step 2 — Start the Telemetry Agent

**Windows:**
```powershell
.\.venv\Scripts\python.exe agent/agent.py
```

**Linux:**
```bash
python3 agent/agent.py
```

*The agent will auto-detect the operating system, sample system metrics every 3 seconds, and transmit them to `http://127.0.0.1:8000/telemetry`.*

---

### 8.3 Step 3 — Start the React Dashboard

**Windows & Linux:**
```bash
cd dashboard
npm run dev
```

*Access the dashboard in your browser at `http://localhost:5173`.*

---

## 9. Environment Variables

| Variable | Default Value | Description |
|---|---|---|
| `SYSWATCH_BACKEND_URL` | `http://127.0.0.1:8000` | Target URL used by the agent to POST telemetry. |
| `SYSWATCH_INTERVAL` | `3.0` | Agent sampling interval in seconds. |
| `SYSWATCH_TIMEOUT` | `5.0` | Agent HTTP request timeout in seconds. |
| `SYSWATCH_MAX_RETRIES` | `3` | Maximum retry attempts for failed agent transmissions. |
| `SYSWATCH_TOP_PROCESSES`| `10` | Number of top resource processes collected. |
| `SYSWATCH_DB_PATH` | `<root>/telemetry.db` | Absolute or relative path to SQLite database. |
| `SYSWATCH_RETENTION_DAYS`| `7` | Retention policy window in days before purging. |
| `VITE_API_URL` | `http://127.0.0.1:8000` | Backend API base URL consumed by the React UI. |

---

## 10. API Documentation Summary

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Root service banner and status. |
| `GET` | `/health` | Deep health check (DB connectivity & record count). |
| `POST` | `/telemetry` | Ingest agent telemetry snapshot. |
| `GET` | `/telemetry/latest` | Retrieve latest record with calculated network throughput. |
| `GET` | `/telemetry` | Paginated retrieval (`limit`, `offset`, `hostname`). |
| `GET` | `/telemetry/history` | Historical time-range query (`start`, `end`, `hostname`). |
| `GET` | `/telemetry/stats` | Aggregate statistics (min, max, avg, transfer volume). |
| `POST` | `/maintenance/cleanup` | Execute database retention pruning. |
| `GET` | `/logs` | Query system logs (`level`, `search`, `limit`). |
| `GET` | `/alerts` | Query active or historical alerts. |
| `POST` | `/alerts/{id}/dismiss` | Dismiss an alert record. |

Full interactive API documentation is available via Swagger UI at `http://127.0.0.1:8000/docs`.  
Comprehensive endpoint specifications are located in [docs/API_REFERENCE.md](docs/API_REFERENCE.md).

---

## 11. Database Schema

SYSWATCH stores telemetry in a centralized SQLite database using WAL mode:
- **`telemetry`**: Stores host metadata, timestamps, CPU metrics, memory metrics, disk partitions, cumulative network bytes, interface data, and top processes.
- **`logs`**: System and daemon event log entries.
- **`alerts`**: Threshold notifications and security notices.
- **Indexes:** `idx_telemetry_timestamp`, `idx_telemetry_host_ts`, `idx_logs_timestamp`, `idx_alerts_timestamp`.

Schema definitions and migration details are documented in [docs/DATABASE_SCHEMA.md](docs/DATABASE_SCHEMA.md).

---

## 12. Automated Testing

Run the automated test suite with pytest:

```bash
# Windows
.\.venv\Scripts\pytest.exe -v

# Linux
pytest -v
```

### Test Coverage Highlights:
- Agent collectors (CPU, Memory, Disk drives/mounts, Network I/O, Processes).
- Pydantic schema validation & serialization.
- Exponential backoff retry logic.
- Mathematical network throughput ($dt$ calculation, counter rollovers, reboot handling).
- Historical query time filters and aggregate statistics calculations.
- Cross-platform detection and safe hardware sensor fallbacks.
- End-to-end telemetry pipeline verification.

Build the React frontend to verify type safety and bundle output:
```bash
cd dashboard
npm run build
```

---

## 13. Documentation Index

- [System Architecture](docs/ARCHITECTURE.md)
- [Docker Deployment Guide](docs/DOCKER_DEPLOYMENT.md)
- [Codebase Audit & Problem Assessment](docs/CODE_AUDIT.md)
- [API Reference Manual](docs/API_REFERENCE.md)
- [Database Schema & Migration](docs/DATABASE_SCHEMA.md)
- [Development Log](docs/DEVELOPMENT_LOG.md)

---

## 14. Current Limitations & Roadmap

- **Single-Machine Milestone:** Currently optimized for monitoring the local machine on which the agent runs. Multi-machine aggregation is ready via the `host_id` and `hostname` database schema.
- **Hardware Temperature:** Linux exposes CPU core temperature via `/sys/class/thermal` and kernel drivers. On standard Windows consumer environments without custom WMI/ACPI thermal drivers, temperature is safely returned as `null` to avoid fabricated measurements.
- **Authentication:** V1.0 operates as an internal monitoring tool without mandatory token auth between agent and server. Token-based HMAC authentication is slated for v1.1.
