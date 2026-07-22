# URJA — Development Setup Guide

**Version**: 1.0
**Author**: Technical Writer
**Last Updated**: 2026-07-22
**Stack**: FastAPI (Python 3.12+) | PostgreSQL 16 / TimescaleDB 2.17 | Next.js 16 | Tailwind v4 | shadcn/ui | Textual (TUI)

> This guide gets you from zero to running URJA locally in under 10 minutes. You do not need to understand the energy domain — just follow the steps.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Clone the Repository](#2-clone-the-repository)
3. [Backend Setup](#3-backend-setup)
4. [Frontend Setup](#4-frontend-setup)
5. [TUI Setup (Optional)](#5-tui-setup-optional)
6. [Docker Alternative (Quickest Path)](#6-docker-alternative-quickest-path)
7. [Verify Everything Works](#7-verify-everything-works)
8. [Troubleshooting](#8-troubleshooting)

---

## 1. Prerequisites

| Tool | Minimum Version | Check Command |
|------|----------------|---------------|
| Python | 3.12+ | `python3.12 --version` |
| Node.js | 20+ | `node --version` |
| npm | 10+ | `npm --version` |
| Docker | 24.0+ | `docker --version` |
| Docker Compose | 2.20+ | `docker compose version` |
| Git | 2.30+ | `git --version` |
| PostgreSQL Client (optional) | 16+ | `psql --version` |

### Platform Notes

- **Linux (Ubuntu 22.04+, Debian 12+)**: Primary target. Everything works natively.
- **macOS**: Works with Docker Desktop. Python 3.12 via `brew install python@3.12`.
- **Windows**: Use WSL2 with Ubuntu. Do not run natively on Windows — the asyncpg driver requires a Unix socket.
- **Raspberry Pi (arm64)**: Works. See [Troubleshooting](#84-arm64-raspberry-pi-notes).

### Install Python 3.12 (if not installed)

```bash
# Ubuntu / Debian
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.12 python3.12-venv python3.12-dev

# macOS
brew install python@3.12

# Verify
python3.12 --version
```

### Install Node.js 20+

```bash
# Ubuntu / Debian
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install nodejs

# macOS
brew install node@20

# Verify
node --version
npm --version
```

---

## 2. Clone the Repository

```bash
git clone https://github.com/ravikumarve/URJA.git
cd URJA
```

The repository is a monorepo with this layout:

```
URJA/
├── backend/          # FastAPI application
│   ├── src/          # Application code
│   ├── tests/        # pytest suite
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/         # Next.js 16 dashboard
│   ├── src/          # Application code
│   ├── Dockerfile
│   └── package.json
├── dashboard-tui/    # Textual TUI (optional)
│   ├── app.py
│   └── Dockerfile
├── docker/           # Docker configs (health checks, monitoring)
├── docs/             # Documentation
└── docker-compose.yml
```

There are no submodules to initialize.

---

## 3. Backend Setup

### 3.1 Create Virtual Environment

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
```

You should see `(.venv)` in your shell prompt. To deactivate later, run `deactivate`.

### 3.2 Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

This installs FastAPI, SQLAlchemy 2.0, asyncpg, ARQ, httpx, Pydantic v2, Alembic, Ruff, mypy, pytest, and all other dependencies.

### 3.3 Configure Environment Variables

```bash
# Copy the example env file
cp .env.example .env

# Edit the .env file
nano .env
```

For local development, the defaults work with one change — you need a local PostgreSQL instance running:

```bash
# Minimum .env for local dev (Docker-based PostgreSQL)
DATABASE_URL=postgresql+asyncpg://urja:urja@localhost:5432/urja
REDIS_URL=redis://localhost:6379/0
JWT_SECRET=dev-secret-do-not-use-in-production
CORS_ORIGINS=http://localhost:3000
LOG_LEVEL=DEBUG
```

> **Tip**: If you are running PostgreSQL via Docker (recommended), skip to Section 3.5 — the container auto-configures the database.

### 3.4 Start PostgreSQL & Redis (Native Alternative)

If you prefer running PostgreSQL and Redis natively instead of Docker:

```bash
# Ubuntu / Debian
sudo apt install postgresql-16 redis-server
sudo systemctl start postgresql redis-server

# Create the URJA database
sudo -u postgres psql -c "CREATE USER urja WITH PASSWORD 'urja';"
sudo -u postgres psql -c "CREATE DATABASE urja OWNER urja;"
```

**Recommended**: Use Docker for the infrastructure services — it is simpler and isolates versions.

### 3.5 Start PostgreSQL & Redis with Docker

```bash
# From the project root
docker compose up -d db redis

# Wait for them to be healthy
docker compose ps

# Verify both show "(healthy)"
```

The `db` service creates the `urja` database and user automatically from the `.env` variables.

### 3.6 Run Database Migrations

```bash
# Ensure your venv is activated and you are in the backend/ directory
cd backend
source .venv/bin/activate

alembic upgrade head
```

Expected output:

```
INFO  [alembic.runtime.migration] Running upgrade  -> <hash>, initial schema
```

If you see `Target database is not up to date`, the migrations ran successfully.

### 3.7 Load Seed Data

```bash
cd backend
source .venv/bin/activate
python scripts/seed.py
```

This creates:
- A demo organization and admin user
- 5–10 sample solar/wind assets
- 30 days of telemetry data (generation, temperature, voltage)
- Sample curtailment events, carbon credits, and health alerts

Default login credentials (printed at the end of the script):

```
Email:    admin@urja.local
Password: change-me-on-first-login
```

### 3.8 Start the Development Server

```bash
cd backend
source .venv/bin/activate
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

The API is now running at **http://localhost:8000**.

Open **http://localhost:8000/docs** in your browser — you should see the Swagger UI with all API endpoints (auth, assets, telemetry, dispatch, carbon, health, settings).

---

## 4. Frontend Setup

### 4.1 Install Dependencies

Open a **new terminal** (keep the backend server running):

```bash
cd frontend
npm install
```

### 4.2 Configure Environment

```bash
cp .env.example .env
```

The defaults work for local development:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_MAP_TILE_URL=https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png
```

### 4.3 Start the Development Server

```bash
cd frontend
npm run dev
```

The frontend starts on **http://localhost:3000** with hot module replacement. Open it in your browser — you should see the login page.

Login with:

```
Email:    admin@urja.local
Password: change-me-on-first-login
```

---

## 5. TUI Setup (Optional)

The Textual-based Terminal UI is optional but showcases a key differentiator. It runs in your terminal or in a browser via `textual-web`.

### 5.1 Install TUI Dependencies

```bash
cd dashboard-tui
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 5.2 Configure Environment

```bash
cp .env.example .env
```

For local development:

```bash
URJA_API_URL=http://localhost:8000/api/v1
URJA_POLL_INTERVAL=15
```

### 5.3 Run the TUI

```bash
cd dashboard-tui
source .venv/bin/activate
python app.py
```

This opens the Textual TUI in your terminal with four screens:
- **Overview** — live generation stats, top alerts
- **Curtailment** — curtailment events, revenue lost
- **Carbon** — credit portfolio, audit trail
- **Health** — asset health scores, active alerts

Navigate with keyboard: **Tab** / **Shift+Tab** to focus, **Arrow keys** to move, **Ctrl+Q** to quit.

---

## 6. Docker Alternative (Quickest Path)

If you do not want to set up Python virtual environments, Node.js, or configure databases, use Docker Compose to run everything with a single command.

### 6.1 Configure Environment

```bash
# From the project root
cp .env.example .env
```

Edit `.env` and change the secrets:

```bash
POSTGRES_PASSWORD=$(openssl rand -base64 32)
REDIS_PASSWORD=$(openssl rand -base64 32)
JWT_SECRET=$(openssl rand -base64 48)
```

### 6.2 Start All Services

```bash
docker compose up -d
```

This builds and starts five containers:

| Service | Container Name | Port | Purpose |
|---------|---------------|------|---------|
| `db` | `urja-db` | 5432 (internal) | PostgreSQL + TimescaleDB |
| `redis` | `urja-redis` | 6379 (internal) | ARQ queue + cache |
| `api` | `urja-api` | 8000 (internal) | FastAPI REST API |
| `frontend` | `urja-frontend` | 3000 (host) | Next.js dashboard |
| `tui` | `urja-tui` | 8080 (host, optional) | Textual TUI via browser |

### 6.3 Run Migrations

```bash
docker compose exec api alembic upgrade head
```

### 6.4 Load Seed Data

```bash
docker compose exec api python scripts/seed.py
```

### 6.5 Optional: Include TUI

The TUI is behind a Docker profile to keep the default stack lean:

```bash
docker compose --profile tui up -d
```

Access the TUI in your browser at **http://localhost:8080**.

### 6.6 Stop Everything

```bash
docker compose down
# To also delete volumes (wipes database data):
docker compose down -v
```

---

## 7. Verify Everything Works

### 7.1 API Auto-Docs

Open **http://localhost:8000/docs** in your browser.

You should see the Swagger UI with these endpoint groups:
- **Auth** — login, refresh, API keys
- **Assets** — CRUD, hierarchy
- **Telemetry** — ingest, query
- **Dispatch** — curtailment, revenue, rules
- **Carbon** — credits, mint, audit trail
- **Health** — scores, alerts, maintenance
- **Settings** — configuration, branding

Try `GET /health` — it should return:

```json
{
  "status": "ok",
  "version": "1.0.0",
  "checks": {
    "database": "connected",
    "redis": "connected",
    "uptime_seconds": 123
  }
}
```

### 7.2 Dashboard

Open **http://localhost:3000** and log in with:

```
Email:    admin@urja.local
Password: change-me-on-first-login
```

You should see the dashboard with:
- 6 KPI cards (Current Generation, Total Revenue, Carbon Credits, etc.)
- Duck curve chart with price overlay
- Mini asset map
- Alert ticker

Navigate to each page:
- **Assets** — asset table, detail view, hierarchy tree
- **Yield** — revenue lost card, dispatch rule editor
- **Carbon** — credit portfolio, mint form, audit trail
- **Health** — health score grid, alert list
- **Settings** — branding, thresholds, API keys

### 7.3 TUI

If running the TUI locally, you should see live data in four screens. The Overview screen shows a data table with generation stats and an alert strip at the top.

### 7.4 Run Backend Tests

```bash
cd backend
source .venv/bin/activate
pytest
```

All tests should pass. Expected output: `===  X passed in Y.YYs ===`

### 7.5 Run Lint and Type Check

```bash
cd backend
source .venv/bin/activate
ruff check .          # Should show zero errors
ruff format --check . # Should show nothing (already formatted)
mypy src/             # Should pass with no errors
```

### 7.6 Verify Frontend Build

```bash
cd frontend
npm run build    # Should complete without errors
npm run lint     # Should show zero errors
```

---

## 8. Troubleshooting

### 8.1 Port Conflicts

```
Error: address already in use
```

Check what is using the ports:

```bash
sudo lsof -i :3000 -i :8000 -i :5432 -i :6379 -i :8080
```

**Common fixes:**

| Port | Service | Typical Conflict | Fix |
|------|---------|-----------------|-----|
| 5432 | PostgreSQL | Native PostgreSQL is running | `sudo systemctl stop postgresql` |
| 6379 | Redis | Native Redis is running | `sudo systemctl stop redis-server` |
| 3000 | Next.js | Another dev server | Kill it: `kill $(lsof -ti :3000)` |
| 8000 | FastAPI | Another API process | Kill it: `kill $(lsof -ti :8000)` |
| 8080 | TUI | Another web service | Change port in docker-compose.yml |

### 8.2 Database Connection Failures

```
sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) connection refused
```

**Causes and fixes:**

| Symptom | Cause | Fix |
|---------|-------|-----|
| `connection refused` | PostgreSQL not running | Start it: `docker compose up -d db` or `sudo systemctl start postgresql` |
| `authentication failed` | Wrong password in `.env` | Check `POSTGRES_PASSWORD` and `DATABASE_URL` match |
| `database "urja" does not exist` | Database not created | Create it: `createdb urja` or run the Docker container which auto-creates it |
| `role "urja" does not exist` | User not created | Create user: `createuser -P urja` |

**Quick diagnostic:**

```bash
# Test connection from API container
docker compose exec api python -c "
from src.config import settings
from sqlalchemy.ext.asyncio import create_async_engine
import asyncio

async def test():
    engine = create_async_engine(settings.database_url)
    async with engine.connect() as conn:
        result = await conn.execute(text('SELECT 1'))
        print(f'Connected: {result.scalar()}')
asyncio.run(test())
"
```

### 8.3 Redis Connection Failures

```
redis.exceptions.ConnectionError: Error 111 connecting to localhost:6379. Connection refused.
```

**Causes and fixes:**

| Symptom | Cause | Fix |
|---------|-------|-----|
| `Connection refused` | Redis not running | Start it: `docker compose up -d redis` or `sudo systemctl start redis-server` |
| `NOAUTH Authentication required` | Password mismatch | Check `REDIS_PASSWORD` in `.env` |
| `ERR max number of clients reached` | Connection pool exhausted | Restart Redis: `docker compose restart redis` |

### 8.4 Python Version Issues

```
SyntaxError: invalid syntax — perhaps you forgot a comma?
```

URJA requires **Python 3.12+**. The code uses Python 3.12 features (type union syntax with `|`, `Self` type, etc.).

```bash
# Check your Python version
python3 --version

# If it is < 3.12, use python3.12 explicitly
python3.12 -m venv .venv

# Or install Python 3.12
# See Section 1 — Prerequisites
```

If you have multiple Python versions, always use `python3.12` explicitly.

### 8.5 Virtual Environment Not Activated

```
ModuleNotFoundError: No module named 'fastapi'
```

Your virtual environment is not activated or you installed packages outside it.

```bash
# Activate the venv
source backend/.venv/bin/activate

# Verify packages are installed
pip list | grep fastapi

# Reinstall if needed
pip install -r backend/requirements.txt
```

### 8.6 Alembic Migration Errors

```
FAILED: Target database is not up to date.
```

```bash
# Check current migration state
alembic current

# Apply all pending migrations
alembic upgrade head

# If you need to roll back (last migration only):
alembic downgrade -1

# If things are completely broken, reset from scratch:
alembic downgrade base
alembic upgrade head
```

### 8.7 Seed Data Script Fails

```
psycopg2.errors.UniqueViolation: duplicate key value violates unique constraint
```

The seed script was already run. You can safely run it again — it skips existing records.

If you need to reset completely:

```bash
# Option 1: Drop and recreate the database
docker compose exec db psql -U urja -c "DROP DATABASE urja;"
docker compose exec db psql -U urja -c "CREATE DATABASE urja;"
alembic upgrade head
python scripts/seed.py

# Option 2: Wipe everything with Docker (including volumes)
docker compose down -v
docker compose up -d
alembic upgrade head
python scripts/seed.py
```

### 8.8 Frontend Blank Page

```
Blank page in browser, Console shows: Failed to load resource: net::ERR_CONNECTION_REFUSED
```

The frontend cannot reach the API. Check:

```bash
# 1. Is the API running?
curl http://localhost:8000/health

# 2. Is NEXT_PUBLIC_API_URL set correctly?
echo $NEXT_PUBLIC_API_URL
# Should be: http://localhost:8000/api/v1

# 3. Did you restart the frontend dev server after changing .env?
# Kill it (Ctrl+C) and run again:
npm run dev
```

### 8.9 Docker Build Failures

```
ERROR: failed to solve: failed to compute cache key: failed to compute cache key
```

Common Docker issues:

| Error | Cause | Fix |
|-------|-------|-----|
| `failed to compute cache key` | File not found in build context | Check that `backend/`, `frontend/`, etc. exist |
| `Cannot connect to the Docker daemon` | Docker not running | `sudo systemctl start docker` |
| `no matching manifest for linux/arm64` | arm64 image not available | Use `--platform linux/amd64` or check image tags |
| `Build cache is corrupted` | Stale cache | `docker builder prune -a` |

### 8.10 CORS Errors

```
Access to fetch at 'http://localhost:8000/api/v1/...' from origin 'http://localhost:3000'
has been blocked by CORS policy.
```

```bash
# Check CORS_ORIGINS in the API .env
# It should include http://localhost:3000
grep CORS_ORIGINS backend/.env

# If using Docker, restart the API container after changing .env
docker compose restart api
```

### 8.11 Permission Denied on Volume Mounts

```
Permission denied: /var/lib/postgresql/data
```

```bash
# Fix PostgreSQL data directory permissions
sudo chown -R 999:999 /data/urja/postgres

# Fix API uploads directory permissions
sudo chown -R 1000:1000 /data/urja/uploads
```

### 8.12 arm64 / Raspberry Pi Notes

```bash
# URJA runs on Raspberry Pi 4+ (4 GB RAM minimum)
# Use the arm64 TimescaleDB image:
docker compose up -d

# The docker-compose.yml auto-detects the architecture.
# If TimescaleDB fails to pull, explicitly specify:
image: timescale/timescaledb:2.17-pg16-arm64
```

**Known differences on arm64:**
- Build times are ~3x longer (compilation-heavy packages)
- Do not run the TUI container on a Pi with less than 4 GB RAM
- Use at least a 32 GB SD card or external SSD for Docker data

---

## Quick Reference Card

```bash
# ─────────────────────────────────────────────────────────────
# URJA — Quick Start
# ─────────────────────────────────────────────────────────────

# Docker path (fastest — everything in containers)
git clone https://github.com/ravikumarve/URJA.git
cd URJA
cp .env.example .env
# edit .env with secrets
docker compose up -d
docker compose exec api alembic upgrade head
docker compose exec api python scripts/seed.py
open http://localhost:3000

# Manual path (native development)
cp .env.example .env
docker compose up -d db redis
cd backend && python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
python scripts/seed.py
uvicorn src.main:app --reload &
cd ../frontend && npm install && npm run dev
open http://localhost:3000

# Default login
# Email:    admin@urja.local
# Password: change-me-on-first-login

# Useful commands
docker compose ps                    # Check all service statuses
docker compose logs -f api           # Follow API logs
docker compose exec api alembic upgrade head  # Run migrations
docker compose down -v               # Stop and wipe data
```
