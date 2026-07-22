# URJA — Configuration Reference

**Version**: 1.0
**Last Updated**: 2026-07-22
**Applies To**: URJA Boilerplate v1 — FastAPI + Next.js 16 + TimescaleDB + Redis 7 + Textual TUI

> Complete reference for all environment variables, settings, and configuration options. Use this as a searchable API reference when deploying, tuning, or troubleshooting URJA.

---

## Table of Contents

1. [Environment Variables](#1-environment-variables)
   - [Database](#11-database)
   - [Redis](#12-redis)
   - [Authentication & JWT](#13-authentication--jwt)
   - [API (Backend)](#14-api-backend)
   - [External Integrations](#15-external-integrations)
   - [Email (SMTP)](#16-email-smtp)
   - [Frontend (Next.js)](#17-frontend-nextjs)
   - [TUI (Textual)](#18-tui-textual)
   - [Carbon Module](#19-carbon-module)
   - [Health Module](#110-health-module)
   - [Logging](#111-logging)
2. [Docker Compose Configuration](#2-docker-compose-configuration)
   - [Service Environment Mapping](#21-service-environment-mapping)
   - [Volume Mounts](#22-volume-mounts)
   - [Port Mappings](#23-port-mappings)
   - [Resource Limits](#24-resource-limits)
   - [Health Checks](#25-health-checks)
   - [Network Configuration](#26-network-configuration)
   - [Docker Compose Profiles](#27-docker-compose-profiles)
3. [Application-Level Configuration (Pydantic Settings)](#3-application-level-configuration-pydantic-settings)
   - [Database Settings](#31-database-settings)
   - [API Settings](#32-api-settings)
   - [Carbon Settings](#33-carbon-settings)
   - [Health Settings](#34-health-settings)
   - [Telemetry Settings](#35-telemetry-settings)
   - [Task Queue (ARQ) Settings](#36-task-queue-arq-settings)
4. [TimescaleDB Configuration](#4-timescaledb-configuration)
   - [Hypertable Chunk Intervals](#41-hypertable-chunk-intervals)
   - [Compression Policies](#42-compression-policies)
   - [Retention Policies](#43-retention-policies)
   - [Continuous Aggregate Refresh Intervals](#44-continuous-aggregate-refresh-intervals)
5. [Seed Data Configuration](#5-seed-data-configuration)
   - [Default 50MW Farm Profile](#51-default-50mw-farm-profile)
   - [Customization Guide](#52-customization-guide)
   - [Multi-Scenario Seeds](#53-multi-scenario-seeds)
6. [Logging & Monitoring](#6-logging--monitoring)
   - [Log Levels Per Service](#61-log-levels-per-service)
   - [Log Format](#62-log-format)
   - [Health Check Endpoints](#63-health-check-endpoints)
   - [Metrics Endpoints](#64-metrics-endpoints)
7. [Email Configuration](#7-email-configuration)
   - [SMTP Settings](#71-smtp-settings)
   - [Alert Notification Templates](#72-alert-notification-templates)
   - [Report Delivery Configuration](#73-report-delivery-configuration)
8. [Production Overrides](#8-production-overrides)

---

## 1. Environment Variables

### 1.1 Database

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `POSTGRES_DB` | Yes | `urja` | PostgreSQL database name |
| `POSTGRES_USER` | Yes | `urja` | PostgreSQL application user (runtime, no DDL) |
| `POSTGRES_PASSWORD` | Yes | — | PostgreSQL password. Generate: `openssl rand -base64 32` |
| `POSTGRES_HOST` | Yes | `db` | PostgreSQL hostname (Docker service name). Use `localhost` for native dev |
| `POSTGRES_PORT` | Yes | `5432` | PostgreSQL port |
| `DATABASE_URL` | Yes | — | Full asyncpg connection string. Auto-built from the above in `.env.example`. Pattern: `postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}` |
| `DATABASE_POOL_SIZE` | No | `10` | SQLAlchemy async connection pool size |
| `DATABASE_MAX_OVERFLOW` | No | `5` | Maximum overflow connections beyond pool size |
| `DATABASE_POOL_TIMEOUT` | No | `30` | Seconds to wait for a connection from the pool |
| `DATABASE_POOL_PRE_PING` | No | `true` | Verify connections before using them from the pool |
| `DATABASE_SSL_MODE` | No | `prefer` | SSL mode for database connection: `disable`, `prefer`, `require`, `verify-ca`, `verify-full` |
| `DATABASE_MIGRATION_USER` | No | `urja_migrate` | Separate database user for Alembic schema migrations (DDL privileges) |
| `DATABASE_MIGRATION_PASSWORD` | No | — | Password for migration user |
| `DATABASE_BACKUP_USER` | No | `urja_backup` | Read-only user for automated backups |

### 1.2 Redis

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `REDIS_URL` | Yes | `redis://:${REDIS_PASSWORD}@redis:6379/0` | Redis connection string. Pattern: `redis://[:password]@host:port/db` |
| `REDIS_PASSWORD` | Yes | — | Redis AUTH password. Generate: `openssl rand -base64 32` |
| `REDIS_MAX_MEMORY` | No | `128mb` | Redis maxmemory eviction threshold |
| `REDIS_MAX_MEMORY_POLICY` | No | `allkeys-lru` | Redis eviction policy when memory limit reached |
| `REDIS_APPENDONLY` | No | `yes` | Enable Redis AOF persistence: `yes` or `no` |
| `REDIS_APPENDFSYNC` | No | `everysec` | AOF fsync policy: `always`, `everysec`, `no` |
| `REDIS_CACHE_TTL` | No | `300` | Default cache TTL in seconds for API responses |
| `REDIS_DB_CACHE` | No | `1` | Redis DB index for cache (DB 0 is ARQ queue) |
| `REDIS_DB_ARQ` | No | `0` | Redis DB index for ARQ task queue |

### 1.3 Authentication & JWT

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `JWT_SECRET` | Yes | — | HS256 signing key for JWT tokens. Generate: `openssl rand -base64 48`. Minimum 256-bit entropy |
| `JWT_ALGORITHM` | No | `HS256` | JWT signing algorithm |
| `JWT_ACCESS_EXPIRE_MINUTES` | No | `15` | Access token lifetime in minutes. Short TTL limits compromise window |
| `JWT_REFRESH_EXPIRE_DAYS` | No | `7` | Refresh token lifetime in days. Stored as httpOnly cookie |
| `JWT_REFRESH_SECRET` | No | Uses `JWT_SECRET` | Separate signing key for refresh tokens (optional defense-in-depth) |
| `JWT_ISSUER` | No | `urja` | JWT `iss` (issuer) claim value |
| `PASSWORD_BCRYPT_ROUNDS` | No | `12` | bcrypt cost factor for password hashing |
| `LOGIN_RATE_LIMIT_PER_MINUTE` | No | `5` | Max login attempts per IP per minute |
| `LOGIN_RATE_LIMIT_BURST` | No | `2` | Allowed burst above rate limit |
| `ACCOUNT_LOCKOUT_THRESHOLD` | No | `10` | Failed logins before account lockout |
| `ACCOUNT_LOCKOUT_DURATION_MINUTES` | No | `15` | Lockout duration in minutes |
| `PASSWORD_RESET_TOKEN_EXPIRE_HOURS` | No | `1` | Password reset token TTL in hours |

### 1.4 API (Backend)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `CORS_ORIGINS` | Yes | `http://localhost:3000` | Comma-separated list of allowed CORS origins. In production, set to exact frontend domain |
| `CORS_ALLOW_CREDENTIALS` | No | `true` | Allow cookies in CORS requests |
| `API_HOST` | No | `0.0.0.0` | FastAPI bind host |
| `API_PORT` | No | `8000` | FastAPI listen port |
| `API_WORKERS` | No | `1` | Number of Uvicorn workers (keep 1 for ARQ compatibility in single container) |
| `API_MAX_UPLOAD_SIZE_MB` | No | `10` | Maximum upload file size in MB |
| `RATE_LIMIT_AUTHENTICATED` | No | `300` | Requests per minute per authenticated user |
| `RATE_LIMIT_AUTHENTICATED_BURST` | No | `50` | Burst requests per minute |
| `RATE_LIMIT_API_KEY_READ` | No | `1000` | Requests per minute for read-only API keys |
| `RATE_LIMIT_API_KEY_WRITE` | No | `500` | Requests per minute for write-scoped API keys |
| `RATE_LIMIT_UNAUTHENTICATED` | No | `20` | Requests per minute for unauthenticated requests |
| `RATE_LIMIT_TELEMETRY_INGEST` | No | `10000` | Requests per minute for telemetry ingest endpoint |
| `TELEMETRY_BATCH_MAX_SIZE` | No | `1000` | Maximum telemetry records per batch ingest request |
| `DEFAULT_PAGE_SIZE` | No | `20` | Default pagination page size for list endpoints |
| `MAX_PAGE_SIZE` | No | `100` | Maximum allowed page size |
| `TZ` | No | `UTC` | Application timezone |

### 1.5 External Integrations

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `WEATHER_API_PROVIDER` | No | `openweather` | Weather data provider: `openweather`, `solcast`, `custom` |
| `WEATHER_API_KEY` | No | — | API key for weather data provider |
| `WEATHER_API_BASE_URL` | No | — | Custom base URL for weather API (if provider is `custom`) |
| `WEATHER_REFRESH_INTERVAL_HOURS` | No | `6` | How often to refresh weather forecast data |
| `GRID_PRICE_API_PROVIDER` | No | `epex` | Grid pricing provider: `epex`, `caiso`, `nordpool`, `custom` |
| `GRID_PRICE_API_KEY` | No | — | API key for grid pricing provider |
| `GRID_PRICE_API_BASE_URL` | No | — | Custom base URL for grid pricing API |
| `GRID_PRICE_REFRESH_INTERVAL_HOURS` | No | `1` | How often to refresh grid pricing data |
| `CARBON_REGISTRY_PROVIDER` | No | `verra` | Carbon registry provider: `verra`, `hedera`, `custom` |
| `CARBON_REGISTRY_API_KEY` | No | — | API key for carbon registry integration |
| `CARBON_REGISTRY_BASE_URL` | No | — | Custom base URL for carbon registry |
| `CARBON_REGISTRY_ORG_ID` | No | — | Organization identifier within the carbon registry |

### 1.6 Email (SMTP)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SMTP_HOST` | Conditional | — | SMTP server hostname. Required if email features (password reset, alerts, reports) are enabled |
| `SMTP_PORT` | No | `587` | SMTP server port: `25`, `465` (SSL), `587` (STARTTLS) |
| `SMTP_USER` | Conditional | — | SMTP authentication username |
| `SMTP_PASSWORD` | Conditional | — | SMTP authentication password |
| `SMTP_FROM_EMAIL` | Conditional | — | From: address for outgoing emails. E.g., `noreply@yourfarm.com` |
| `SMTP_FROM_NAME` | No | `URJA` | Display name for the From: field |
| `SMTP_USE_TLS` | No | `true` | Enable STARTTLS (port 587) |
| `SMTP_USE_SSL` | No | `false` | Enable SSL/TLS (port 465) |
| `SMTP_TIMEOUT` | No | `30` | SMTP connection timeout in seconds |
| `EMAIL_ALERTS_ENABLED` | No | `true` | Enable email alert notifications |
| `EMAIL_REPORTS_ENABLED` | No | `true` | Enable email report delivery |
| `EMAIL_REPORT_SCHEDULE_CRON` | No | `0 8 * * 1` | Cron expression for weekly ESG report email |

### 1.7 Frontend (Next.js)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `NEXT_PUBLIC_API_URL` | Yes | `http://api:8000/api/v1` | API base URL as accessible from the browser. In production: `https://api.yourfarm.com/api/v1` |
| `NEXT_PUBLIC_MAP_TILE_URL` | No | `https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png` | Leaflet tile layer URL template |
| `NEXT_PUBLIC_MAP_ATTRIBUTION` | No | `&copy; OpenStreetMap contributors` | Leaflet attribution string |
| `NEXT_PUBLIC_DEFAULT_CENTER_LAT` | No | `20.0` | Default map center latitude |
| `NEXT_PUBLIC_DEFAULT_CENTER_LNG` | No | `78.0` | Default map center longitude |
| `NEXT_PUBLIC_DEFAULT_ZOOM` | No | `5` | Default map zoom level |
| `NEXT_PUBLIC_POLL_INTERVAL_MS` | No | `15000` | Dashboard data refresh interval in milliseconds |
| `NEXT_PUBLIC_APP_NAME` | No | `URJA` | Application name displayed in UI |
| `NEXT_PUBLIC_PRIMARY_COLOR` | No | `#059669` | Brand primary color (hex) for theme customization |
| `NEXT_TELEMETRY_DISABLED` | No | `1` | Disable Next.js telemetry. Keep `1` for privacy |
| `NEXT_PUBLIC_CDN_ASSET_PREFIX` | No | — | CDN URL prefix for static assets (if using CDN) |

### 1.8 TUI (Textual)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `URJA_API_URL` | Yes | `http://api:8000/api/v1` | API base URL for TUI container |
| `URJA_POLL_INTERVAL` | No | `15` | TUI data polling interval in seconds |
| `URJA_AUTH_TOKEN` | No | — | Pre-authenticated API token for TUI (avoids login prompt) |
| `URJA_THEME` | No | `dark` | TUI color theme: `dark`, `light`, `high-contrast` |
| `URJA_LOG_LEVEL` | No | `INFO` | TUI-specific log level (separate from API) |

### 1.9 Carbon Module

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `CARBON_MRV_METHODOLOGY` | No | `IPMVP_v2.1` | Carbon MRV methodology version. Tracks which calculation standard was used |
| `CARBON_DEFAULT_EMISSION_FACTOR` | No | `0.85` | Default grid emission factor (tCO₂e/MWh). Used when per-region factor is not configured |
| `CARBON_EMISSION_FACTOR_SOURCE` | No | `iea` | Emission factor data source: `iea`, `eia`, `manual` |
| `CARBON_CREDIT_MIN_KWH` | No | `1000` | Minimum generation (kWh) required to issue a single carbon credit |
| `CARBON_IDEMPOTENCY_TTL_HOURS` | No | `24` | How long idempotency keys are stored for carbon mint operations |
| `CARBON_AUDIT_TRAIL_ENABLED` | No | `true` | Enable blockchain/compatible audit trail push |
| `CARBON_VERIFICATION_REQUIRED` | No | `true` | Require external verification step before credits become active |
| `CARBON_MAX_CREDIT_ISSUANCE_BATCH` | No | `100` | Maximum credits issuable in a single batch operation |

### 1.10 Health Module

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `HEALTH_ANOMALY_ZSCORE_THRESHOLD` | No | `2.0` | Z-score threshold for warning-level anomaly detection |
| `HEALTH_ANOMALY_ZSCORE_CRITICAL` | No | `3.0` | Z-score threshold for critical-level anomaly detection |
| `HEALTH_SCAN_INTERVAL_MINUTES` | No | `15` | Health scan background task interval in minutes |
| `HEALTH_SCORE_WINDOW_HOURS` | No | `24` | Lookback window for health score computation (hours) |
| `HEALTH_MAINTENANCE_THRESHOLD` | No | `40` | Health score below which maintenance work orders are auto-generated (0–100) |
| `HEALTH_ALERT_RETENTION_DAYS` | No | `365` | Days to retain resolved alerts |
| `HEALTH_MAX_ALERTS_PER_ASSET` | No | `50` | Maximum concurrent active alerts per asset |
| `HEALTH_ANOMALY_DETECTION_METHOD` | No | `zscore` | Detection method: `zscore`, `iqr`, `mad`. Pro tier adds `lstm` and `xgboost` |

### 1.11 Logging

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `LOG_LEVEL` | No | `INFO` | Python logging level: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |
| `LOG_FORMAT` | No | `json` | Log output format: `json` (structured), `text` (human-readable) |
| `LOG_INCLUDE_TRACEBACK` | No | `true` | Include full traceback in error-level logs |
| `LOG_REDACT_SECRETS` | No | `true` | Redact sensitive values (passwords, tokens, API keys) from log output |
| `LOG_SHIPPING_ENABLED` | No | `false` | Enable external log shipping |
| `LOG_SHIPPING_ENDPOINT` | No | — | Log shipping endpoint URL (Loki, Datadog, etc.) |
| `LOG_SHIPPING_TOKEN` | No | — | Log shipping authentication token |
| `AUDIT_LOG_RETENTION_DAYS` | No | `365` | Application-level audit log retention (database audit_log table is permanent) |
| `METRICS_ENABLED` | No | `false` | Enable Prometheus metrics endpoint at `/metrics` |

---

## 2. Docker Compose Configuration

### 2.1 Service Environment Mapping

| Service | Environment Variable | Source (`.env`) | Default |
|---------|---------------------|-----------------|---------|
| **db** | `POSTGRES_DB` | `POSTGRES_DB` | `urja` |
| | `POSTGRES_USER` | `POSTGRES_USER` | `urja` |
| | `POSTGRES_PASSWORD` | `POSTGRES_PASSWORD` | *(required)* |
| **redis** | `REDIS_PASSWORD` | `REDIS_PASSWORD` | *(required)* |
| | *(all redis-server flags passed via `command:`)* | | |
| **api** | `DATABASE_URL` | `DATABASE_URL` | auto-built |
| | `REDIS_URL` | `REDIS_URL` | auto-built |
| | `JWT_SECRET` | `JWT_SECRET` | *(required)* |
| | `JWT_ACCESS_EXPIRE_MINUTES` | `JWT_ACCESS_EXPIRE_MINUTES` | `15` |
| | `JWT_REFRESH_EXPIRE_DAYS` | `JWT_REFRESH_EXPIRE_DAYS` | `7` |
| | `CORS_ORIGINS` | `CORS_ORIGINS` | `http://localhost:3000` |
| | `LOG_LEVEL` | `LOG_LEVEL` | `INFO` |
| | `WEATHER_API_KEY` | `WEATHER_API_KEY` | *(empty)* |
| | `GRID_PRICE_API_KEY` | `GRID_PRICE_API_KEY` | *(empty)* |
| | `CARBON_REGISTRY_API_KEY` | `CARBON_REGISTRY_API_KEY` | *(empty)* |
| | `SMTP_HOST` | `SMTP_HOST` | *(empty)* |
| | `SMTP_PORT` | `SMTP_PORT` | `587` |
| | `SMTP_USER` | `SMTP_USER` | *(empty)* |
| | `SMTP_PASSWORD` | `SMTP_PASSWORD` | *(empty)* |
| | `SMTP_FROM_EMAIL` | `SMTP_FROM_EMAIL` | *(empty)* |
| **frontend** | `NEXT_PUBLIC_API_URL` | `NEXT_PUBLIC_API_URL` | `http://api:8000/api/v1` |
| | `NEXT_PUBLIC_MAP_TILE_URL` | `NEXT_PUBLIC_MAP_TILE_URL` | OpenStreetMap default |
| | `NEXT_TELEMETRY_DISABLED` | *(hardcoded)* | `1` |
| **tui** | `URJA_API_URL` | `URJA_API_URL` | `http://api:8000/api/v1` |
| | `URJA_POLL_INTERVAL` | `URJA_POLL_INTERVAL` | `15` |

### 2.2 Volume Mounts

| Volume Name | Container Path | Service | Purpose | Backup Required |
|-------------|---------------|---------|---------|-----------------|
| `pgdata` | `/var/lib/postgresql/data` | db | Persistent PostgreSQL data directory | ✅ Critical |
| `redisdata` | `/data` | redis | Redis RDB/AOF persistence | ❌ Repopulated |
| `api_uploads` | `/app/uploads` | api | User-uploaded files (branding, ESG reports) | ⚠️ Optional |
| *(bind mount)* | `/var/lib/postgresql/data/wal_archive` | db | WAL archive for point-in-time recovery | ✅ If configured |

**Production bind-mount recommendation:**
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

### 2.3 Port Mappings

| Service | Internal Port | Host Mapping | Exposure | Notes |
|---------|--------------|--------------|----------|-------|
| **db** | `5432` | `127.0.0.1:5432` | Internal (Docker network) | Remove host mapping in production |
| **redis** | `6379` | `127.0.0.1:6379` | Internal (Docker network) | Remove host mapping in production |
| **api** | `8000` | `127.0.0.1:8000` | Internal (Docker DNS: `http://api:8000`) | Frontend + TUI access via Docker DNS |
| **frontend** | `3000` | `0.0.0.0:3000` | Host-facing | Only service exposed to internet (behind reverse proxy) |
| **tui** | `8080` | `0.0.0.0:8080` | Optional host-facing | Disabled by default (behind profile) |

### 2.4 Resource Limits

| Service | CPU Limit | Memory Limit | CPU Reservation | Memory Reservation |
|---------|-----------|-------------|-----------------|-------------------|
| **db** | 2 cores | 1 GB | 0.5 cores | 512 MB |
| **redis** | 0.5 cores | 128 MB | 0.1 cores | 64 MB |
| **api** | 2 cores | 512 MB | 0.25 cores | 256 MB |
| **frontend** | 1 core | 256 MB | 0.25 cores | 128 MB |
| **tui** | 0.5 cores | 128 MB | 0.1 cores | 64 MB |

**Total minimum:** ~1 GB RAM / **Total recommended:** ~2 GB RAM

### 2.5 Health Checks

| Service | Test Command | Interval | Timeout | Retries | Start Period |
|---------|-------------|----------|---------|---------|--------------|
| **db** | `pg_isready -U ${POSTGRES_USER}` | 10s | 5s | 5 | 60s |
| **redis** | `redis-cli -a ${REDIS_PASSWORD} ping` | 10s | 3s | 5 | 10s |
| **api** | `curl -f http://localhost:8000/health` | 15s | 5s | 3 | 30s |
| **frontend** | `curl -f http://localhost:3000` | 15s | 5s | 3 | 120s |
| **tui** | N/A (best-effort, optional service) | — | — | — | — |

A service is marked `unhealthy` after 3 consecutive failed health checks.

### 2.6 Network Configuration

```
Docker Network: urja_network (bridge, 172.20.0.0/16)
    │
    ├── api:8000       (internal — http://api:8000)
    ├── frontend:3000  (host-facing → reverse proxy)
    ├── db:5432        (internal — postgresql://db:5432)
    ├── redis:6379     (internal — redis://redis:6379)
    └── tui:8080       (optional, host-facing)
```

**Service startup order:**
```
db (healthy) ──┐
               ├──▶ api (healthy) ──▶ frontend (healthy)
redis (healthy)┘                    └──▶ tui (optional)
```

### 2.7 Docker Compose Profiles

| Profile | Services Included | Command |
|---------|------------------|---------|
| *(default)* | db, redis, api, frontend | `docker compose up -d` |
| `tui` | + tui | `docker compose --profile tui up -d` |
| `monitoring` | + prometheus, grafana, loki, promtail | `docker compose --profile monitoring up -d` |
| `development` | + all debug tools | `docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d` |

---

## 3. Application-Level Configuration (Pydantic Settings)

The following settings are defined in the backend's Pydantic `Settings` model (typically `backend/app/core/config.py`). These can be overridden via environment variables.

### 3.1 Database Settings

| Setting | Env Variable | Default | Description |
|---------|-------------|---------|-------------|
| `db_url` | `DATABASE_URL` | *(required)* | Async PostgreSQL connection string |
| `db_pool_size` | `DATABASE_POOL_SIZE` | `10` | Connection pool size (adjust with PgBouncer: set to `5`) |
| `db_max_overflow` | `DATABASE_MAX_OVERFLOW` | `5` | Additional connections beyond pool_size |
| `db_pool_timeout` | `DATABASE_POOL_TIMEOUT` | `30` | Seconds to wait for pool connection |
| `db_pool_pre_ping` | `DATABASE_POOL_PRE_PING` | `True` | Verify connection before use |
| `db_ssl_mode` | `DATABASE_SSL_MODE` | `prefer` | PostgreSQL SSL mode |
| `db_echo` | *(dev only)* | `False` | Log all SQL statements (development only) |

**PgBouncer-compatible pool settings:**
```python
engine = create_async_engine(
    DATABASE_URL,
    pool_size=5,        # Smaller than PgBouncer's DEFAULT_POOL_SIZE
    max_overflow=5,     # Allows burst but stays within PgBouncer limits
    pool_pre_ping=True,
)
```

### 3.2 API Settings

| Setting | Env Variable | Default | Description |
|---------|-------------|---------|-------------|
| `cors_origins` | `CORS_ORIGINS` | `["http://localhost:3000"]` | List of allowed CORS origins (comma-separated in env) |
| `cors_allow_credentials` | `CORS_ALLOW_CREDENTIALS` | `True` | Allow credentials in CORS |
| `api_host` | `API_HOST` | `0.0.0.0` | Bind address |
| `api_port` | `API_PORT` | `8000` | Listen port |
| `api_workers` | `API_WORKERS` | `1` | Uvicorn workers (keep 1 for single-container ARQ) |
| `max_upload_size` | `API_MAX_UPLOAD_SIZE_MB` | `10` | Max file upload in MB |
| `rate_limit_authenticated` | `RATE_LIMIT_AUTHENTICATED` | `300` | Requests/min for JWT-authenticated users |
| `rate_limit_unauthenticated` | `RATE_LIMIT_UNAUTHENTICATED` | `20` | Requests/min for anonymous requests |
| `rate_limit_telemetry_ingest` | `RATE_LIMIT_TELEMETRY_INGEST` | `10000` | Requests/min for telemetry ingest |
| `default_page_size` | `DEFAULT_PAGE_SIZE` | `20` | Default pagination limit |
| `max_page_size` | `MAX_PAGE_SIZE` | `100` | Maximum allowed page size |
| `app_timezone` | `TZ` | `UTC` | Application timezone |

### 3.3 Carbon Settings

| Setting | Env Variable | Default | Description |
|---------|-------------|---------|-------------|
| `mrv_methodology` | `CARBON_MRV_METHODOLOGY` | `IPMVP_v2.1` | Methodology identifier embedded in each credit audit trail |
| `default_emission_factor` | `CARBON_DEFAULT_EMISSION_FACTOR` | `0.85` | tCO₂e per MWh default grid emission factor |
| `credit_min_kwh` | `CARBON_CREDIT_MIN_KWH` | `1000` | Minimum kWh threshold for a single credit |
| `idempotency_ttl_hours` | `CARBON_IDEMPOTENCY_TTL_HOURS` | `24` | Idempotency key storage duration |
| `audit_trail_enabled` | `CARBON_AUDIT_TRAIL_ENABLED` | `True` | Enable Verra/Hedera audit trail push |
| `verification_required` | `CARBON_VERIFICATION_REQUIRED` | `True` | Require third-party verification before credit activation |
| `max_credit_batch` | `CARBON_MAX_CREDIT_ISSUANCE_BATCH` | `100` | Maximum credits per batch issuance |

**CO₂ equivalency formula:**
```
CO₂_eq (tCO₂e) = generation_kWh × emission_factor (tCO₂e/MWh) / 1000
```

### 3.4 Health Settings

| Setting | Env Variable | Default | Description |
|---------|-------------|---------|-------------|
| `anomaly_zscore_warning` | `HEALTH_ANOMALY_ZSCORE_THRESHOLD` | `2.0` | |z| > 2 flags warning |
| `anomaly_zscore_critical` | `HEALTH_ANOMALY_ZSCORE_CRITICAL` | `3.0` | |z| > 3 flags critical |
| `scan_interval_minutes` | `HEALTH_SCAN_INTERVAL_MINUTES` | `15` | Background scan interval |
| `score_window_hours` | `HEALTH_SCORE_WINDOW_HOURS` | `24` | Lookback window for scoring |
| `maintenance_threshold` | `HEALTH_MAINTENANCE_THRESHOLD` | `40` | Health score below threshold triggers work order (0–100) |
| `alert_retention_days` | `HEALTH_ALERT_RETENTION_DAYS` | `365` | Days before resolved alerts are pruned |
| `max_alerts_per_asset` | `HEALTH_MAX_ALERTS_PER_ASSET` | `50` | Max concurrent active alerts |
| `detection_method` | `HEALTH_ANOMALY_DETECTION_METHOD` | `zscore` | Statistical method for anomaly detection |

**Health score calculation:**
```
health_score = Σ(metric_score_i × weight_i) / Σ(weight_i)
  where metric_score_i = max(0, 100 - |z-score| × 25)  (clamped to 0–100)
```

### 3.5 Telemetry Settings

| Setting | Env Variable | Default | Description |
|---------|-------------|---------|-------------|
| `ingest_batch_max_size` | `TELEMETRY_BATCH_MAX_SIZE` | `1000` | Maximum records per batch ingest |
| `retention_days_raw` | *(configurable per deployment)* | `90` | Days to retain raw telemetry readings |
| `retention_days_hourly` | *(TimescaleDB policy)* | `365` | Days to retain hourly aggregates |
| `retention_days_daily` | *(TimescaleDB policy)* | `1825` | Days to retain daily aggregates (5 years) |
| `compression_policy_after_days` | *(TimescaleDB policy)* | `7` | Days after which to compress telemetry chunks |
| `curtailment_detection_window_minutes` | *(runtime config)* | `15` | Telemetry window for curtailment detection |
| `curtailment_confirmation_intervals` | *(runtime config)* | `3` | Consecutive windows needed to confirm curtailment |

### 3.6 Task Queue (ARQ) Settings

| Setting | Env Variable | Default | Description |
|---------|-------------|---------|-------------|
| `arq_redis_url` | `REDIS_URL` | *(from env)* | Redis connection for ARQ (uses DB 0) |
| `arq_queue_name` | — | `urja_tasks` | ARQ queue name |
| `arq_max_jobs` | — | `10` | Maximum concurrent jobs per worker |
| `arq_job_timeout_seconds` | — | `300` | Maximum job execution time before timeout (5 min) |
| `arq_keep_result_seconds` | — | `3600` | How long to keep completed job results (1 hour) |
| `arq_poll_interval_ms` | — | `1000` | How often the worker polls for new jobs |
| `arq_health_check_interval_s` | — | `30` | How often the worker sends a health check ping |

**Default ARQ cron schedule:**

| Task | Cron Expression | Interval | Description |
|-----|----------------|----------|-------------|
| `health_scan` | `*/15 * * * *` | Every 15 min | Anomaly detection, health scoring |
| `refresh_weather` | `0 */6 * * *` | Every 6 hours | Weather forecast refresh |
| `refresh_pricing` | `0 * * * *` | Every hour | Grid pricing refresh |
| `daily_rollup` | `0 0 * * *` | Daily at midnight | Continuous aggregate computation |

---

## 4. TimescaleDB Configuration

### 4.1 Hypertable Chunk Intervals

| Hypertable | Chunk Interval | Rationale |
|------------|---------------|-----------|
| `telemetry_readings` | 1 day | 50MW farm generates ~50K readings/day — 1-day chunks balance insert performance with query range scans |
| `telemetry_batches` | 7 days | Batch metadata is low-volume; weekly chunks reduce chunk count |
| `curtailment_events` | 7 days | Event-based table, moderate volume |
| `alerts` | 7 days | Alert data volume is moderate; 7-day chunks allow efficient recent-alert queries |
| `health_scores` | 7 days | Daily score snapshots; 7-day chunks |

**Set chunk interval:**
```sql
SELECT set_chunk_time_interval('telemetry_readings', INTERVAL '1 day');
```

### 4.2 Compression Policies

| Hypertable | Compress After | Compression Method | Segment By | Order By |
|------------|---------------|--------------------|------------|----------|
| `telemetry_readings` | 7 days | TimescaleDB native | `asset_id` | `ts DESC` |
| `telemetry_batches` | 30 days | TimescaleDB native | `status` | `created_at DESC` |
| `curtailment_events` | 30 days | TimescaleDB native | `asset_id` | `ts DESC` |
| `alerts` | 90 days | TimescaleDB native | `asset_id, status` | `created_at DESC` |
| `health_scores` | 90 days | TimescaleDB native | `asset_id` | `ts DESC` |

**Set compression policy:**
```sql
ALTER TABLE telemetry_readings SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'asset_id',
    timescaledb.compress_orderby = 'ts DESC'
);
SELECT add_compression_policy('telemetry_readings', INTERVAL '7 days');
```

### 4.3 Retention Policies

| Hypertable / View | Retention Period | Policy |
|-------------------|-----------------|--------|
| `telemetry_readings` (raw) | 90 days | Drop chunks older than 90 days |
| `telemetry_audit` | 365 days | Drop chunks older than 1 year |
| `aggregate_hourly` | 365 days | Drop chunks older than 1 year |
| `aggregate_daily` | 1825 days (5 years) | Drop chunks older than 5 years |
| `api_request_log` | 30 days | Drop chunks older than 30 days |

**Set retention policy:**
```sql
SELECT add_retention_policy('telemetry_readings', INTERVAL '90 days');
SELECT add_retention_policy('aggregate_hourly', INTERVAL '365 days');
SELECT add_retention_policy('aggregate_daily', INTERVAL '1825 days');
```

### 4.4 Continuous Aggregate Refresh Intervals

| Continuous Aggregate | Refresh Interval | Bucket Width | Refresh Lag |
|---------------------|-----------------|--------------|-------------|
| `aggregate_hourly` | Every 1 hour | 1 hour | 30 minutes (allows late-arriving data) |
| `aggregate_daily` | Every 1 day | 1 day | 2 hours (allows hourly rollup to complete) |

**Refresh policy SQL:**
```sql
CREATE MATERIALIZED VIEW aggregate_hourly
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', ts) AS bucket,
    asset_id,
    AVG(generation_kw) AS avg_generation_kw,
    SUM(generation_kwh) AS total_generation_kwh,
    MAX(generation_kw) AS peak_generation_kw,
    COUNT(*) AS reading_count
FROM telemetry_readings
GROUP BY bucket, asset_id
WITH NO DATA;

SELECT add_continuous_aggregate_policy('aggregate_hourly',
    start_offset => INTERVAL '3 days',
    end_offset => NULL,
    schedule_interval => INTERVAL '1 hour',
    initial_start => NULL,
    timezone => 'UTC'
);
```

---

## 5. Seed Data Configuration

### 5.1 Default 50MW Farm Profile

The seed script (`scripts/seed.py`) creates a complete 50MW solar farm for demonstration and evaluation:

| Parameter | Value | Description |
|-----------|-------|-------------|
| **Total capacity** | 50 MW | Nameplate capacity of the demonstration farm |
| **Assets** | 20 inverters | 20 × 2.5 MW inverters distributed across the farm |
| **Telemetry generation** | 14+ days | Synthetic 15-min interval telemetry with realistic diurnal patterns |
| **Curtailment events** | 3–5 events | Pre-seeded curtailment scenarios demonstrating revenue loss calculation |
| **Carbon credits** | 2–3 credits | Pre-seeded issued carbon credits with complete audit trail |
| **Health alerts** | 5–10 alerts | Mix of active and resolved alerts with varying severity |
| **Dispatch rules** | 3 rules | Default rules: battery charging, curtailment threshold, time-of-day pricing |
| **Users** | 3 users | `admin@urja.local` (admin), `operator@urja.local` (operator), `viewer@urja.local` (viewer) |
| **Default password** | `change-me-on-first-login` | All users. Prompts password change on first login |

### 5.2 Customization Guide

**Modify seed data for different scenarios:**

1. **Edit seed configuration** — `backend/scripts/seed_config.yaml` (or equivalent):
   ```yaml
   farm:
     name: "Custom Farm"
     total_capacity_mw: 100  # Change to your desired capacity
     asset_count: 40          # Number of assets to generate
     telemetry_days: 30       # Days of historical data
     telemetry_interval_min: 15

   curtailment:
     events: 10               # Number of seeded curtailment events
     min_duration_hours: 1
     max_duration_hours: 6
     revenue_per_mwh: 45      # Implied tariff rate for revenue calc

   carbon:
     credits: 5
     emission_factor: 0.85    # tCO2e/MWh

   weather:
     noise_factor: 0.15       # Random variation in irradiance (0=perfect, 1=chaotic)
     cloud_days: [3, 7, 12]   # Days to simulate cloud cover
   ```

2. **Run custom seed:**
   ```bash
   docker compose exec api python -m app.scripts.seed --config seed_config_custom.yaml
   ```

3. **Add multiple organizations:**
   ```bash
   docker compose exec api python -m app.scripts.seed --orgs 3
   ```

### 5.3 Multi-Scenario Seeds

| Scenario | Asset Count | Capacity | Telemetry Duration | Use Case |
|----------|------------|----------|-------------------|----------|
| **default** | 20 inverters | 50 MW | 14 days | Demo and evaluation |
| **small-farm** | 5 inverters | 10 MW | 30 days | Small installation, longer history |
| **large-farm** | 100 inverters | 250 MW | 7 days | High asset count, performance testing |
| **wind-farm** | 30 turbines | 75 MW | 14 days | Wind turbine profile with vibration data |
| **mixed-portfolio** | 30 solar + 15 wind | 100 MW | 30 days | Multi-technology demonstration |
| **curtailment-heavy** | 20 inverters | 50 MW | 30 days | Simulates aggressive grid curtailment |
| **degraded-health** | 20 inverters | 50 MW | 14 days | Multiple failing assets, alert display |

**Run a specific scenario:**
```bash
docker compose exec api python -m app.scripts.seed --scenario wind-farm
```

---

## 6. Logging & Monitoring

### 6.1 Log Levels Per Service

| Service | Default Level | File/Stream | Format |
|---------|--------------|-------------|--------|
| **api** | `INFO` | stdout/stderr (Docker) | JSON structured |
| **api (ARQ workers)** | `INFO` | stdout/stderr (same container) | JSON structured |
| **frontend** | *(Next.js built-in)* | stdout/stderr | Text |
| **tui** | `INFO` | stdout/stderr | Text |
| **db** | *(PostgreSQL default)* | stdout/stderr | Text |
| **redis** | *(notice)* | stdout/stderr | Text |

**Env variable configuration:**
```bash
LOG_LEVEL=INFO           # API and ARQ workers
URJA_LOG_LEVEL=INFO      # TUI-specific
```

### 6.2 Log Format

**JSON structured logging (default for API):**
```json
{
  "timestamp": "2026-07-22T14:30:00.123Z",
  "level": "INFO",
  "logger": "app.services.health_scorer",
  "message": "Health scan completed for asset inv_001",
  "extra": {
    "asset_id": "inv_001",
    "health_score": 87.5,
    "anomalies_found": 2,
    "scan_duration_ms": 145
  },
  "request_id": "req_abc123",
  "trace_id": "trace_xyz789"
}
```

**Fields included in every log line:**

| Field | Description | Always Present |
|-------|-------------|---------------|
| `timestamp` | ISO 8601 with milliseconds | Yes |
| `level` | Log level (uppercase) | Yes |
| `logger` | Python module path | Yes |
| `message` | Human-readable log message | Yes |
| `extra` | Structured context (varies by event) | No |
| `request_id` | Unique request identifier (API middleware) | For API requests |
| `trace_id` | Distributed trace identifier | If tracing enabled |
| `user_id` | Authenticated user identifier | For authenticated requests |
| `org_id` | Organization identifier | For authenticated requests |
| `duration_ms` | Request processing time | For API requests |
| `status_code` | HTTP response status | For API requests |

**Text format (alternative):**
```
[2026-07-22 14:30:00] INFO     app.services.health_scorer — Health scan completed for asset inv_001 (score=87.5, anomalies=2, duration=145ms)
```

### 6.3 Health Check Endpoints

| Endpoint | Method | Description | Response |
|----------|--------|-------------|----------|
| `/health` | GET | Comprehensive service health | `{"status": "ok", "version": "1.0.0", "checks": {"database": "connected", "redis": "connected", "uptime_seconds": 3600}}` |
| `/health/live` | GET | Liveness probe (Kubernetes-style) | `{"status": "ok"}` |
| `/health/ready` | GET | Readiness probe (Kubernetes-style) | `{"status": "ok", "checks": {...}}` |
| `/health/db` | GET | Database connectivity check | `{"status": "connected", "response_time_ms": 2}` |
| `/health/redis` | GET | Redis connectivity check | `{"status": "connected", "response_time_ms": 1}` |

**Docker Compose health check command:**
```yaml
test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
```

**Security note:** The `/health` endpoint returns connectivity status for dependencies only. It does NOT leak environment variables, configuration, database versions, or system details.

### 6.4 Metrics Endpoints

| Endpoint | Method | Description | Format |
|----------|--------|-------------|--------|
| `/metrics` | GET | Prometheus metrics | Prometheus text format |
| `/metrics/prometheus` | GET | Prometheus metrics (alternative path) | Prometheus text format |

**Available metrics (when `METRICS_ENABLED=true`):**

| Metric Name | Type | Labels | Description |
|-------------|------|--------|-------------|
| `urja_http_requests_total` | Counter | `method`, `endpoint`, `status` | Total HTTP requests |
| `urja_http_request_duration_seconds` | Histogram | `method`, `endpoint` | Request latency distribution |
| `urja_telemetry_ingested_total` | Counter | `asset_type` | Telemetry records ingested |
| `urja_telemetry_ingestion_duration_seconds` | Histogram | — | Telemetry ingestion latency |
| `urja_telemetry_rejected_total` | Counter | `reason` | Telemetry records rejected by validation |
| `urja_curtailment_events_total` | Counter | `asset_id` | Curtailment events detected |
| `urja_revenue_lost_total` | Counter | `asset_id` | Cumulative revenue lost in cents |
| `urja_carbon_credits_issued_total` | Counter | `methodology` | Carbon credits issued |
| `urja_carbon_credits_retired_total` | Counter | — | Carbon credits retired |
| `urja_health_scan_duration_seconds` | Histogram | — | Health scan processing time |
| `urja_alerts_active` | Gauge | `severity` | Currently active alerts |
| `urja_db_connection_pool_size` | Gauge | — | Current DB connection pool size |
| `urja_db_connection_pool_available` | Gauge | — | Available DB connections in pool |
| `urja_cache_hit_ratio` | Gauge | — | Redis cache hit ratio (0–1) |
| `urja_queue_depth` | Gauge | `queue` | ARQ queue depth |
| `urja_arq_job_duration_seconds` | Histogram | `task_name` | ARQ job processing time |
| `urja_arq_jobs_failed_total` | Counter | `task_name` | Failed ARQ jobs |

**Prometheus scrape configuration:**
```yaml
scrape_configs:
  - job_name: 'urja-api'
    static_configs:
      - targets: ['api:8000']
    metrics_path: '/metrics'
```

---

## 7. Email Configuration

### 7.1 SMTP Settings

URJA uses SMTP for transactional emails (password reset, user invitations) and optional periodic reports.

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SMTP_HOST` | Conditional | — | SMTP server hostname |
| `SMTP_PORT` | No | `587` | SMTP port |
| `SMTP_USER` | Conditional | — | SMTP username |
| `SMTP_PASSWORD` | Conditional | — | SMTP password |
| `SMTP_FROM_EMAIL` | Conditional | `noreply@yourfarm.com` | Sender email address |
| `SMTP_FROM_NAME` | No | `URJA` | Sender display name |
| `SMTP_USE_TLS` | No | `true` | Use STARTTLS (port 587) |
| `SMTP_USE_SSL` | No | `false` | Use SSL (port 465) |
| `SMTP_TIMEOUT` | No | `30` | Connection timeout in seconds |

**Supported providers:**

| Provider | SMTP Host | SMTP Port | TLS/SSL | Notes |
|----------|-----------|-----------|---------|-------|
| **SendGrid** | `smtp.sendgrid.net` | `587` | TLS | Use API key as password |
| **Mailgun** | `smtp.mailgun.org` | `587` | TLS | Use SMTP credentials |
| **Mailjet** | `in-v3.mailjet.com` | `587` | TLS | Use API key as username |
| **Amazon SES** | `email-smtp.region.amazonaws.com` | `587` | TLS | Requires SMTP credentials from IAM |
| **Postmark** | `smtp.postmarkapp.com` | `587` | TLS | Use server token as password |
| **Gmail SMTP** | `smtp.gmail.com` | `587` | TLS | Use app-specific password. Not recommended for production |
| **Custom SMTP** | *(your server)* | `25`/`465`/`587` | Configurable | For self-hosted mail servers |

### 7.2 Alert Notification Templates

Alert notifications are sent when health anomalies reach critical levels. Templates are stored in `backend/app/templates/email/`:

| Template | Trigger | Recipients | Variables |
|----------|---------|------------|-----------|
| `alert_critical.html` | Critical anomaly detected | org admins + operators | `{asset_name}`, `{metric}`, `{observed_value}`, `{expected_value}`, `{deviation_pct}`, `{alert_id}`, `{dashboard_url}` |
| `alert_warning.html` | Warning-level anomaly | org operators | Same as above |
| `alert_batch.html` | Daily digest of active alerts | org operators | `{alert_count}`, `{critical_count}`, `{warning_count}`, `{top_alerts[]}`, `{dashboard_url}` |
| `alert_maintenance.html` | Maintenance work order generated | org admins | `{asset_name}`, `{health_score}`, `{suggested_action}`, `{work_order_id}` |

**Template variable reference:**

| Variable | Description | Available In |
|----------|-------------|--------------|
| `{{ alert.asset_name }}` | Display name of the affected asset | All alert templates |
| `{{ alert.metric }}` | Metric that triggered the alert (e.g., `generation_kw`, `temperature_c`) | `alert_critical`, `alert_warning` |
| `{{ alert.observed_value }}` | Actual observed value | `alert_critical`, `alert_warning` |
| `{{ alert.expected_value }}` | Expected/mean value for the metric | `alert_critical`, `alert_warning` |
| `{{ alert.deviation_pct }}` | Deviation as percentage | `alert_critical`, `alert_warning` |
| `{{ alert.severity }}` | `critical` or `warning` | `alert_critical`, `alert_warning` |
| `{{ alert.created_at }}` | ISO 8601 timestamp | All alert templates |
| `{{ org.name }}` | Organization display name | All templates |
| `{{ dashboard_url }}` | Link to the dashboard | All templates |

**Customize templates:** Edit the `.html` files in `backend/app/templates/email/` and rebuild the API container.

### 7.3 Report Delivery Configuration

| Setting | Env Variable | Default | Description |
|---------|-------------|---------|-------------|
| `email_reports_enabled` | `EMAIL_REPORTS_ENABLED` | `true` | Enable periodic report delivery |
| `email_report_schedule_cron` | `EMAIL_REPORT_SCHEDULE_CRON` | `0 8 * * 1` | Cron expression (default: Monday 8 AM) |

**Supported report types:**

| Report | Schedule | Content | Format |
|--------|----------|---------|--------|
| **Weekly ESG Summary** | `0 8 * * 1` (Monday) | Generation totals, carbon credits issued, CO₂ avoided, revenue summary | PDF attachment |
| **Monthly Operations Report** | `0 8 1 * *` (1st of month) | Detailed generation analytics, curtailment summary, health trends, carbon portfolio | PDF attachment |
| **Curtailment Digest** | `0 8 * * 1` (Monday) | Revenue lost from curtailment, top events, trend comparison | PDF attachment |
| **Health Summary** | `0 8 * * *` (Daily) | Active alerts count, fleet health score average, maintenance recommendations | Inline HTML |

**ESG report signature:**
```
Signature = RSA-SHA256(report_content_hash, private_key)
```
The signature is embedded in the PDF metadata for tamper evidence. Verify via public key at `GET /api/v1/organization/public-key`.

---

## 8. Production Overrides

Use a production override file to adjust configuration without modifying the base `docker-compose.yml`:

```yaml
# docker-compose.prod.yml
services:
  api:
    environment:
      LOG_LEVEL: WARNING
      METRICS_ENABLED: "true"
      CORS_ORIGINS: https://dashboard.yourfarm.com

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
    command: redis-server --requirepass ${REDIS_PASSWORD} --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru
```

**Deploy with production overrides:**
```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

---

## Appendix: Quick Reference

### Secret Generation

```bash
# Generate all production secrets
POSTGRES_PASSWORD=$(openssl rand -base64 32)
REDIS_PASSWORD=$(openssl rand -base64 32)
JWT_SECRET=$(openssl rand -base64 48)

echo "POSTGRES_PASSWORD=$POSTGRES_PASSWORD"
echo "REDIS_PASSWORD=$REDIS_PASSWORD"
echo "JWT_SECRET=$JWT_SECRET"
```

### Minimum Viable `.env` (Development)

```bash
POSTGRES_PASSWORD=devpassword
REDIS_PASSWORD=devpassword
JWT_SECRET=dev-jwt-secret-min-32-chars-long
CORS_ORIGINS=http://localhost:3000
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

### Minimum Viable `.env` (Production)

```bash
POSTGRES_PASSWORD=<openssl rand -base64 32>
REDIS_PASSWORD=<openssl rand -base64 32>
JWT_SECRET=<openssl rand -base64 48>
CORS_ORIGINS=https://dashboard.yourfarm.com
NEXT_PUBLIC_API_URL=https://dashboard.yourfarm.com/api/v1
LOG_LEVEL=WARNING
```

### Related Documents

| Document | Description |
|----------|-------------|
| [QUICKSTART.md](QUICKSTART.md) | 5-minute deployment guide |
| [TUTORIAL.md](TUTORIAL.md) | Walk-through of all features |
| [TUI-GUIDE.md](TUI-GUIDE.md) | Textual terminal UI reference |
| [ARCHITECTURE.md](../technical/ARCHITECTURE.md) | System architecture and trade-offs |
| [DEPLOYMENT.md](../technical/DEPLOYMENT.md) | Full deployment and operations guide |
| [SECURITY.md](../technical/SECURITY.md) | Threat model and security configuration |
