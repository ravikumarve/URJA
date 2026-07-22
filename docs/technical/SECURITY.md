# URJA — Security Architecture & Threat Model

**Version**: 1.0
**Author**: Security Architect
**Last Updated**: 2026-07-22
**Framework**: STRIDE (Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege)
**Scope**: URJA boilerplate v1 — self-hosted deployment by buyers

> This document is written for developers who purchased URJA. It describes what is already secured in the codebase, what you must configure for your deployment, and how to think about threats to your renewable energy asset management system. Security is a spectrum, not a binary.

---

## Table of Contents

1. [Threat Model](#1-threat-model)
2. [Authentication & Authorization](#2-authentication--authorization)
3. [API Security](#3-api-security)
4. [Database Security](#4-database-security)
5. [Secrets Management](#5-secrets-management)
6. [Infrastructure Security](#6-infrastructure-security)
7. [Secure Development](#7-secure-development)
8. [Carbon Credit Specific Security](#8-carbon-credit-specific-security)
9. [Logging & Incident Response](#9-logging--incident-response)
10. [Compliance Considerations](#10-compliance-considerations)
11. [Buyer Configuration Checklist](#11-buyer-configuration-checklist)

---

## 1. Threat Model

### 1.1 Assets

| Asset | Sensitivity | Financial Impact if Compromised |
|-------|-------------|--------------------------------|
| **Generation data (telemetry)** | Commercially sensitive — reveals operational patterns, production capacity | Moderate: competitor intelligence, contract renegotiation leverage |
| **Carbon credits** | Financially significant — each credit represents ~1 tCO2e at $40–$100 market value | High: fraudulent minting or retirement can create direct monetary loss |
| **API keys** | Machine-to-machine credentials for SCADA integration | High: unauthorized telemetry injection or data exfiltration |
| **User credentials** | Dashboard access for operators, admins, viewers | High: full system compromise via admin account |
| **Dispatch rules** | Configuration for battery charging, curtailment decisions | Moderate: manipulated rules cause revenue loss |
| **Grid pricing data** | Day-ahead and real-time market prices | Low: public data, but manipulated pricing skews dispatch decisions |
| **Configuration (env vars)** | Database passwords, JWT secret, external API keys | Critical: full system compromise |

### 1.2 Threat Actors

| Actor | Motivation | Capability | Likelihood |
|-------|------------|------------|------------|
| **External attacker** | Financial gain, data theft, ransomware | Internet-based scanning, credential stuffing, known CVE exploitation | Medium |
| **Compromised API key holder** | Data exfiltration, telemetry injection | Valid credentials with limited scope | Low |
| **Malicious insider (operator)** | Carbon credit fraud, data manipulation | Authenticated access, domain knowledge | Low |
| **Disgruntled ex-employee** | Sabotage, data destruction | Revoked credentials, but may have retained API keys | Low |
| **Supply chain attacker** | Dependency compromise, backdoor insertion | Compromised npm/PyPI package | Very low (but high impact) |

### 1.3 Trust Boundaries

```
Internet
   │
   ▼
[Reverse Proxy / Load Balancer]  ─── Boundary 1: TLS termination
   │
   ▼
[Next.js Frontend]  ─── Boundary 2: User session ↔ API
   │
   ▼
[FastAPI Application]  ─── Boundary 3: Application ↔ Database
   │
   ├──▶ [PostgreSQL + TimescaleDB]  ─── Boundary 4: DB network isolation
   │
   └──▶ [Redis 7]
```

**Boundary 1 — Internet → Reverse Proxy:**
- TLS termination happens here. All traffic must be HTTPS in production.
- Rate limiting, IP blocking, WAF rules live at this boundary.
- No direct database or Redis access from outside the Docker network.

**Boundary 2 — Frontend ↔ API:**
- JWT access tokens (15 min TTL) passed as `Authorization: Bearer` headers.
- httpOnly refresh tokens (7 day TTL) for session extension.
- API keys (`X-API-Key` header) for M2M traffic.
- CORS restricted to configured origins.

**Boundary 3 — Application ↔ Database:**
- Parameterized queries via SQLAlchemy ORM — no raw SQL concatenation.
- Application connects with least-privilege database user.
- `organization_id` scoping enforced at service layer — never trusted from client.

**Boundary 4 — Database Network Isolation:**
- PostgreSQL port 5432 and Redis port 6379 are internal to the Docker network only.
- No external exposure of database or Redis ports.

### 1.4 STRIDE Analysis Per Component

| Component | Spoofing | Tampering | Repudiation | Info Disclosure | DoS | Elevation of Privilege |
|-----------|----------|-----------|-------------|-----------------|-----|------------------------|
| **API (FastAPI)** | JWT signature verification prevents token forgery | Pydantic validation rejects malformed payloads | All auth attempts and mutations logged in `audit_log` | CORS, rate limiting, no sensitive fields in error messages | Rate limiting per IP and per key | RBAC enforced at middleware and service layer |
| **Frontend (Next.js)** | httpOnly cookies prevent XSS token theft | Input validation before API submission | N/A (frontend actions logged server-side) | No secrets in client-side bundles. CSP headers. | Request throttling | UI enforces role-based visibility; server rejects unauthorized actions |
| **Database** | Connection string from env vars only | Parameterized queries prevent SQL injection | `audit_log` table is append-only, no updates/deletes allowed | Encrypted at rest (buyer responsibility). Least-privilege DB user. | Connection pooling limits max connections | No direct DB access from outside application network |
| **Redis** | Authentication via `REDIS_PASSWORD` env var | N/A (cache layer, no persistent critical data) | N/A | No sensitive data cached long-term | Memory limits via `maxmemory` config | Separate Redis instance per deployment |
| **Carbon Credits** | Credit issuance requires JWT auth + RBAC | Cryptographic hash chain between consecutive credits | Full audit trail per credit — actor, timestamp, changes | Credit data available only within org scope | Rate limited mint endpoint | Multi-step validation prevents raw-data-to-credit path |

---

## 2. Authentication & Authorization

### 2.1 Authentication Methods

| Method | Use Case | Implementation | Security Properties |
|--------|----------|----------------|---------------------|
| **JWT Access Token** | Web dashboard sessions | HS256-signed, 15 min TTL, stored in memory (frontend JS) | Short TTL limits window of compromise. Cannot be revoked individually — rotation by short expiry. |
| **JWT Refresh Token** | Session extension | HS256-signed, 7 day TTL, stored in httpOnly Secure SameSite=Strict cookie. SHA-256 hash stored in `sessions` table. | Rotated on each use (old token revoked). Server-side revocation possible by deleting session row. httpOnly prevents XSS theft. |
| **API Key** | M2M (SCADA, external monitoring) | Pre-generated UUID v4 with `urja_` prefix. SHA-256 hash stored in DB. Full key shown **once** on creation. | Cannot be retrieved after creation. Can be revoked individually via `DELETE /api/v1/api-keys/{id}`. Scoped to `read`, `write`, or `admin`. |

**JWT Token Payload:**
```json
{
  "sub": "user_abc123",
  "org": "org_xyz789",
  "roles": ["admin"],
  "iat": 1712345678,
  "exp": 1712346578
}
```

**Token Storage Rules:**
- Access tokens NEVER stored in localStorage or sessionStorage — only in memory (React context variable).
- Refresh tokens NEVER accessible to JavaScript — httpOnly cookie only.
- API keys stored in environment variables or secret manager — never hardcoded in config files.

### 2.2 RBAC Roles

| Role | Scope | Allowed Actions |
|------|-------|-----------------|
| **admin** | Organization-wide | Full CRUD on all modules, user management, API key management, dispatch rules, settings |
| **operator** | Organization-wide | View all, acknowledge alerts, export reports, run dispatch optimization, create work orders |
| **viewer** | Organization-wide | View-only access to all dashboards and exports. No mutations. |

Permission model: `{action}:{resource}` (e.g., `read:telemetry`, `write:dispatch_rules`).

**Enforcement layers:**
1. **API Middleware**: Decodes JWT, extracts org + roles, attaches to request context.
2. **Service Layer**: Checks permission against required action and resource.
3. **Database Layer**: All queries scoped by `organization_id` from authenticated context.

### 2.3 Multi-Tenant Data Isolation

URJA supports two deployment patterns:
- **Single-org per instance**: One organization per Docker Compose deployment.
- **Multi-org per instance**: A buyer managing multiple farms can create separate organizations.

**Isolation mechanism:**
- Every table includes an `organization_id` column with a composite index.
- The `organization_id` is extracted from the JWT or API key at the middleware layer — NEVER accepted from client request body.
- All repository queries include `WHERE organization_id = :org_id` via a base repository mixin.
- No cross-organization data access is possible at the service layer — enforced by design.
- Organization IDs are UUIDs — not guessable sequence numbers.

**What if a buyer modifies the code?** The isolation is enforced at three layers (middleware, service, query). Removing all three layers requires deliberate code modification. Accidental IDOR is architecturally prevented.

### 2.4 Password Policy

| Requirement | Setting |
|-------------|---------|
| Minimum length | 8 characters |
| Hashing algorithm | bcrypt (cost factor 12) |
| Rate limit on login | 5 attempts per minute per IP |
| Account lockout | After 10 failed attempts, account locked for 15 minutes |
| Password reset | Email-based reset token (1 hour TTL, single-use) |

---

## 3. API Security

### 3.1 Rate Limiting

| Tier | Limit | Burst | Applied To |
|------|-------|-------|------------|
| Authenticated (JWT) | 300 req/min | 50 req | Per user |
| API Key (read) | 1,000 req/min | 100 req | Per key |
| API Key (write) | 500 req/min | 50 req | Per key |
| API Key (admin) | 500 req/min | 50 req | Per key |
| Unauthenticated | 20 req/min | 5 req | Per IP |
| Telemetry ingest (API key) | 10,000 req/min | 500 req | Per key |
| Login endpoint | 5 req/min | 2 req | Per IP |

**Rate limit headers included in every response:**
```http
X-RateLimit-Limit: 300
X-RateLimit-Remaining: 287
X-RateLimit-Reset: 1712346878
Retry-After: 45
```

Exceeded limit returns `429 Too Many Requests` with RFC 7807 error body.

### 3.2 Input Validation

- **All request bodies** validated by Pydantic v2 schemas at the router boundary.
- **Unknown fields** are rejected by strict mode — no silent field dropping.
- **Type coercion** disabled — strings in integer fields return 422.
- **SQL injection** prevented by SQLAlchemy ORM parameterized queries. No raw SQL concatenation anywhere in the codebase.
- **Path traversal** prevented by UUID-typed path parameters — no string paths to database.
- **Batch limits** enforced — telemetry ingest capped at 1,000 records per request.

### 3.3 CORS

```python
# backend/app/middleware/cors.py
origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Authorization", "Content-Type", "X-API-Key", "Idempotency-Key"],
)
```

**Hardening guidance for production:**
- Set `CORS_ORIGINS` to the exact frontend URL (e.g., `https://dashboard.yourfarm.com`).
- Do NOT use wildcard (`*`) origins in production.
- If API and frontend are on the same domain, CORS is not needed for same-origin requests.

### 3.4 Security Headers

The frontend (Next.js) should be configured with the following headers (via reverse proxy or `next.config.js`):

```http
Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' https://*.tile.openstreetmap.org data:; connect-src 'self' https://api.yourfarm.com; frame-ancestors 'none'
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Strict-Transport-Security: max-age=31536000; includeSubDomains
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: camera=(), microphone=(), geolocation=(self)
```

### 3.5 Idempotency

`POST` endpoints that create resources support idempotency via the `Idempotency-Key` header:

```http
POST /api/v1/carbon/issue
Idempotency-Key: idem_abc123def456
```

- Key is stored for 24 hours.
- Duplicate keys return the original response (201 or error) — no duplicate resource created.
- This prevents accidental double-issuance of carbon credits from network retries.
- Affected endpoints: `POST /carbon/issue`, `POST /telemetry` (batch).

### 3.6 Authentication Bypass Protections

- **Registration**: Requires unique organization slug and email. Rate limited.
- **Login**: Failed attempts logged. Rate limited per IP. Account lockout after 10 failures.
- **Token refresh**: Old refresh token is revoked when a new one is issued (rotation). Replay of a revoked token returns 401.
- **Logout**: Server-side invalidation of refresh token prevents further access token issuance.
- **API key creation**: Requires admin role. Key shown once and cannot be retrieved.

---

## 4. Database Security

### 4.1 Connection Security

| Measure | Implementation |
|---------|----------------|
| Connection string | From `DATABASE_URL` environment variable — never hardcoded |
| Application user | Least-privilege database user — only has CRUD on application tables, no DDL (migrations run by separate user or CI) |
| Connection pooling | SQLAlchemy async pool with configurable `pool_size` and `max_overflow` (default: 10 / 5) |
| Network isolation | Database port 5432 exposed only within Docker network — not accessible from host or internet |
| SSL/TLS | Database connection uses TLS if available (configurable via connection string parameter) |

### 4.2 Query Security

- **Parameterized queries**: All database operations use SQLAlchemy ORM or asyncpg parameterized queries. No string interpolation of user input.
- **organization_id scoping**: Every repository method includes `WHERE organization_id = :org_id` — extracted from authenticated context, never from client input.
- **No raw SQL**: The codebase does not use `text()` or raw string queries for any user-facing operation. Administrative scripts may use raw SQL but are never exposed via API.

### 4.3 Encryption at Rest

| Data | Mechanism | Responsibility |
|------|-----------|----------------|
| Database files (pgdata volume) | PostgreSQL TDE (Transparent Data Encryption) or filesystem-level encryption (LUKS) | Buyer configures |
| Backups | Encrypted with GPG or AWS KMS before storage | Buyer configures |
| Redis data | No persistent encryption — Redis data is ephemeral cache. If Redis persistence (RDB/AOF) is enabled, buyer should encrypt the volume. | Buyer configures |

### 4.4 Audit Log (Append-Only)

The `audit_log` table is the immutable record of all significant system actions:

```sql
CREATE RULE audit_log_no_update AS ON UPDATE TO audit_log DO INSTEAD NOTHING;
CREATE RULE audit_log_no_delete AS ON DELETE TO audit_log DO INSTEAD NOTHING;
```

- Rows cannot be updated or deleted at the database level.
- All auth attempts, data modifications, and admin actions are logged.
- Audit log is scoped by `organization_id` and includes actor, action, target, changes (JSON diff), IP address, and user agent.

### 4.5 Database User Management

| User | Purpose | Permissions |
|------|---------|-------------|
| `urja_app` (application) | Runtime database access | `SELECT`, `INSERT`, `UPDATE`, `DELETE` on all application tables. No DDL. |
| `urja_migrate` (migrations) | Alembic schema migrations | Schema modification privileges. Should not be the application user. |
| `urja_backup` (backups) | Automated backups | `SELECT` on all tables, `COPY` privilege. |

In Docker Compose, the application connects as `urja_app`. The migration user is used only during deployment. The application user cannot modify schema or access PostgreSQL system catalogs.

---

## 5. Secrets Management

### 5.1 What Must Be Secret

| Secret | Where It's Used | How It's Set |
|--------|-----------------|--------------|
| `POSTGRES_PASSWORD` | Database authentication | `.env` file, Docker secrets |
| `JWT_SECRET` | JWT signing (HS256) | `.env` file |
| `JWT_REFRESH_SECRET` | Refresh token signing (can be same as `JWT_SECRET` or separate) | `.env` file |
| `REDIS_PASSWORD` | Redis authentication | `.env` file |
| `DATABASE_URL` | Application database connection | Built from env vars at startup |
| External API keys (weather, grid pricing, carbon registry) | External service integration | `.env` file |
| Encryption keys for settings encryption | Encrypted settings in `settings` table | `.env` file |

### 5.2 Rules

1. **ALL secrets go in environment variables.** Nothing is hardcoded. `.env.example` is checked into the repository with placeholder values (e.g., `POSTGRES_PASSWORD=change-me-in-production`).
2. **`.env` is in `.gitignore`.** The actual `.env` file is never committed. Pre-commit hooks validate this.
3. **No secrets in code comments, logs, or error messages.** Logging at DEBUG level redacts sensitive fields (password hashes, token values, API keys).
4. **Secrets rotated on deployment.** A deployment script generates new secrets unless explicitly preserved.
5. **Docker secrets** are supported for production deployments. `POSTGRES_PASSWORD` and `JWT_SECRET` can be passed as Docker secrets instead of environment variables.

### 5.3 .env.example Template

```bash
# Database
POSTGRES_DB=urja
POSTGRES_USER=urja
POSTGRES_PASSWORD=change-me-in-production

# API
DATABASE_URL=postgresql+asyncpg://urja:${POSTGRES_PASSWORD}@db:5432/urja
REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
REDIS_PASSWORD=change-me-in-production
JWT_SECRET=generate-a-random-64-char-string
JWT_ACCESS_EXPIRE_MINUTES=15
JWT_REFRESH_EXPIRE_DAYS=7
CORS_ORIGINS=http://localhost:3000
LOG_LEVEL=INFO

# External Services (optional)
WEATHER_API_KEY=
GRID_PRICE_API_KEY=
CARBON_REGISTRY_API_KEY=

# Frontend
NEXT_PUBLIC_API_URL=http://api:8000/api/v1
NEXT_PUBLIC_MAP_TILE_URL=https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png
```

### 5.4 Recommended Tools for Production

| Tool | Purpose |
|------|---------|
| `openssl rand -base64 48` | Generate JWT secret key |
| Docker secrets | Pass secrets as files mounted into containers (more secure than env vars) |
| HashiCorp Vault | Centralized secret management (overkill for single-server deployments, useful for enterprise) |
| AWS Secrets Manager / GCP Secret Manager | Cloud-native secret storage (if deploying on cloud) |

---

## 6. Infrastructure Security

### 6.1 Docker Compose Hardening

| Service | User | Privileged | Ports Exposed | Notes |
|---------|------|------------|---------------|-------|
| **api** | Non-root `urja` user (UID 1000) | No | Internal (Docker network) | Health check at `/health` |
| **frontend** | Non-root `node` user (UID 1000) | No | `3000` (to host) | Built as production build |
| **db** | PostgreSQL default (`postgres` UID 999) | No | Internal only | Health check via `pg_isready` |
| **redis** | Non-root (redis default) | No | Internal only | Health check via `redis-cli ping` |
| **tui** | Non-root | No | `8080` (to host, optional) | Textual web mode |

### 6.2 Docker Compose Security Directives

```yaml
services:
  api:
    user: "1000:1000"
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    read_only: true
    tmpfs:
      - /tmp

  db:
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    cap_add:
      - CHOWN
      - DAC_OVERRIDE
      - SETUID
      - SETGID
```

### 6.3 Network Security

```
Docker Network: urja_network (bridge, internal)
  - API container exposed at api:8000 (internal only)
  - Frontend container exposed at :3000 (host-facing)
  - DB container exposed at db:5432 (internal only)
  - Redis container exposed at redis:6379 (internal only)
```

- Only the frontend (port 3000) and optional TUI web mode (port 8080) are exposed to the host.
- Database and Redis ports are internal to the Docker network — not accessible from outside.
- In production, place a reverse proxy (Caddy, Nginx, Traefik) in front of the frontend for TLS termination.

### 6.4 Health Endpoints

- `GET /health` returns basic status: `{"status": "ok", "version": "1.0.0"}`.
- Does NOT return system information (DB version, Python version, disk usage).
- Does NOT return environment variables or configuration.
- Docker Compose uses health checks for orchestration, not for external monitoring.

### 6.5 Reverse Proxy Configuration (Production)

Recommended: Caddy (auto TLS) or Nginx.

**Caddy example:**
```caddyfile
dashboard.yourfarm.com {
    reverse_proxy frontend:3000
    header /api/* X-Forwarded-Proto {scheme}
    header /* Strict-Transport-Security "max-age=31536000"
}
```

**Nginx example:**
```nginx
server {
    listen 443 ssl;
    server_name dashboard.yourfarm.com;

    ssl_certificate /etc/letsencrypt/live/dashboard.yourfarm.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/dashboard.yourfarm.com/privkey.pem;

    location / {
        proxy_pass http://frontend:3000;
    }

    location /api/ {
        proxy_pass http://api:8000;
    }

    add_header Strict-Transport-Security "max-age=31536000" always;
}
```

---

## 7. Secure Development

### 7.1 Dependency Management

| Measure | Tool | Schedule |
|---------|------|----------|
| Python dependency scanning | `pip-audit` or Safety CLI | Pre-commit and CI |
| JavaScript dependency scanning | `npm audit` | Pre-commit and CI |
| Container image scanning | Grype or Trivy | CI pipeline |
| Dependency updates | Dependabot (GitHub) or Renovate | Weekly automated PRs |

**Pinning:**
- `requirements.txt` pins exact versions (`package==1.2.3`), not range constraints.
- `package-lock.json` is checked into version control.
- Docker images pin major versions (`timescale/timescaledb:2.17-pg16`) and are updated explicitly.

### 7.2 Pre-Commit Hooks

The repository includes `.pre-commit-config.yaml` with:

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-added-large-files
      - id: detect-private-key

  - repo: https://github.com/astral-sh/ruff
    rev: v0.4.0
    hooks:
      - id: ruff
      - id: ruff-format

  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets
        args: ['--baseline', '.secrets.baseline']
```

### 7.3 SAST in CI

| Tool | Scope | Trigger |
|------|-------|---------|
| **Ruff** (linter) | Python code quality, import organization | Every push |
| **MyPy** (type checker) | Python type safety in strict mode | Every push |
| **Pyright** | Additional Python type checking | Every push |
| **Bandit** | Python security analysis (SQL injection, hardcoded passwords, eval) | Every push |
| **ESLint** | JavaScript/TypeScript security rules | Every push |

### 7.4 Secrets Detection

- `detect-secrets` runs as a pre-commit hook with a baseline file.
- Any new secret detected without being in the baseline blocks the commit.
- CI also runs `detect-secrets` on the full repository to catch secrets that might have been committed.

---

## 8. Carbon Credit Specific Security

Carbon credits have financial value. A compromised carbon module could mint fraudulent credits or retire legitimate ones. These controls are specific to the carbon pipeline.

### 8.1 Immutable Audit Trail

Every carbon credit has a complete audit trail stored in the `audit_log` table:

```
credit.created       → who created it and from which generation batch
credit.issued        → when it was issued to the registry
credit.retired       → who retired it and when
credit.cancelled     → who cancelled it and why
```

The audit log is protected by PostgreSQL rules preventing any `UPDATE` or `DELETE` at the database level.

### 8.2 Cryptographic Hash Chain

Each carbon credit record contains a `previous_credit_hash` field linking it to the preceding credit:

```sql
ALTER TABLE carbon_credits ADD COLUMN previous_credit_hash TEXT;
ALTER TABLE carbon_credits ADD COLUMN credit_hash TEXT NOT NULL UNIQUE;
```

**Hash computation:**
```
credit_hash = SHA256(
    previous_credit_hash +
    credit_id +
    asset_id +
    quantity +
    generation_start +
    generation_end +
    issued_by
)
```

This creates a tamper-evident chain. Modifying any field in a credit record invalidates all subsequent hashes. The chain can be verified periodically by a background worker.

**Verification query:**
```sql
SELECT
    credit_id,
    credit_hash = SHA256(
        previous_credit_hash ||
        credit_id::text ||
        asset_id::text ||
        quantity::text ||
        generation_start::text ||
        generation_end::text ||
        issued_by::text
    ) AS hash_valid
FROM carbon_credits
ORDER BY ts ASC;
```

### 8.3 Multi-Step Validation

Carbon credit issuance follows a validated pipeline — no direct path from raw telemetry to minted credit:

```
Step 1: Generation data aggregated (kWh by asset, by time range)
Step 2: Emission factor applied (CO2_eq = kWh × factor)
Step 3: Methodology version validated (IPMVP_v2.1 or configured)
Step 4: De-duplication check (credits not already issued for this range)
Step 5: Credit record created (status: pending)
Step 6: Audit trail record written
Step 7: Registry push (Verra / Hedera Guardian)
Step 8: Credit status set to active
```

- Steps 5–8 happen in a database transaction with rollback on failure.
- No single API call can create credits without going through the full pipeline.
- The `POST /carbon/issue` endpoint requires `write` or `admin` scope.
- The `Idempotency-Key` header prevents double-issuance from network retries.

### 8.4 Export Security

ESG report exports (PDF) include a digital signature:

```
Signature = RSA-SHA256( report_content_hash, private_key )
```

The signature is embedded in the PDF metadata. Verifying the signature confirms the report was generated by the URJA instance and has not been tampered with. The public key is retrievable via `GET /api/v1/organization/public-key`.

This does not constitute a legally binding digital signature — it provides tamper evidence for internal audit purposes.

### 8.5 Roles for Carbon Operations

| Action | Required Role |
|--------|---------------|
| View credit portfolio | `viewer` or higher |
| Issue credits | `operator` or higher |
| Retire credits | `admin` only |
| Cancel credits | `admin` only |
| Export ESG report | `operator` or higher |
| Change emission factor | `admin` only |

---

## 9. Logging & Incident Response

### 9.1 What Is Logged

| Event | Logged To | Retention |
|-------|-----------|-----------|
| Successful login | `audit_log` + application logs | 90 days (audit_log permanent) |
| Failed login (incl. IP, user agent) | `audit_log` + application logs | 90 days |
| Token refresh | Application logs | 30 days |
| API key creation/revocation | `audit_log` | Permanent |
| Asset CRUD operations | `audit_log` | Permanent |
| Telemetry ingestion | `audit_log` (batch level) | 90 days |
| Carbon credit mint/retire/cancel | `audit_log` | Permanent (regulatory) |
| Dispatch rule changes | `audit_log` | Permanent |
| Alert acknowledge/resolve | `audit_log` | 1 year |
| User role changes | `audit_log` | Permanent |
| Settings changes | `audit_log` | Permanent |
| Rate limit violations | Application logs | 30 days |
| 4xx and 5xx responses | Application logs | 30 days |

### 9.2 What Is NOT Logged

- Passwords (plaintext or hashed) — never written to logs.
- JWT tokens or API key values.
- Full telemetry payloads (logged at DEBUG level only, which is disabled in production).
- Database connection strings.
- External API keys.

### 9.3 Alert Thresholds

| Condition | Alert | Action |
|-----------|-------|--------|
| >5 failed logins in 1 minute | Credential stuffing detected | Log warning, increase rate limiting |
| >20 failed logins in 1 hour | Active brute force attack | Log critical, consider IP block |
| API key used from new IP (geo-change) | Possible key compromise | Log warning (requires buyer to implement geo-fencing on their reverse proxy) |
| >10 carbon credits retired in 1 hour | Unusual carbon activity | Log warning |
| Audit log entry for admin user at 3 AM | Off-hours admin activity | Log info (security-conscious buyers may alert on this) |
| Database connection pool exhausted | Possible DoS or connection leak | Log critical |
| >1000 telemetry records rejected in 1 hour | Ingestion pipeline issue | Log warning |

### 9.4 Breach Containment

If a breach is suspected, the following actions can be taken immediately:

1. **Revoke all sessions for an organization:**
   ```sql
   UPDATE sessions SET is_revoked = TRUE
   WHERE organization_id = :org_id AND is_revoked = FALSE;
   ```

2. **Revoke all API keys for an organization:**
   ```sql
   UPDATE api_keys SET is_active = FALSE
   WHERE organization_id = :org_id AND is_active = TRUE;
   ```

3. **Deactivate user accounts:**
   ```sql
   UPDATE users SET is_active = FALSE
   WHERE organization_id = :org_id AND is_active = TRUE;
   ```

4. **Reset JWT secret** (forces re-login for all users):
   Change `JWT_SECRET` in `.env` and restart the API container.

5. **Rotate database password:**
   Change `POSTGRES_PASSWORD` in `.env`, update `DATABASE_URL`, restart all containers.

### 9.5 Forensics

- The `audit_log` table provides a non-repudiable trail of all actions.
- Application logs (stdout/stderr) are captured by Docker and should be shipped to a centralized logging system (ELK, Loki, Datadog) in production.
- The `audit_log` is never rotated or truncated — it is the permanent record.
- For cloud deployments, enable AWS CloudTrail / GCP Audit Logs for infrastructure-level audit.

---

## 10. Compliance Considerations

### 10.1 SOC 2 Principles

URJA's security architecture aligns with SOC 2 trust service criteria:

| SOC 2 Criterion | URJA Implementation |
|-----------------|---------------------|
| **Security** — Protect against unauthorized access | RBAC, JWT auth, API key scoping, rate limiting, CORS |
| **Availability** — System available for operation | Health checks, Docker restart policies, connection pooling |
| **Processing Integrity** — Processing is complete and accurate | Pydantic validation, idempotency keys, parameterized queries |
| **Confidentiality** — Information designated as confidential is protected | `organization_id` isolation, audit logging, no PII in logs |
| **Privacy** — Personal information is collected and handled appropriately | Minimal PII collected (email, name), no tracking/analytics |

**Buyer responsibility:** SOC 2 certification requires formal policies, annual audits, and organizational controls. URJA provides the technical foundation but buyers must implement policies around access reviews, incident response plans, and employee training.

### 10.2 GDPR Readiness

| GDPR Requirement | URJA Support |
|------------------|--------------|
| **Right to be forgotten** | `DELETE /api/v1/users/{id}` deletes user data. Organization deletion removes all related data. |
| **Data portability** | `GET /api/v1/export` returns all user and organization data in JSON format. |
| **Data processing records** | `audit_log` captures all actions on user data. |
| **Breach notification** | Alert thresholds in Section 9.3 detect unusual activity. Buyer must implement notification procedures. |
| **Consent tracking** | The `users` table includes `email_verified_at` for consent audit. No marketing emails are sent by the boilerplate. |
| **Data minimization** | Only required fields collected: email, display name, role. No tracking cookies, no analytics. |

**Buyer responsibility:** GDPR compliance depends on how you deploy URJA (EU vs. non-EU data residency), whether you collect additional PII, and your data processing register.

### 10.3 Carbon Credit Standards Alignment

| Standard | URJA Alignment |
|----------|----------------|
| **Verra VCS Methodology** | IPMVP methodology built-in. Methodology version tracked per credit. Generation period, emission factor, and calculation visible in audit trail. |
| **Verra Registry** | `registry_tx_id` and `registry_url` stored per credit. Integration point for Verra registry API (buyer implements). |
| **Hedera Guardian** | MRV pipeline designed to push Verifiable Credentials to Hedera Guardian. Audit trail structure compatible with Guardian schema. |
| **ICVCM (Integrity Council)** | Core principles followed: conservative emission factors, transparent methodology, third-party verifiable audit trail. |

**Important:** URJA provides the data pipeline and audit infrastructure for carbon credit issuance. It does not replace third-party verification required by Verra, Gold Standard, or other registries. Credits issued through URJA must still undergo independent verification before they are tradeable.

---

## 11. Buyer Configuration Checklist

This checklist covers what is already secured in the boilerplate and what you must configure for your production deployment.

### ✅ Already Secured (No Action Required)

- [x] All database queries parameterized via SQLAlchemy ORM — no SQL injection vectors
- [x] `organization_id` scoping on all queries — no IDOR between organizations
- [x] Passwords hashed with bcrypt (cost 12) — no plaintext storage
- [x] JWT signed with HS256 — token forgery prevented
- [x] Refresh tokens stored as httpOnly cookies — XSS cannot steal them
- [x] Refresh token rotation — old token revoked on each refresh
- [x] API keys stored as SHA-256 hashes — raw key shown only once
- [x] RBAC with three roles (admin, operator, viewer) — enforced at middleware + service layer
- [x] Rate limiting per IP and per API key
- [x] Pydantic validation on all endpoints — malformed payloads rejected
- [x] CORS restricted to configured origins
- [x] Audit log is append-only — no updates or deletes at DB level
- [x] Docker containers run as non-root users
- [x] No privileged containers
- [x] Internal database/Redis ports not exposed to host
- [x] Health endpoints do not leak system information
- [x] Idempotency keys prevent duplicate resource creation
- [x] Carbon credit hash chain provides tamper evidence
- [x] Pre-commit hooks for secrets detection
- [x] `.env` in `.gitignore` — secrets never committed
- [x] No tracking, no analytics, no telemetry from the boilerplate itself

### ⚠️ Must Configure (Buyer Action Required)

- [ ] **Set strong secrets**: Generate new `JWT_SECRET`, `POSTGRES_PASSWORD`, `REDIS_PASSWORD` for production. Do NOT use the `.env.example` values.
- [ ] **Enable TLS**: Configure a reverse proxy (Caddy, Nginx, Traefik) with valid TLS certificates. Do NOT expose HTTP in production.
- [ ] **Configure CORS origins**: Set `CORS_ORIGINS` to your actual frontend domain.
- [ ] **Set up backups**: Configure automated PostgreSQL backups (pg_dump, pgBackRest, or cloud-native snapshot). Test recovery.
- [ ] **Enable database encryption at rest**: Configure PostgreSQL TDE or use filesystem-level encryption (LUKS) on the data volume.
- [ ] **Configure email sending**: Set SMTP credentials for password reset and user invitation emails. If not configured, these features will not work.
- [ ] **Set up centralized logging**: Ship Docker logs to ELK, Loki, Datadog, or similar. Enable log retention and alerting.
- [ ] **Implement WAF**: Consider a web application firewall (Cloudflare, ModSecurity) for production deployments.
- [ ] **Regular dependency updates**: Subscribe to Dependabot or Renovate notifications. Apply security patches promptly.
- [ ] **Penetration testing**: Conduct or contract a penetration test before deploying with real operational data.
- [ ] **Vulnerability disclosure policy**: Publish a `SECURITY.md` (this document) and a contact for security researchers to report findings.

### 🔒 Recommended for Enterprise Deployments

- [ ] Use Docker secrets instead of environment variables for sensitive values.
- [ ] Deploy with a dedicated secrets manager (HashiCorp Vault, AWS Secrets Manager).
- [ ] Enable database audit logging (PostgreSQL `pgaudit` extension) for compliance.
- [ ] Implement network policies (Kubernetes NetworkPolicy or iptables) for micro-segmentation.
- [ ] Use a hardware security module (HSM) or cloud KMS for JWT signing keys.
- [ ] Conduct annual penetration tests and security reviews.
- [ ] Implement SIEM integration (Splunk, Sentinel, ELK) for real-time threat detection.

---

## Appendix A: Vulnerability Disclosure

If you discover a security vulnerability in URJA, please report it privately:

1. **Do NOT** open a public GitHub issue.
2. Email the maintainer at the contact address provided in the Gumroad purchase confirmation.
3. Include a detailed description, steps to reproduce, and (if possible) a proof of concept.
4. Allow 72 hours for an initial response and 14 days for a fix before public disclosure.

We follow coordinated disclosure: we will fix the vulnerability, notify affected buyers, and publish a security advisory after the fix is deployed.

## Appendix B: Related Documents

| Document | Description |
|----------|-------------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | System architecture, C4 diagrams, ADR-5 (JWT auth decision), ADR-7 (polling) |
| [API-SPEC.md](API-SPEC.md) | API contract — auth flows, token structure, RBAC, rate limits |
| [DATABASE.md](DATABASE.md) | Database schema — audit log, sessions table, api_keys table, carbon_credits |
| [PRD.md](../product/PRD.md) | Product requirements — non-goals re: compliance certifications |
| [DEPLOYMENT.md](DEPLOYMENT.md) | Deployment guide — Docker Compose, environment variables, TLS |

---

*SECURITY.md v1.0 — Review this document with every major release. Security postures evolve. Your deployment is your responsibility; this document is your map.*
