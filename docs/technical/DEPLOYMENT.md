# URJA — Deployment Guide

**Version**: 1.0
**Author**: DevOps Automator
**Last Updated**: 2026-07-22
**Stack**: FastAPI (Python 3.12+) + PostgreSQL 16 / TimescaleDB 2.17 + Next.js 16 + Redis 7 + Textual TUI

> This guide covers everything you need to deploy URJA — from a 5-minute local setup to a production-grade deployment with TLS, backups, and monitoring. Written for developers who purchased the boilerplate and need to get it running on their own infrastructure.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Quick Deploy (5 Minutes)](#2-quick-deploy-5-minutes)
3. [Production Deployment](#3-production-deployment)
4. [Docker Compose Configuration](#4-docker-compose-configuration)
5. [Environment Configuration](#5-environment-configuration)
6. [Scaling Considerations](#6-scaling-considerations)
7. [Monitoring & Observability](#7-monitoring--observability)
8. [Troubleshooting](#8-troubleshooting)
9. [Backup & Disaster Recovery](#9-backup--disaster-recovery)

---

## 1. Prerequisites

### Hardware Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | 2 cores | 4 cores |
| RAM | 4 GB | 8 GB |
| Disk | 20 GB SSD | 50 GB SSD |
| Architecture | linux/amd64 | linux/amd64 or linux/arm64 (Raspberry Pi 4+) |

### Software Requirements

| Software | Version | Notes |
|----------|---------|-------|
| Docker | 24.0+ | [Install guide](https://docs.docker.com/engine/install/) |
| Docker Compose | 2.20+ | Ships with Docker Desktop; `docker compose` plugin |
| Git | 2.30+ | For cloning the repository |
| OpenSSL | 3.0+ | For generating secrets |

### Port Requirements

| Port | Service | Protocol | Required | Exposed To |
|------|---------|----------|----------|------------|
| 3000 | Frontend (Next.js) | HTTP | Yes | Host / Internet |
| 8000 | API (FastAPI) | HTTP | Internal | Docker network only |
| 5432 | Database (PostgreSQL) | TCP | Internal | Docker network only |
| 6379 | Redis | TCP | Internal | Docker network only |
| 8080 | TUI (Textual Web) | HTTP | Optional | Host |

### OS Support

| OS | Status | Notes |
|----|--------|-------|
| Ubuntu 22.04+ | ✅ Tested | Primary target |
| Debian 12+ | ✅ Tested | |
| Fedora 38+ | ⚠️ Community | SELinux may need config |
| Raspberry Pi OS (arm64) | ✅ Tested | See [arm64 notes](#arm64-raspberry-pi) |
| macOS (Docker Desktop) | ✅ Tested | Development only |
| Windows (WSL2) | ⚠️ Community | Docker Desktop + WSL2 backend |

---

## 2. Quick Deploy (5 Minutes)

For local development or evaluation, here is the fastest path to a running URJA instance.

```bash
# 1. Clone the repository
git clone https://github.com/ravikumarve/URJA.git
cd URJA

# 2. Create environment file from template
cp .env.example .env

# 3. Edit the .env file with your secrets
#    At minimum, change: POSTGRES_PASSWORD, JWT_SECRET, REDIS_PASSWORD
#    Generate secrets: openssl rand -base64 48
nano .env

# 4. Start all services
docker compose up -d

# 5. Check that all services are healthy
docker compose ps

# 6. Run database migrations
docker compose exec api alembic upgrade head

# 7. Seed initial data (optional)
docker compose exec api python -m app.scripts.seed

# 8. Open the dashboard
echo "Open http://localhost:3000 in your browser"
echo "Default login: admin@urja.local / password: change-me-on-first-login"
```

**What happens behind the scenes:**

```
docker compose up -d
    │
    ├──▶ Network "urja_network" created
    ├──▶ Volume "pgdata" created
    ├──▶ Volume "redisdata" created
    │
    ├──▶ db (PostgreSQL + TimescaleDB) starts
    │       └── pg_isready health check (10s interval)
    │
    ├──▶ redis (Redis 7) starts
    │       └── redis-cli ping health check (10s interval)
    │
    ├──▶ api (FastAPI) starts after db + redis are healthy
    │       ├── Alembic migrations run automatically on first start
    │       └── curl -f http://localhost:8000/health (15s interval)
    │
    ├──▶ frontend (Next.js 16) starts after api is healthy
    │       ├── Production build (first time: ~60s)
    │       └── curl -f http://localhost:3000 (15s interval)
    │
    └──▶ tui (Textual TUI) starts after api is healthy (optional)
            └── Access via http://localhost:8080
```

---

## 3. Production Deployment

### 3.1 Environment Variables Reference

All environment variables are defined in `.env`. See [Section 5](#5-environment-configuration) for the complete template.

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| **Database** | | | |
| `POSTGRES_DB` | Yes | `urja` | PostgreSQL database name |
| `POSTGRES_USER` | Yes | `urja` | PostgreSQL application user |
| `POSTGRES_PASSWORD` | Yes | — | PostgreSQL password (generate: `openssl rand -base64 32`) |
| `POSTGRES_HOST` | Yes | `db` | PostgreSQL hostname (Docker service name) |
| `POSTGRES_PORT` | Yes | `5432` | PostgreSQL port |
| **API** | | | |
| `DATABASE_URL` | Yes | — | Full asyncpg connection string (auto-built from above in .env.example) |
| `REDIS_URL` | Yes | — | Redis connection string (auto-built) |
| `REDIS_PASSWORD` | Yes | — | Redis password (generate: `openssl rand -base64 32`) |
| `JWT_SECRET` | Yes | — | HS256 key for JWT signing (generate: `openssl rand -base64 48`) |
| `JWT_ACCESS_EXPIRE_MINUTES` | No | `15` | Access token lifetime |
| `JWT_REFRESH_EXPIRE_DAYS` | No | `7` | Refresh token lifetime |
| `CORS_ORIGINS` | Yes | `http://localhost:3000` | Comma-separated allowed origins |
| `LOG_LEVEL` | No | `INFO` | Python logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| **External Services (optional)** | | | |
| `WEATHER_API_KEY` | No | — | OpenWeather or Solcast API key |
| `GRID_PRICE_API_KEY` | No | — | Market pricing API key |
| `CARBON_REGISTRY_API_KEY` | No | — | Verra / Hedera Guardian API key |
| `SMTP_HOST` | No | — | Email sending (password reset, alerts) |
| `SMTP_PORT` | No | `587` | SMTP port |
| `SMTP_USER` | No | — | SMTP username |
| `SMTP_PASSWORD` | No | — | SMTP password |
| `SMTP_FROM_EMAIL` | No | — | From address for outgoing emails |
| **Frontend** | | | |
| `NEXT_PUBLIC_API_URL` | Yes | `http://api:8000/api/v1` | API base URL (from browser perspective) |
| `NEXT_PUBLIC_MAP_TILE_URL` | No | OpenStreetMap default | Leaflet tile server URL |
| `NEXT_TELEMETRY_DISABLED` | No | `1` | Disables Next.js telemetry |
| **TUI** | | | |
| `URJA_API_URL` | Yes | `http://api:8000/api/v1` | API base URL for TUI |
| `URJA_POLL_INTERVAL` | No | `15` | Poll interval in seconds |

### 3.2 SSL/TLS Setup

URJA does not terminate TLS internally. You must place a reverse proxy in front of the frontend (port 3000) for production deployments.

#### Option A: Caddy (Recommended — Auto TLS)

Caddy automatically provisions and renews Let's Encrypt certificates.

```bash
# Create a docker-compose.override.yml or separate caddy service
```

```yaml
# caddy.yml — add to your Docker Compose stack
services:
  caddy:
    image: caddy:2-alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile:ro
      - caddy_data:/data
      - caddy_config:/config
    networks:
      - urja_network

volumes:
  caddy_data:
  caddy_config:
```

```caddyfile
# Caddyfile
dashboard.yourfarm.com {
    reverse_proxy frontend:3000

    header /api/* X-Forwarded-Proto {scheme}
    header /* Strict-Transport-Security "max-age=31536000; includeSubDomains"

    # Optional: rate limiting at proxy level
    rate_limit {
        zone dynamic {
            key {remote_host}
            events 1000
            window 1m
        }
    }
}
```

#### Option B: Nginx + Let's Encrypt

```bash
# Install certbot and obtain certificate
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d dashboard.yourfarm.com
```

```nginx
# /etc/nginx/sites-available/dashboard.yourfarm.com
server {
    listen 443 ssl http2;
    server_name dashboard.yourfarm.com;

    ssl_certificate /etc/letsencrypt/live/dashboard.yourfarm.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/dashboard.yourfarm.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' https://*.tile.openstreetmap.org data:; connect-src 'self' https://api.yourfarm.com;";

    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# HTTP → HTTPS redirect
server {
    listen 80;
    server_name dashboard.yourfarm.com;
    return 301 https://$server_name$request_uri;
}
```

#### Option C: Traefik

```yaml
services:
  traefik:
    image: traefik:v3.0
    command:
      - "--providers.docker=true"
      - "--providers.docker.exposedbydefault=false"
      - "--entrypoints.websecure.address=:443"
      - "--certificatesresolvers.letsencrypt.acme.tlschallenge=true"
      - "--certificatesresolvers.letsencrypt.acme.email=admin@yourfarm.com"
      - "--certificatesresolvers.letsencrypt.acme.storage=/letsencrypt/acme.json"
    ports:
      - "443:443"
    volumes:
      - "/var/run/docker.sock:/var/run/docker.sock:ro"
      - "traefik_letsencrypt:/letsencrypt"
    labels:
      - "traefik.enable=true"

  frontend:
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.frontend.rule=Host(`dashboard.yourfarm.com`)"
      - "traefik.http.routers.frontend.entrypoints=websecure"
      - "traefik.http.routers.frontend.tls.certresolver=letsencrypt"
      - "traefik.http.services.frontend.loadbalancer.server.port=3000"

volumes:
  traefik_letsencrypt:
```

### 3.3 Database Backup Strategy

Backups are your safety net. Three complementary strategies are recommended:

#### Strategy 1: Daily pg_dump (Required)

```bash
# /usr/local/bin/urja-backup.sh
#!/bin/bash
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/var/backups/urja}"
DB_CONTAINER="${DB_CONTAINER:-urja-db-1}"
DB_USER="${DB_USER:-urja}"
DB_NAME="${DB_NAME:-urja}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/urja_${TIMESTAMP}.sql.gz"
ENCRYPT_KEY="${ENCRYPT_KEY:-}"

mkdir -p "$BACKUP_DIR"

echo "[$(date)] Starting backup..."

# Dump and compress
docker exec "$DB_CONTAINER" pg_dump \
    --username="$DB_USER" \
    --dbname="$DB_NAME" \
    --format=custom \
    --compress=9 \
    --file=/tmp/urja_dump.dump \
    --no-owner \
    --no-privileges

# Copy out of container
docker cp "${DB_CONTAINER}:/tmp/urja_dump.dump" "${BACKUP_DIR}/urja_${TIMESTAMP}.dump"

# Clean up inside container
docker exec "$DB_CONTAINER" rm /tmp/urja_dump.dump

# Encrypt if key is set
if [ -n "$ENCRYPT_KEY" ]; then
    gpg --batch --yes --passphrase "$ENCRYPT_KEY" \
        --symmetric --cipher-algo AES256 \
        "${BACKUP_DIR}/urja_${TIMESTAMP}.dump"
    rm "${BACKUP_DIR}/urja_${TIMESTAMP}.dump"
    echo "[$(date)] Backup encrypted: urja_${TIMESTAMP}.dump.gpg"
else
    echo "[$(date)] Backup created: urja_${TIMESTAMP}.dump"
fi

# Remove backups older than retention period
find "$BACKUP_DIR" -name "urja_*.dump*" -mtime "+$RETENTION_DAYS" -delete

echo "[$(date)] Backup complete."
```

**Cron schedule:**
```cron
# Run daily at 2:00 AM
0 2 * * * /usr/local/bin/urja-backup.sh >> /var/log/urja-backup.log 2>&1
```

#### Strategy 2: WAL Archiving (Optional, Point-in-Time Recovery)

For deployments that need point-in-time recovery capability:

```sql
-- In postgresql.conf (inside the container or custom config)
wal_level = replica
archive_mode = on
archive_command = 'cp %p /var/lib/postgresql/data/wal_archive/%f'
archive_timeout = 60
```

Mount an additional volume for WAL archives:

```yaml
services:
  db:
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ./backups/wal:/var/lib/postgresql/data/wal_archive
```

#### Strategy 3: Off-Site Replication

- **Cloud storage**: Use `rclone` to sync backup files to S3, Google Cloud Storage, or Backblaze B2 after each dump.
  ```bash
  rclone sync /var/backups/urja remote:urja-backups/
  ```
- **Off-site PostgreSQL**: Set up streaming replication to a secondary server in a different physical location.
- **Database as a Service**: For critical deployments, consider using a managed TimescaleDB instance (Timescale Cloud, AWS RDS with TimescaleDB extension) which provides automated backups and point-in-time recovery out of the box.

### 3.4 Health Check Configuration

Health checks are defined in the Docker Compose file and run at configured intervals. A container is marked as `unhealthy` after 3 consecutive failures.

| Service | Check Command | Interval | Retries | Start Period |
|---------|--------------|----------|---------|--------------|
| **db** | `pg_isready -U urja` | 10s | 5 | 60s |
| **redis** | `redis-cli -a $REDIS_PASSWORD ping` | 10s | 5 | 10s |
| **api** | `curl -f http://localhost:8000/health` | 15s | 3 | 30s |
| **frontend** | `curl -f http://localhost:3000` | 15s | 3 | 120s |
| **tui** | N/A (optional, best-effort) | — | — | — |

The API health endpoint (`GET /health`) returns:

```json
{
    "status": "ok",
    "version": "1.0.0",
    "checks": {
        "database": "connected",
        "redis": "connected",
        "uptime_seconds": 3600
    }
}
```

### 3.5 Resource Limits

Set resource limits to prevent any single container from consuming all host resources. These are recommended safe defaults — adjust based on your deployment scale.

```yaml
services:
  db:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M

  redis:
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 128M
        reservations:
          cpus: '0.1'
          memory: 64M

  api:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M

  frontend:
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 256M
        reservations:
          cpus: '0.25'
          memory: 128M

  tui:
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 128M
        reservations:
          cpus: '0.1'
          memory: 64M
```

### 3.6 Volume Mounts

| Volume | Container Path | Purpose | Backup Required |
|--------|---------------|---------|-----------------|
| `pgdata` | `/var/lib/postgresql/data` | PostgreSQL database files | ✅ Critical |
| `redisdata` | `/data` | Redis persistence (RDB/AOF) | ❌ Repopulated from DB |
| `api_uploads` | `/app/uploads` | User-uploaded files (branding, reports) | ⚠️ Optional |

**Recommended volume configuration:**

```yaml
volumes:
  pgdata:
    driver: local
    driver_opts:
      type: none
      device: /data/urja/postgres
      o: bind

  redisdata:
    driver: local
    driver_opts:
      type: none
      device: /data/urja/redis
      o: bind

  api_uploads:
    driver: local
    driver_opts:
      type: none
      device: /data/urja/uploads
      o: bind
```

Bind-mounting to a dedicated data directory (e.g., `/data/urja/`) simplifies backup and disaster recovery — you can snapshot the entire directory at once.

### 3.7 Production Hardening Checklist

- [ ] **Generate unique secrets** — never use `.env.example` values in production
- [ ] **Enable TLS** — configure Caddy, Nginx, or Traefik with valid certificates
- [ ] **Restrict CORS** — set `CORS_ORIGINS` to your exact frontend domain
- [ ] **Configure CORS** — remove `*` wildcard; use specific origins
- [ ] **Set up automated backups** — daily pg_dump with off-site sync
- [ ] **Enable database encryption at rest** — use LUKS or PostgreSQL TDE
- [ ] **Configure email sending** — set SMTP credentials for password reset
- [ ] **Set up log aggregation** — ship Docker logs to centralized storage
- [ ] **Apply security headers** — via reverse proxy (CSP, HSTS, X-Frame-Options)
- [ ] **Restrict network access** — only expose ports 443 (HTTPS) and optionally 80 (redirect)
- [ ] **Run containers as non-root** — already configured in Docker Compose
- [ ] **Enable Docker BuildKit** — set `DOCKER_BUILDKIT=1` and `COMPOSE_DOCKER_CLI_BUILD=1`

---

## 4. Docker Compose Configuration

### 4.1 Complete docker-compose.yml

```yaml
version: "3.9"

name: urja

# ── Networks ──────────────────────────────────────────────────────────────
networks:
  urja_network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16

# ── Volumes ────────────────────────────────────────────────────────────────
volumes:
  pgdata:
    driver: local
  redisdata:
    driver: local
  api_uploads:
    driver: local

# ── Services ───────────────────────────────────────────────────────────────
services:

  # ── Database ─────────────────────────────────────────────────────────────
  db:
    image: timescale/timescaledb:2.17-pg16
    container_name: urja-db
    restart: unless-stopped
    networks:
      - urja_network
    ports:
      # Internal only — do not expose to host in production
      - "127.0.0.1:5432:5432"
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-urja}
      POSTGRES_USER: ${POSTGRES_USER:-urja}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - pgdata:/var/lib/postgresql/data
      # Optional: mount custom postgresql.conf for tuning
      # - ./docker/db/postgresql.conf:/etc/postgresql/postgresql.conf:ro
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-urja}"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 60s
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    cap_add:
      - CHOWN
      - DAC_OVERRIDE
      - SETUID
      - SETGID

  # ── Redis ────────────────────────────────────────────────────────────────
  redis:
    image: redis:7-alpine
    container_name: urja-redis
    restart: unless-stopped
    networks:
      - urja_network
    ports:
      # Internal only
      - "127.0.0.1:6379:6379"
    command: >
      redis-server
      --requirepass ${REDIS_PASSWORD}
      --appendonly yes
      --appendfsync everysec
      --maxmemory 128mb
      --maxmemory-policy allkeys-lru
    volumes:
      - redisdata:/data
    healthcheck:
      test: ["CMD", "redis-cli", "-a", "${REDIS_PASSWORD}", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5
      start_period: 10s
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 128M
        reservations:
          cpus: '0.1'
          memory: 64M
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL

  # ── API (FastAPI) ────────────────────────────────────────────────────────
  api:
    build:
      context: ./backend
      dockerfile: Dockerfile
      args:
        BUILDKIT_INLINE_CACHE: "1"
    container_name: urja-api
    restart: unless-stopped
    networks:
      - urja_network
    ports:
      # Internal — frontend and TUI access via Docker DNS
      - "127.0.0.1:8000:8000"
    environment:
      DATABASE_URL: ${DATABASE_URL}
      REDIS_URL: ${REDIS_URL}
      JWT_SECRET: ${JWT_SECRET}
      JWT_ACCESS_EXPIRE_MINUTES: ${JWT_ACCESS_EXPIRE_MINUTES:-15}
      JWT_REFRESH_EXPIRE_DAYS: ${JWT_REFRESH_EXPIRE_DAYS:-7}
      CORS_ORIGINS: ${CORS_ORIGINS:-http://localhost:3000}
      LOG_LEVEL: ${LOG_LEVEL:-INFO}
      WEATHER_API_KEY: ${WEATHER_API_KEY:-}
      GRID_PRICE_API_KEY: ${GRID_PRICE_API_KEY:-}
      CARBON_REGISTRY_API_KEY: ${CARBON_REGISTRY_API_KEY:-}
      SMTP_HOST: ${SMTP_HOST:-}
      SMTP_PORT: ${SMTP_PORT:-587}
      SMTP_USER: ${SMTP_USER:-}
      SMTP_PASSWORD: ${SMTP_PASSWORD:-}
      SMTP_FROM_EMAIL: ${SMTP_FROM_EMAIL:-}
    volumes:
      - api_uploads:/app/uploads
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 15s
      timeout: 5s
      retries: 3
      start_period: 30s
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    read_only: true
    tmpfs:
      - /tmp
    user: "1000:1000"

  # ── Frontend (Next.js 16) ───────────────────────────────────────────────
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
      args:
        NEXT_TELEMETRY_DISABLED: "1"
    container_name: urja-frontend
    restart: unless-stopped
    networks:
      - urja_network
    ports:
      - "3000:3000"
    environment:
      NEXT_PUBLIC_API_URL: ${NEXT_PUBLIC_API_URL:-http://api:8000/api/v1}
      NEXT_PUBLIC_MAP_TILE_URL: ${NEXT_PUBLIC_MAP_TILE_URL:-https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png}
      NEXT_TELEMETRY_DISABLED: "1"
    depends_on:
      api:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000"]
      interval: 15s
      timeout: 5s
      retries: 3
      start_period: 120s
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 256M
        reservations:
          cpus: '0.25'
          memory: 128M
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    user: "1000:1000"

  # ── TUI (Textual — Optional) ────────────────────────────────────────────
  tui:
    build:
      context: ./dashboard-tui
      dockerfile: Dockerfile
    container_name: urja-tui
    restart: unless-stopped
    networks:
      - urja_network
    ports:
      # Only expose if you need browser-based TUI access
      - "8080:8080"
    environment:
      URJA_API_URL: ${URJA_API_URL:-http://api:8000/api/v1}
      URJA_POLL_INTERVAL: ${URJA_POLL_INTERVAL:-15}
    depends_on:
      api:
        condition: service_healthy
    profiles:
      # Run with: docker compose --profile tui up -d
      - tui
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 128M
        reservations:
          cpus: '0.1'
          memory: 64M
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    user: "1000:1000"
```

### 4.2 Service Dependencies & Startup Order

```
db (healthy) ──┐
               ├──▶ api (healthy) ──▶ frontend (healthy)
redis (healthy)┘                    └──▶ tui (optional)
```

Startup is orchestrated via `depends_on` with `condition: service_healthy`. Each service waits for its dependencies to pass their health checks before starting. This prevents the API from crashing because the database is not yet accepting connections.

### 4.3 Network Configuration

```
Docker Network: urja_network (bridge, 172.20.0.0/16)
    │
    ├── api:8000       (internal — Docker DNS: http://api:8000)
    ├── frontend:3000  (host-facing — mapped to host port 3000)
    ├── db:5432        (internal — Docker DNS: postgresql://db:5432)
    ├── redis:6379     (internal — Docker DNS: redis://redis:6379)
    └── tui:8080       (optional — mapped to host port 8080)
```

**Security principle:** Database and Redis ports are only accessible within the Docker network. The frontend is the only service exposed to the host (and the outside world via the reverse proxy). The API is accessible internally — the frontend and TUI communicate with it via Docker's internal DNS.

### 4.4 Docker Compose Profiles

The TUI service is behind a profile to keep the default deployment lean:

```bash
# Default: all services except TUI
docker compose up -d

# With TUI
docker compose --profile tui up -d
```

---

## 5. Environment Configuration

### 5.1 Complete .env.example

```bash
# ═══════════════════════════════════════════════════════════════════════════
# URJA — Environment Configuration
# ═══════════════════════════════════════════════════════════════════════════
# Copy this file to .env and edit before running:
#   cp .env.example .env && nano .env
# NEVER commit the actual .env file to version control.
# ═══════════════════════════════════════════════════════════════════════════

# ── Database ──────────────────────────────────────────────────────────────
# PostgreSQL 16 + TimescaleDB
POSTGRES_DB=urja
POSTGRES_USER=urja
POSTGRES_PASSWORD=CHANGE_ME_GENERATE_SECURE_RANDOM
POSTGRES_HOST=db
POSTGRES_PORT=5432

# ── API (FastAPI) ─────────────────────────────────────────────────────────
DATABASE_URL=postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}
REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0

# Redis (used by ARQ task queue + caching)
REDIS_PASSWORD=CHANGE_ME_GENERATE_SECURE_RANDOM

# JWT Authentication
# Generate: openssl rand -base64 48
JWT_SECRET=CHANGE_ME_GENERATE_64_CHAR_BASE64
JWT_ACCESS_EXPIRE_MINUTES=15
JWT_REFRESH_EXPIRE_DAYS=7

# CORS — comma-separated list of allowed origins
CORS_ORIGINS=http://localhost:3000

# Logging (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO

# ── External Services (Optional) ──────────────────────────────────────────
# Weather API (OpenWeather, Solcast, etc.)
WEATHER_API_KEY=
# Grid price API (EPEX, CAISO, Nord Pool, etc.)
GRID_PRICE_API_KEY=
# Carbon registry API (Verra, Hedera Guardian)
CARBON_REGISTRY_API_KEY=

# ── Email (SMTP — Optional) ──────────────────────────────────────────────
# Required for password reset and user invitation emails
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
SMTP_FROM_EMAIL=noreply@yourfarm.com

# ── Frontend (Next.js 16) ────────────────────────────────────────────────
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_MAP_TILE_URL=https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png

# ── TUI (Textual) ─────────────────────────────────────────────────────────
URJA_API_URL=http://api:8000/api/v1
URJA_POLL_INTERVAL=15
```

### 5.2 Production vs Development Differences

| Aspect | Development | Production |
|--------|-------------|------------|
| **Compose file** | `docker compose up -d` | `docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d` |
| **CORS_ORIGINS** | `http://localhost:3000` | `https://dashboard.yourfarm.com` |
| **NEXT_PUBLIC_API_URL** | `http://localhost:8000/api/v1` | `https://api.yourfarm.com/api/v1` or same-domain proxy |
| **LOG_LEVEL** | `DEBUG` | `INFO` or `WARNING` |
| **Database port** | Exposed to host | Internal only |
| **Redis** | Default config | Password required, `maxmemory` set |
| **Secrets** | Placeholder values | Strong generated secrets |
| **Reverse proxy** | None (direct access) | Caddy / Nginx / Traefik with TLS |
| **Volume mounts** | Docker volumes | Bind mounts to specific host paths |
| **Health checks** | Optional | Required for orchestration |
| **Resource limits** | None | CPU + memory constraints |

Use a production override file for environment-specific settings:

```yaml
# docker-compose.prod.yml
services:
  api:
    environment:
      LOG_LEVEL: WARNING

  frontend:
    environment:
      NEXT_PUBLIC_API_URL: https://dashboard.yourfarm.com/api/v1

  db:
    ports:
      # Remove host port mapping entirely
      - "5432"

  redis:
    ports:
      - "6379"
```

Then deploy with:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### 5.3 Secrets Generation

Run these commands to generate strong secrets for production:

```bash
#!/bin/bash
# generate-secrets.sh — run once when setting up production

echo "=== URJA Production Secrets ==="
echo ""
echo "POSTGRES_PASSWORD=$(openssl rand -base64 32)"
echo "REDIS_PASSWORD=$(openssl rand -base64 32)"
echo "JWT_SECRET=$(openssl rand -base64 48)"
echo ""
echo "Save these securely (password manager, vault, or encrypted file)."
echo "They will not be shown again."

# Optional: write directly to .env
# ./generate-secrets.sh > .env
```

**Secret handling rules:**
1. Never commit `.env` to version control (`.env` is in `.gitignore`)
2. Never use `.env.example` values in production
3. Rotate secrets periodically or after any suspected compromise
4. For enterprise deployments, use Docker secrets instead of environment variables

**Docker secrets alternative:**

```yaml
services:
  api:
    secrets:
      - jwt_secret
      - db_password

secrets:
  jwt_secret:
    file: ./secrets/jwt_secret.txt
  db_password:
    file: ./secrets/db_password.txt
```

---

## 6. Scaling Considerations

### 6.1 Vertical Scaling (Recommended First Step)

URJA is designed for single-server deployment. When you outgrow the minimum requirements, vertical scaling is the simplest path:

| Scale | Server Spec | Expected Capacity |
|-------|-------------|-------------------|
| Small | 4 CPU, 8 GB RAM | 50 assets, 100K readings/day |
| Medium | 8 CPU, 16 GB RAM | 200 assets, 500K readings/day |
| Large | 16 CPU, 32 GB RAM | 500 assets, 2M readings/day |

**Upgrade steps:**
1. Stop the stack: `docker compose down`
2. Provision a larger server
3. Copy the `/data/urja` directory to the new server
4. Update DNS to point to the new server
5. Start the stack: `docker compose up -d`

### 6.2 When to Add PgBouncer

PgBouncer provides connection pooling for PostgreSQL. The API uses SQLAlchemy's async connection pool (default: 10 connections), which is sufficient for most deployments.

**Consider PgBouncer when:**
- The API serves more than 50 concurrent requests
- You see `remaining connection slots are reserved` errors in API logs
- You have multiple API replicas connecting to the same database
- You need strict connection limiting for database capacity planning

**Adding PgBouncer:**

```yaml
services:
  pgbouncer:
    image: edoburu/pgbouncer:1.21
    networks:
      - urja_network
    environment:
      DB_USER: ${POSTGRES_USER}
      DB_PASSWORD: ${POSTGRES_PASSWORD}
      DB_HOST: db
      DB_PORT: "5432"
      POOL_MODE: transaction
      MAX_CLIENT_CONN: "100"
      DEFAULT_POOL_SIZE: "20"
    depends_on:
      db:
        condition: service_healthy

  api:
    environment:
      DATABASE_URL: postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@pgbouncer:6432/${POSTGRES_DB}
```

**Important:** Ensure your SQLAlchemy pool settings are appropriate for the PgBouncer pool size:

```python
# backend/app/core/database.py
engine = create_async_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=5,
    pool_pre_ping=True,
)
```

### 6.3 When to Move Redis to Separate Instance

Redis handles ARQ task queuing and cache storage. It is lightweight and can share the server with other services.

**Consider a dedicated Redis instance when:**
- The task queue consistently has > 10,000 pending jobs
- Cache hit ratio drops below 70% (indicating memory pressure)
- Redis container uses > 80% of its allocated memory
- You need Redis Sentinel for high availability

**Separate Redis deployment:**

```yaml
services:
  redis:
    # Remove from main docker-compose.yml
    # Deploy separately or use managed Redis (Upstash, Redis Cloud)
    image: redis:7-alpine
    # ... separate deployment
```

Update the `REDIS_URL` environment variable to point to the external Redis instance:

```bash
REDIS_URL=redis://:password@your-redis-host:6379/0
```

### 6.4 When to Add a CDN for Frontend Assets

The Next.js frontend serves static assets (JavaScript bundles, CSS, images). For most deployments, the built-in serving is sufficient.

**Consider a CDN when:**
- The dashboard loads from multiple geographic regions
- Asset sizes exceed 5 MB per page load
- You have > 100 daily active users
- Time-to-interactive exceeds 3 seconds

**CDN integration:**

```yaml
# frontend/Dockerfile — build with asset prefix
FROM node:20-alpine AS builder
ARG NEXT_PUBLIC_API_URL
ARG CDN_ASSET_PREFIX
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}
ENV NEXT_PUBLIC_CDN_ASSET_PREFIX=${CDN_ASSET_PREFIX}
RUN npm run build

# In production, upload .next/static to your CDN
# Then set the asset prefix in environment
```

For cloud deployments, front the entire application with Cloudflare (free plan is sufficient):

```bash
# 1. Point your domain to Cloudflare nameservers
# 2. Set SSL/TLS to "Full (strict)"
# 3. Enable Auto Minify for HTML, CSS, JS
# 4. Enable Brotli compression
# 5. Set caching rules for static assets
```

### 6.5 Horizontal Scaling Readiness

While URJA is a modular monolith and does not auto-scale, the architecture is designed to be horizontally scaled without code changes:

| Component | Horizontal Strategy | Complexity |
|-----------|-------------------|------------|
| **API** | Run multiple replicas behind a load balancer. Requires shared Redis (already configured) and connection pooling via PgBouncer. | Medium |
| **Frontend** | Stateless — run multiple replicas behind a load balancer. Sessions are JWT-based, no sticky sessions needed. | Easy |
| **ARQ Workers** | Run multiple worker containers consuming from the same Redis queue. Tasks are idempotent. | Easy |
| **Database** | TimescaleDB supports read replicas. Writes go to primary, reads to replicas. Requires connection string changes. | Hard |

---

## 7. Monitoring & Observability

### 7.1 Health Endpoint

The API exposes a health check endpoint at `GET /health`:

```bash
curl http://localhost:8000/health
```

```json
{
    "status": "ok",
    "version": "1.0.0",
    "checks": {
        "database": {
            "status": "connected",
            "response_time_ms": 2
        },
        "redis": {
            "status": "connected",
            "response_time_ms": 1
        },
        "uptime_seconds": 86400
    }
}
```

**Important:** The health endpoint does not leak sensitive information. It returns connectivity status for dependencies only — no environment variables, configuration, or system details.

### 7.2 Docker Health Checks

The Docker Compose file includes health checks for every service. Monitor container health:

```bash
# Check status of all services
docker compose ps

# Watch health status
watch docker compose ps

# View health check logs
docker compose logs db | grep health
docker compose logs api | grep health
```

### 7.3 Log Aggregation

By default, all services log to stdout/stderr, captured by Docker.

#### Quick diagnostic commands:

```bash
# Follow all logs
docker compose logs -f

# Follow specific service
docker compose logs -f api
docker compose logs -f frontend

# Last 100 lines with timestamps
docker compose logs --tail=100 -t api

# Filter by error level
docker compose logs api | grep -i error

# Export logs to file
docker compose logs --no-color > urja-logs-$(date +%Y%m%d).txt
```

#### Production log shipping with Loki + Promtail:

```yaml
# docker-compose.monitoring.yml
services:
  promtail:
    image: grafana/promtail:2.9
    volumes:
      - /var/log:/var/log:ro
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
      - ./docker/monitoring/promtail-config.yml:/etc/promtail/config.yml:ro
    command: -config.file=/etc/promtail/config.yml

  loki:
    image: grafana/loki:2.9
    ports:
      - "3100:3100"
    volumes:
      - ./docker/monitoring/loki-config.yml:/etc/loki/local-config.yml:ro
    command: -config.file=/etc/loki/local-config.yml

  grafana:
    image: grafana/grafana:10.4
    ports:
      - "3001:3000"
    environment:
      GF_SECURITY_ADMIN_PASSWORD: change-me
      GF_INSTALL_PLUGINS: grafana-piechart-panel
    volumes:
      - grafana_data:/var/lib/grafana
```

#### Log shipping with Vector (lighter alternative):

```yaml
services:
  vector:
    image: timberio/vector:0.35-alpine
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - ./docker/monitoring/vector.toml:/etc/vector/vector.toml:ro
    environment:
      VECTOR_REQUIRE_HEALTHY: "false"
```

### 7.4 Metrics (Optional Prometheus + Grafana)

For deployments that need metrics visualization, add Prometheus and Grafana:

```yaml
services:
  prometheus:
    image: prom/prometheus:v2.51
    ports:
      - "9090:9090"
    volumes:
      - ./docker/monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus_data:/prometheus

  grafana:
    image: grafana/grafana:10.4
    ports:
      - "3001:3000"
    environment:
      GF_SECURITY_ADMIN_PASSWORD: change-me
    volumes:
      - grafana_data:/var/lib/grafana

volumes:
  prometheus_data:
  grafana_data:
```

**Prometheus configuration (prometheus.yml):**

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'urja-api'
    static_configs:
      - targets: ['api:8000']
    metrics_path: '/metrics'

  - job_name: 'urja-db'
    static_configs:
      - targets: ['db:9187']  # postgres_exporter sidecar

  - job_name: 'urja-redis'
    static_configs:
      - targets: ['redis:9121']  # redis_exporter sidecar
```

**Suggested Grafana dashboards:**
- API request rate, latency, error rate (RED metrics)
- PostgreSQL connections, cache hit ratio, active queries
- Redis memory usage, hit rate, connected clients
- Container CPU and memory utilization

### 7.5 Backup Verification Schedule

| Frequency | Action | Responsible |
|-----------|--------|-------------|
| Daily | Automated backup runs | Cron |
| Weekly | Verify backup file exists and is non-empty | Manual check |
| Monthly | Restore backup to test environment and verify data integrity | Manual restore + test |
| Quarterly | Test full disaster recovery (provision new server, restore, verify) | Manual drill |

**Backup verification script:**

```bash
#!/bin/bash
# /usr/local/bin/urja-verify-backup.sh
#
# Run weekly: 0 6 * * 1 /usr/local/bin/urja-verify-backup.sh

BACKUP_DIR="${BACKUP_DIR:-/var/backups/urja}"

# Find latest backup
LATEST=$(ls -t "$BACKUP_DIR"/urja_*.dump 2>/dev/null | head -1)

if [ -z "$LATEST" ]; then
    echo "ALERT: No backup found!" | mail -s "URJA Backup Alert" admin@yourfarm.com
    exit 1
fi

# Check file size (minimum 1 MB for a non-empty dump)
SIZE=$(stat -c%s "$LATEST")
if [ "$SIZE" -lt 1048576 ]; then
    echo "ALERT: Backup file too small: $SIZE bytes" | mail -s "URJA Backup Alert" admin@yourfarm.com
    exit 1
fi

# Verify dump integrity
pg_restore --list "$LATEST" > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "ALERT: Backup file corrupted: $LATEST" | mail -s "URJA Backup Alert" admin@yourfarm.com
    exit 1
fi

echo "[OK] Backup verified: $LATEST ($(numfmt --to=iec $SIZE))"
```

---

## 8. Troubleshooting

### 8.1 Common Startup Issues

#### Issue: `docker compose up -d` fails silently

```bash
# Check container status
docker compose ps

# View logs for all services
docker compose logs

# Specific service
docker compose logs api
```

**Typical cause:** Port conflict or missing environment variables.

**Fix:**
```bash
# Check if ports are already in use
sudo lsof -i :3000 -i :8000 -i :5432 -i :6379

# Stop conflicting services
sudo systemctl stop postgresql  # if running natively

# Verify .env file has all required variables
grep -v "^#" .env | grep "=" | wc -l
```

#### Issue: API container exits immediately

```bash
docker compose logs api
```

**Common causes & fixes:**

| Error | Cause | Fix |
|-------|-------|-----|
| `connection refused for database` | Database not ready yet | Use `depends_on: condition: service_healthy` |
| `authentication failed` | Wrong POSTGRES_PASSWORD | Check `.env` matches between api and db services |
| `"secret key is missing"` | JWT_SECRET not set | Add `JWT_SECRET` to `.env` |
| `ModuleNotFoundError` | Build cache stale | `docker compose build --no-cache api` |

#### Issue: Frontend shows blank page or build error

```bash
# Check frontend logs
docker compose logs frontend

# Rebuild (Next.js build errors are caught at build time)
docker compose build --no-cache frontend
docker compose up -d frontend
```

**Common fixes:**

| Symptom | Cause | Fix |
|---------|-------|-----|
| Blank page with console errors | API URL misconfigured | Check `NEXT_PUBLIC_API_URL` in `.env` |
| `TypeError: Cannot read properties of undefined` | Missing env variable at build time | Rebuild with correct env |
| Static 404 on route | Build incomplete | `docker compose build --no-cache frontend` |
| Slow first load | Production build happening on startup | Pre-build the image or wait 60–120s |

### 8.2 Database Connection Failures

#### Symptom: API logs show `connection refused`

```bash
# Is the database container running?
docker compose ps db

# Can the API container reach the database?
docker compose exec api ping db

# Check database logs
docker compose logs db | tail -50
```

**Root causes:**
1. Database container not yet healthy — wait for startup period
2. Wrong hostname — use `db` (Docker service name), not `localhost`
3. Database port mapped differently — verify ports in compose file
4. PostgreSQL failed to start due to corrupted data — check logs

**Recovery:**
```bash
# Recreate database from scratch (WARNING: destroys all data)
docker compose down -v  # removes volumes including pgdata
docker compose up -d

# Or restore from backup
docker compose down
# Restore procedure — see Section 9
```

#### Symptom: `remaining connection slots are reserved`

The connection pool is exhausted. Either increase the pool size or add PgBonger (see Section 6.2).

```bash
# Check current connections
docker compose exec db psql -U urja -c "SELECT count(*) FROM pg_stat_activity;"

# Kill idle connections (emergency)
docker compose exec db psql -U urja -c "
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE state = 'idle'
AND pid <> pg_backend_pid();
"
```

### 8.3 Redis Connection Issues

#### Symptom: ARQ tasks not processing

```bash
# Check Redis connectivity
docker compose exec api python -c "
import redis
r = redis.from_url('redis://:${REDIS_PASSWORD}@redis:6379/0')
print(r.ping())
"

# Check Redis container status
docker compose ps redis
docker compose logs redis

# Verify REDIS_URL in API container
docker compose exec api env | grep REDIS_URL
```

#### Symptom: Redis memory full

```bash
# Check Redis memory stats
docker compose exec redis redis-cli -a "$REDIS_PASSWORD" info memory

# Flush cache (if acceptable — does not affect persistent data)
docker compose exec redis redis-cli -a "$REDIS_PASSWORD" FLUSHDB

# Increase maxmemory in compose file
command: redis-server --requirepass ${REDIS_PASSWORD} --maxmemory 256mb
```

### 8.4 Frontend Build Failures

#### Symptom: Build fails during `docker compose up -d`

```bash
# Rebuild with verbose output
docker compose build --progress=plain frontend 2>&1 | tee frontend-build.log
```

**Common issues:**

| Error | Cause | Fix |
|-------|-------|-----|
| `Module not found: Can't resolve '...'` | Missing npm dependency | `npm install` locally, then rebuild |
| `Build optimization failed` | Out of memory during build | Increase Docker memory limits, or build on a larger machine |
| `Error: EACCES: permission denied` | File permission issues | Ensure `user: "1000:1000"` in compose file |
| `TypeError: Cannot read properties of undefined (reading '...')` | Missing environment variable | Check `NEXT_PUBLIC_*` env vars are set at build time |

**Tip:** Pre-build the frontend image in CI and push to a registry to avoid building on the server:

```yaml
services:
  frontend:
    image: yourregistry.com/urja-frontend:latest
    build:
      context: ./frontend
      dockerfile: Dockerfile
```

### 8.5 Permissions Problems

#### Symptom: Permission denied on volume mounts

```bash
# Fix pgdata directory permissions
sudo chown -R 999:999 /data/urja/postgres   # PostgreSQL UID
sudo chown -R 1000:1000 /data/urja/uploads   # API UID

# Check current ownership
ls -la /data/urja/
```

**Container UID mapping:**

| Service | UID | GID | Notes |
|---------|-----|-----|-------|
| db | 999 | 999 | PostgreSQL default |
| api | 1000 | 1000 | Non-root `urja` user |
| frontend | 1000 | 1000 | Non-root `node` user |
| redis | 999 | 999 | Redis alpine default |

#### Symptom: Cannot run Docker commands without sudo

```bash
# Add your user to the docker group
sudo usermod -aG docker $USER

# Log out and back in, or run:
newgrp docker
```

### 8.6 arm64 / Raspberry Pi Notes

URJA supports arm64. Everything works on Raspberry Pi 4+ (4 GB RAM minimum).

```bash
# On Raspberry Pi OS (64-bit), run:
docker compose up -d

# Note: TimescaleDB arm64 image is available as
# timescale/timescaledb:2.17-pg16-arm64
```

**Known differences:**
- Build times are ~3× longer on Raspberry Pi (compilation-based packages)
- Do not run the TUI container on a Pi with less than 4 GB RAM
- Use `--platform linux/arm64` explicitly if pulling from a multi-arch registry

### 8.7 Quick Diagnostic Commands

```bash
# Complete health check
echo "=== Containers ===" && docker compose ps && \
echo "=== Disk Usage ===" && df -h /data/urja && \
echo "=== API Health ===" && curl -f http://localhost:8000/health && \
echo "=== DB Size ===" && docker compose exec db psql -U urja -c "
    SELECT pg_size_pretty(pg_database_size('urja'));" && \
echo "=== Redis ===" && docker compose exec redis redis-cli -a "$REDIS_PASSWORD" ping && \
echo "=== Frontend ===" && curl -f -o /dev/null -s -w "%{http_code}" http://localhost:3000

# Network connectivity test
docker compose run --rm api sh -c "ping -c 1 db && ping -c 1 redis"

# Resource usage
docker stats --no-stream
```

---

## 9. Backup & Disaster Recovery

### 9.1 Database Backup Commands

#### Full backup (pg_dump — recommended)

```bash
# Custom format (compressed, restorable selectively)
docker exec urja-db pg_dump \
    --username=urja \
    --dbname=urja \
    --format=custom \
    --compress=9 \
    --file=/tmp/urja_full.dump \
    --no-owner \
    --no-privileges

docker cp urja-db:/tmp/urja_full.dump ./backups/urja_$(date +%Y%m%d).dump
docker exec urja-db rm /tmp/urja_full.dump
```

#### Schema-only backup

```bash
docker exec urja-db pg_dump \
    --username=urja \
    --dbname=urja \
    --schema-only \
    --file=/tmp/urja_schema.sql \
    --no-owner \
    --no-privileges
```

#### Data-only backup (all tables)

```bash
docker exec urja-db pg_dump \
    --username=urja \
    --dbname=urja \
    --data-only \
    --format=custom \
    --compress=9 \
    --file=/tmp/urja_data.dump
```

#### Single table backup

```bash
docker exec urja-db pg_dump \
    --username=urja \
    --dbname=urja \
    --table=telemetry_generation \
    --format=custom \
    --compress=9 \
    --file=/tmp/telemetry_backup.dump
```

### 9.2 Automated Backup Script

Save this as `/usr/local/bin/urja-backup.sh` and make it executable:

```bash
#!/bin/bash
# ──────────────────────────────────────────────────────────────────────────
# URJA — Automated Database Backup Script
# ──────────────────────────────────────────────────────────────────────────
# Installed at: /usr/local/bin/urja-backup.sh
# Cron: 0 2 * * * /usr/local/bin/urja-backup.sh >> /var/log/urja-backup.log 2>&1
# ──────────────────────────────────────────────────────────────────────────

set -euo pipefail

# ── Configuration ─────────────────────────────────────────────────────────
BACKUP_DIR="${BACKUP_DIR:-/var/backups/urja}"
DB_CONTAINER="${DB_CONTAINER:-urja-db}"
DB_USER="${DB_USER:-urja}"
DB_NAME="${DB_NAME:-urja}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
LOCK_FILE="${BACKUP_DIR}/.backup.lock"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/urja_${TIMESTAMP}.dump"
LOG_FILE="${BACKUP_DIR}/backup.log"

# ── Functions ─────────────────────────────────────────────────────────────

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

cleanup() {
    rm -f "$LOCK_FILE"
    log "Lock released."
}

# ── Main ──────────────────────────────────────────────────────────────────

# Prevent concurrent runs
if [ -f "$LOCK_FILE" ]; then
    log "ERROR: Another backup is running (lock file exists). Exiting."
    exit 1
fi
touch "$LOCK_FILE"
trap cleanup EXIT

mkdir -p "$BACKUP_DIR"
log "Starting backup: ${BACKUP_FILE}"

# Step 1: Verify database container is running
if ! docker ps --format '{{.Names}}' | grep -q "^${DB_CONTAINER}$"; then
    log "ERROR: Database container '${DB_CONTAINER}' is not running."
    exit 1
fi

# Step 2: Run pg_dump inside the container
if docker exec "$DB_CONTAINER" pg_dump \
    --username="$DB_USER" \
    --dbname="$DB_NAME" \
    --format=custom \
    --compress=9 \
    --file="/tmp/urja_backup.dump" \
    --no-owner \
    --no-privileges; then
    log "pg_dump completed successfully."
else
    log "ERROR: pg_dump failed."
    exit 1
fi

# Step 3: Copy backup out of container
if docker cp "${DB_CONTAINER}:/tmp/urja_backup.dump" "$BACKUP_FILE"; then
    log "Backup copied to ${BACKUP_FILE}"
else
    log "ERROR: Failed to copy backup from container."
    exit 1
fi

# Step 4: Clean up inside container
docker exec "$DB_CONTAINER" rm /tmp/urja_backup.dump

# Step 5: Verify backup integrity
if pg_restore --list "$BACKUP_FILE" > /dev/null 2>&1; then
    BACKUP_SIZE=$(stat -c%s "$BACKUP_FILE")
    log "Backup verified: $(numfmt --to=iec $BACKUP_SIZE)"
else
    log "ERROR: Backup file is corrupted!"
    rm -f "$BACKUP_FILE"
    exit 1
fi

# Step 6: Remove backups older than retention period
find "$BACKUP_DIR" -name "urja_*.dump" -mtime "+$RETENTION_DAYS" -delete
log "Cleaned up backups older than ${RETENTION_DAYS} days."

# Step 7: Sync to off-site storage (optional)
if [ -n "${RCLONE_REMOTE:-}" ]; then
    if rclone sync "$BACKUP_DIR" "${RCLONE_REMOTE}:urja-backups/" 2>/dev/null; then
        log "Off-site sync completed."
    else
        log "WARNING: Off-site sync failed."
    fi
fi

log "Backup complete: ${BACKUP_FILE}"
```

**Installation:**

```bash
sudo cp urja-backup.sh /usr/local/bin/
sudo chmod +x /usr/local/bin/urja-backup.sh

# Add to crontab (runs daily at 2:00 AM)
(crontab -l 2>/dev/null; echo "0 2 * * * /usr/local/bin/urja-backup.sh >> /var/log/urja-backup.log 2>&1") | crontab -
```

### 9.3 Restore Procedure

#### Full restore from custom format dump

```bash
#!/bin/bash
# urja-restore.sh — Restore URJA database from a pg_dump custom format file
# Usage: ./urja-restore.sh /path/to/backup.dump

set -euo pipefail

BACKUP_FILE="${1:-}"
DB_CONTAINER="${DB_CONTAINER:-urja-db}"
DB_USER="${DB_USER:-urja}"
DB_NAME="${DB_NAME:-urja}"

if [ -z "$BACKUP_FILE" ] || [ ! -f "$BACKUP_FILE" ]; then
    echo "Usage: $0 <path-to-backup.dump>"
    exit 1
fi

echo "=== URJA Database Restore ==="
echo "Backup file: $BACKUP_FILE"
echo "Container:   $DB_CONTAINER"
echo "Database:    $DB_NAME"
echo ""

# Step 1: Confirm
echo "WARNING: This will REPLACE all data in the $DB_NAME database."
read -p "Are you sure? (yes/NO): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    echo "Restore cancelled."
    exit 0
fi

# Step 2: Verify the dump file
echo "[1/5] Verifying backup file integrity..."
pg_restore --list "$BACKUP_FILE" > /dev/null 2>&1 || {
    echo "ERROR: Backup file is corrupted or invalid."
    exit 1
}

# Step 3: Copy dump into container
echo "[2/5] Copying backup into container..."
docker cp "$BACKUP_FILE" "${DB_CONTAINER}:/tmp/urja_restore.dump"

# Step 4: Drop and recreate the database
echo "[3/5] Dropping existing database..."
docker exec "$DB_CONTAINER" psql -U "$DB_USER" -c "DROP DATABASE IF EXISTS ${DB_NAME};"

echo "[4/5] Creating fresh database..."
docker exec "$DB_CONTAINER" psql -U "$DB_USER" -c "CREATE DATABASE ${DB_NAME} OWNER ${DB_USER};"

# Re-enable TimescaleDB on the fresh database
docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -c "CREATE EXTENSION IF NOT EXISTS timescaledb;"

# Step 5: Restore from dump
echo "[5/5] Restoring data (this may take a while)..."
docker exec "$DB_CONTAINER" pg_restore \
    --username="$DB_USER" \
    --dbname="$DB_NAME" \
    --no-owner \
    --no-privileges \
    --exit-on-error \
    --jobs=4 \
    /tmp/urja_restore.dump

# Clean up
docker exec "$DB_CONTAINER" rm /tmp/urja_restore.dump

echo ""
echo "=== Restore complete ==="
echo "Restart the API container to pick up the restored database:"
echo "  docker compose restart api"
```

**Restore with downtime minimization:**

```bash
# 1. Stop the API and workers (data stops flowing, but frontend can remain up)
docker compose stop api

# 2. Run restore
./urja-restore.sh /var/backups/urja/urja_20260722_020000.dump

# 3. Restart everything
docker compose up -d
```

#### Point-in-Time Recovery (if WAL archiving is configured)

```bash
# 1. Restore the base backup
# 2. Configure recovery.conf with the archive location and target time
# 3. Start PostgreSQL in recovery mode
```

### 9.4 Off-Site Backup Recommendations

| Service | Free Tier | Paid Tier | Setup Complexity |
|---------|-----------|-----------|------------------|
| **Backblaze B2** | 10 GB | $0.006/GB/month | Low (rclone) |
| **AWS S3** | 5 GB (12 months) | $0.023/GB/month | Medium (aws-cli) |
| **Google Cloud Storage** | 5 GB | $0.020/GB/month | Medium (gsutil) |
| **rsync.net** | None | $0.02/GB/month | Low (rsync/ssh) |
| **Wasabi** | None | $0.0059/GB/month (no egress) | Low (rclone) |

**rclone configuration example (Backblaze B2):**

```bash
# Install rclone
sudo apt install rclone

# Configure (interactive)
rclone config

# Sync backups to B2
rclone sync /var/backups/urja remote:bucket-name/urja-backups/

# Add to cron for daily off-site sync
# 0 4 * * * rclone sync /var/backups/urja remote:bucket-name/urja-backups/
```

### 9.5 Disaster Recovery Plan

**Situation:** Complete server failure (hardware, OS corruption, or datacenter outage).

**Recovery time objective (RTO):** 2 hours (with backups available)
**Recovery point objective (RPO):** 24 hours (with daily backups)

**Step-by-step recovery:**

```bash
# On a new server:

# 1. Install Docker and Docker Compose
sudo apt update && sudo apt install -y docker.io docker-compose-v2

# 2. Clone the repository
git clone https://github.com/ravikumarve/URJA.git
cd URJA

# 3. Restore .env file from your secret store
# (password manager, vault, or encrypted file)

# 4. Restore data volumes
mkdir -p /data/urja/postgres /data/urja/redis /data/urja/uploads

# If you have a full /data/urja backup:
rsync -avz user@backup-server:/backups/urja/data/ /data/urja/

# Otherwise, restore from a pg_dump:
# 5a. Start only the database
docker compose up -d db

# 5b. Wait for database to be ready
docker compose exec db pg_isready -U urja

# 5c. Restore from backup
./urja-restore.sh /path/to/downloaded/backup.dump

# 5d. Start remaining services
docker compose up -d

# 6. Verify
curl -f http://localhost:8000/health && curl -f http://localhost:3000

# 7. Point DNS to the new server
# 8. Renew TLS certificates if needed
```

**Recovery checklist:**

- [ ] Server provisioned with Docker installed
- [ ] Repository cloned
- [ ] `.env` restored from secure storage
- [ ] Database backup available (local copy or downloaded from off-site)
- [ ] Data volumes restored (or database restored from dump)
- [ ] All containers started and healthy
- [ ] DNS updated
- [ ] TLS certificates renewed
- [ ] Backup schedule re-established on new server
- [ ] Monitoring and alerting re-configured

---

## Appendix A: Docker & System Commands Reference

### Container Management

```bash
# Start all services
docker compose up -d

# Stop all services
docker compose down

# Stop all services AND delete volumes (WARNING: destroys data)
docker compose down -v

# Restart a single service
docker compose restart api

# View logs
docker compose logs -f
docker compose logs -f --tail=100 api

# Rebuild a single service
docker compose build --no-cache api

# Rebuild and restart
docker compose up -d --build api

# Execute command in running container
docker compose exec api alembic upgrade head
docker compose exec db psql -U urja

# Scale API workers (experimental)
docker compose up -d --scale api=2
```

### Monitoring

```bash
# View resource usage
docker stats

# View container details
docker inspect urja-api

# Check disk usage of Docker
docker system df

# Prune unused resources
docker system prune -f
```

### Database

```bash
# Connect to PostgreSQL
docker compose exec db psql -U urja

# List databases
docker compose exec db psql -U urja -c "\l"

# List tables
docker compose exec db psql -U urja -d urja -c "\dt"

# Query size of database
docker compose exec db psql -U urja -d urja -c "
SELECT pg_size_pretty(pg_database_size('urja'));
"

# Kill all connections (useful before restore)
docker compose exec db psql -U urja -c "
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = 'urja' AND pid <> pg_backend_pid();
"
```

### Redis

```bash
# Connect to Redis CLI
docker compose exec redis redis-cli -a "$REDIS_PASSWORD"

# Monitor commands in real-time
docker compose exec redis redis-cli -a "$REDIS_PASSWORD" MONITOR

# Check memory
docker compose exec redis redis-cli -a "$REDIS_PASSWORD" INFO memory

# List queue sizes
docker compose exec redis redis-cli -a "$REDIS_PASSWORD" LLEN arq:queue
```

---

## Appendix B: Related Documents

| Document | Description |
|----------|-------------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | System architecture, C4 diagrams, container specs, ADRs |
| [SECURITY.md](SECURITY.md) | Security architecture, secrets management, hardening checklist |
| [DATABASE.md](DATABASE.md) | Database schema, TimescaleDB hypertables, backup strategy |
| [API-SPEC.md](API-SPEC.md) | API contract, authentication flows, rate limits |
| [PRD.md](../product/PRD.md) | Product requirements document |
| [ADRS.md](ADRS.md) | Architecture Decision Records |

---

*DEPLOYMENT.md v1.0 — Review this document before every major deployment. Infrastructure changes. Backups fail. TLS certificates expire. This document is your operations manual; keep it updated.*
