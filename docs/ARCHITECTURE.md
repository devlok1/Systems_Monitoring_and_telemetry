# SYSWATCH — System Architecture & Design Specification

**Version:** 1.0.0  
**Target Environments:** Microsoft Windows (10/11, Server), Linux (Debian, Ubuntu, Kali, RedHat/CentOS)  
**Architecture Style:** Modular Distributed Single-Machine Agent-Server-Dashboard  

---

## 1. System Topology

```
                  ┌──────────────────────────────────────────────┐
                  │              HOST SYSTEM                     │
                  │   (Windows 10/11/Server or Linux Distros)    │
                  └──────────────────────┬───────────────────────┘
                                         │
                         OS Sensors, psutil & Platform APIs
                                         │
                                         ▼
                  ┌──────────────────────────────────────────────┐
                  │           SYSWATCH TELEMETRY AGENT           │
                  │   - Automatic OS & Arch Identification       │
                  │   - Modular Subsystem Collectors             │
                  │   - Canonical Telemetry Serializer           │
                  │   - Non-Blocking Retry & Backoff Engine      │
                  └──────────────────────┬───────────────────────┘
                                         │
                                   HTTP POST /telemetry
                             (Canonical Telemetry Schema)
                                         │
                                         ▼
                  ┌──────────────────────────────────────────────┐
                  │           FASTAPI INGESTION BACKEND          │
                  │   - Pydantic Payload Validation              │
                  │   - High-Throughput Request Handlers         │
                  │   - Historical Analytics & Stats Engine      │
                  │   - Automatic DB Pruning & Retention         │
                  └──────────────────────┬───────────────────────┘
                                         │
                             SQLite 3 Connection Pool
                             (WAL Mode & Indexed Storage)
                                         │
                                         ▼
                  ┌──────────────────────────────────────────────┐
                  │            SQLITE PERSISTENT STORE           │
                  │   - telemetry table (Indexed by TS & Host)   │
                  │   - logs table                               │
                  │   - alerts table                             │
                  └──────────────────────┬───────────────────────┘
                                         │
                                REST API Endpoints
                      (/telemetry/latest, /history, /stats)
                                         │
                                         ▼
                  ┌──────────────────────────────────────────────┐
                  │           REACT INDUSTRIAL DASHBOARD         │
                  │   - Dark Monospace Industrial Aesthetic      │
                  │   - Real-Time 3s Telemetry Polling           │
                  │   - Stale Pulse & Disconnection Detector     │
                  │   - Multi-Range Historical Charts            │
                  │   - Zero Mock Data / True Real Telemetry     │
                  └──────────────────────────────────────────────┘
```

---

## 2. Core Architectural Subsystems

### 2.1 Cross-Platform Telemetry Agent (`agent/`)

1. **Platform Detection (`agent/platform/`)**:
   - Discovers whether host is Windows or Linux at startup without manual user configuration.
   - On Windows: Queries `platform.win32_ver()` to extract OS release, build version, and platform architecture. Gracefully falls back for temperature.
   - On Linux: Inspects `/etc/os-release` and `platform.freedesktop_os_release()` to detect distributions (Debian, Ubuntu, Kali, etc.) and Linux kernel versions. Discovers thermal sensors via `/sys/class/thermal` and `psutil.sensors_temperatures()`.
2. **Modular Collectors (`agent/collectors/`)**:
   - `cpu.py`: Captures total utilization, per-core utilization (`percpu=True`), core counts, CPU frequency (min/max/current), and CPU temperature where supported.
   - `memory.py`: Captures physical RAM (used, available, total, percent, cached, buffers) and Swap/Pagefile utilization.
   - `disk.py`: Enumerates logical drive letters on Windows (`C:\`, `D:\`) and mounted filesystems on Linux (`/`, `/home`), filtering unready/locked media safely without permission crashes.
   - `network.py`: Aggregates cumulative I/O bytes and packets across all adapters, and gathers per-interface statistics (IPv4 addresses via `socket.AF_INET`, operational UP/DOWN state, MTU, interface speeds).
   - `processes.py`: Sorts and returns top resource-consuming processes, extracting PID, name, RSS memory in bytes, CPU percentage, RAM percentage, and username.
3. **Resilience & Transmission**:
   - Uses configurable timeout, retry count, and exponential backoff.
   - Never crashes the host daemon if backend is temporarily offline or experiencing latency.

---

### 2.2 FastAPI Ingestion & Analytics Backend (`server/`)

1. **Validation & Normalization (`server/schemas/`)**:
   - Validates incoming agent payloads through strict Pydantic schemas (`TelemetryPayload`).
   - Normalizes legacy schema attributes (mapping `system` to `host` seamlessly).
2. **Data Access Layer (`server/database.py`)**:
   - Manages connections using SQLite with WAL (Write-Ahead Logging) mode and normal synchronous I/O, allowing concurrent readers alongside writers.
   - Does not perform schema creation at import time. Employs `init_db()` lifecycle startup hook.
3. **Analytical & Throughput Services (`server/services/`)**:
   - Computes mathematical download and upload rates ($\text{Throughput} = \Delta \text{Bytes} / \Delta t$) across chronological samples.
   - Accounts for hardware reboot counter resets, sample jitter, and non-consecutive intervals.
   - Calculates aggregate metrics (min, max, average, total transferred volume) across arbitrary historical time windows.

---

### 2.3 React / TypeScript Industrial Dashboard (`dashboard/`)

1. **Centralized API Client (`dashboard/src/services/api.ts`)**:
   - Decoupled REST communication using configurable `VITE_API_URL`.
   - Strongly typed responses using TypeScript interfaces.
2. **Telemetry Lifecycle Hook (`dashboard/src/hooks/useTelemetry.ts`)**:
   - Real-time polling cycle (default 3 seconds) with in-flight guard to prevent duplicate stacked requests.
   - Evaluates connection state (`CONNECTED`, `STALE`, `DISCONNECTED`).
   - Dynamic historical time-window querying (5m, 15m, 1h, 6h, 24h).
3. **Pure Metric Visualization**:
   - SVG vector charts (`LineChart`, `DonutChart`, `BarMeter`) rendered purely using native HTML5 SVG and CSS without bulky third-party chart libraries.
   - 100% authentic telemetry data; all placeholder and demonstration mocks removed.

---

## 3. Cross-Platform Strategy

| Subsystem | Windows Specifics | Linux Specifics | Unified Interface |
|---|---|---|---|
| OS Identification | Windows release, build string | Distro name, version, kernel | `HostInfo` model |
| Storage | Logical drives (`C:\`, `D:\`) | Mount points (`/`, `/home`) | `DiskPartition` array |
| Memory | RAM + Pagefile | RAM + Swap + Buffer/Cache | `MemoryMetrics` model |
| Temperature | Handled as `None` (unsupported) | Discovered via kernel sensors | `temperature: Optional[float]` |
| Network | Net adapters, cumulative counters | Interfaces, cumulative counters | `NetworkInterface` array |
| Security | Safe handling of SYSTEM/Admin PIDs | Safe handling of root PIDs | Unprivileged agent mode |

