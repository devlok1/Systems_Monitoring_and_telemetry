# SYSWATCH — Docker Deployment & Containerization Guide

**Version:** 1.0.0  
**Target Environments:** Microsoft Windows (Docker Desktop WSL2) & Linux (Docker Engine & Compose v2)  
**Architecture:** Micro-service containerization with production Nginx reverse proxy and persistent SQLite volume  

---

## 1. System Topology & Container Architecture

```text
                                 SYSWATCH DEPLOYMENT
                                          │
                                 Docker Compose v2
                                          │
                     ┌────────────────────┼────────────────────┐
                     │                    │                    │
                     ▼                    ▼                    ▼
             syswatch-dashboard    syswatch-backend     syswatch-agent
               (Nginx Alpine)     (FastAPI Python 3.12)  (Optional Profile)
                     │                    │                    │
              Port 3000 -> 80          Port 8000               │
              (Static SPA + Proxy)        │                    │
                     │                    │                    │
                     └─────── Reverse ────┤                    │
                              Proxy       │                    │
                                          ▼                    │
                                 SQLite Persistent Store       │
                                (Named Volume: syswatch-data)  │
                                          ▲                    │
                                          └────── Ingest ──────┘
                                            (POST /telemetry)
```

### 1.1 Container Responsibilities

| Container | Image Base | Purpose | Port / Endpoint | Healthcheck |
|---|---|---|---|---|
| `syswatch-backend` | `python:3.12-slim` | FastAPI REST API, analytics engine, historical calculations, and SQLite persistence. | `8000` (Internal & Host mapped) | `curl -f http://127.0.0.1:8000/health` |
| `syswatch-dashboard` | Multi-stage (`node:20-alpine` -> `nginx:alpine`) | Production SPA web server and API reverse proxy routing `/health`, `/telemetry`, `/logs`, `/alerts`. | `3000 -> 80` (Primary browser entry) | `wget -q --spider http://127.0.0.1:80/` |
| `syswatch-agent` | `python:3.12-slim` | Optional containerized telemetry agent for monitoring container workloads (enabled via `--profile agent`). | Internal Docker network | Process supervision & retry loop |

---

## 2. Prerequisites & Installation

### 2.1 Microsoft Windows 10 / 11 / Server
- Docker Desktop with WSL2 backend enabled.
- Docker Compose v2 (`docker compose version` >= 2.20).
- Windows PowerShell 5.1+ or PowerShell 7+.

### 2.2 Linux Distributions (Debian, Ubuntu, Kali, RHEL)
- Docker Engine 24.0+
- Docker Compose plugin (`docker-compose-plugin`)
- Unprivileged user added to the `docker` group:
  ```bash
  sudo usermod -aG docker $USER
  newgrp docker
  ```

---

## 3. Environment Configuration

Copy the sample environment file before first launch:

```bash
cp .env.example .env
```

### Key Configuration Variables

| Variable | Default Value | Description |
|---|---|---|
| `SYSWATCH_BACKEND_PORT` | `8000` | Host port exposing the FastAPI backend. |
| `SYSWATCH_DASHBOARD_PORT` | `3000` | Host port exposing the React dashboard via Nginx. |
| `DATABASE_PATH` | `/app/data/telemetry.db` | Absolute path to SQLite DB file inside the backend container. |
| `COLLECTION_INTERVAL` | `3.0` | Telemetry sampling frequency in seconds. |
| `BACKEND_URL` | `http://backend:8000` | Internal network URL used by containerized agent. |
| `LOG_LEVEL` | `INFO` | Backend log level (`DEBUG`, `INFO`, `WARNING`, `ERROR`). |

---

## 4. Quick Start Commands

### 4.1 Build and Start Core Services (Backend + Dashboard)
```bash
docker compose up -d --build
```

Access the dashboard in your web browser:
```text
http://localhost:3000
```
Swagger API documentation:
```text
http://localhost:3000/docs  (via Nginx Reverse Proxy)
http://localhost:8000/docs  (Direct Backend)
```

### 4.2 Inspect Container Status & Health
```bash
docker compose ps
```
Expected output:
```text
NAME                 IMAGE                    STATUS                  PORTS
syswatch-backend     syswatch-backend:1.0.0   Up (healthy)            0.0.0.0:8000->8000/tcp
syswatch-dashboard   syswatch-dashboard:1.0.0 Up (healthy)            0.0.0.0:3000->80/tcp
```

### 4.3 View Running Logs
```bash
# Follow all container logs
docker compose logs -f

# Follow backend logs
docker compose logs -f backend

# Follow dashboard / Nginx access logs
docker compose logs -f dashboard
```

### 4.4 Stopping & Restarting
```bash
# Stop containers without losing data
docker compose stop

# Restart containers
docker compose restart

# Tear down containers and network (preserves volumes)
docker compose down
```

> [!CAUTION]
> Never run `docker compose down -v` in production! The `-v` flag destroys the persistent SQLite named volume `syswatch-data`.

---

## 5. Host vs. Container Monitoring Modes

### 5.1 Why the Agent is Profile-Gated
Running a monitoring agent inside a standard container isolates it within container namespaces (`cgroups`, namespace PID 1, virtual bridge network). It reflects only the container's isolated view unless explicitly granted host permissions.

To prevent misleading host metrics, `syswatch-agent` is assigned to `profiles: ["agent"]`.

### 5.2 Mode 1: Host Monitoring (Recommended for Accurate Metrics)

#### Windows Host Monitoring
On Windows, Docker Desktop operates Linux containers inside a WSL2 virtual machine. A containerized Linux agent **cannot** inspect Windows physical drive letters (`C:\`, `D:\`), native Windows processes (`explorer.exe`, etc.), or Windows host pagefiles.

**To monitor your Windows host:**
1. Start the backend and dashboard in Docker:
   ```powershell
   docker compose up -d
   ```
2. Run the native Windows agent on your host machine:
   ```powershell
   python agent/agent.py
   # Or using virtual environment:
   .\.venv\Scripts\python.exe agent/agent.py
   ```
The agent automatically posts real Windows telemetry to `http://127.0.0.1:8000/telemetry`, which enters the containerized backend and is visualized on `http://localhost:3000`.

#### Linux Host Monitoring
On Linux, you can either run the agent natively on the host:
```bash
python3 agent/agent.py
```
Or start the agent in host mode:
```bash
docker compose --profile agent up -d
```

### 5.3 Mode 2: Container Environment Monitoring
If you want to monitor the Docker containerized environment itself, activate the agent container:
```bash
docker compose --profile agent up -d
```

---

## 6. Data Persistence & Backup

### 6.1 Persistent Volume Architecture
SQLite is persisted to a dedicated named volume `syswatch-data` mapped to `/app/data` inside `syswatch-backend`.

```text
Host Storage: /var/lib/docker/volumes/syswatch-data/_data
                      │
                      ▼ Bind
Container Path: /app/data/telemetry.db
```

### 6.2 Verifying Persistence Across Container Recreation
1. Send telemetry data using the agent.
2. Verify total records via health endpoint:
   ```bash
   curl http://localhost:8000/health
   ```
3. Destroy and recreate containers:
   ```bash
   docker compose down
   docker compose up -d
   ```
4. Query `/health` or `/telemetry/latest`: All historical and current telemetry remains 100% intact.

### 6.3 Database Backup & Restore
To extract a hot backup of the SQLite database from the running backend:
```bash
# Backup database to host
docker compose exec backend python -c "import sqlite3, sys; src = sqlite3.connect('/app/data/telemetry.db'); dst = sqlite3.connect('/app/data/backup.db'); src.backup(dst); dst.close(); src.close()"
docker cp syswatch-backend:/app/data/backup.db ./telemetry_backup.db

# Restore database from host
docker cp ./telemetry_backup.db syswatch-backend:/app/data/telemetry.db
docker compose restart backend
```

---

## 7. Troubleshooting

| Symptom | Cause | Solution |
|---|---|---|
| `502 Bad Gateway` on Dashboard | Backend container is starting up or unhealthy | Run `docker compose ps` and wait until backend healthcheck passes. |
| Dashboard shows `STATUS: DISCONNECTED` | Browser cannot reach backend API | Verify Nginx proxy pass in `dashboard/nginx.conf` points to `http://backend:8000`. |
| `failed to connect to docker API` | Docker daemon is not running | Start Docker Desktop on Windows or `sudo systemctl start docker` on Linux. |
| Permission denied on `/app/data/telemetry.db` | Container volume ownership mismatch | `Dockerfile.backend` creates `/app/data` with ownership `appuser:appuser`. Do not override with root mounts. |
