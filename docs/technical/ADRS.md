# URJA — Architecture Decision Records

**Version**: 1.0
**Author**: Software Architect
**Last Updated**: 2026-07-22

> This document captures the key architectural decisions made during the design of URJA. Each ADR follows a consistent format: context, options considered, decision, and consequences (with trade-offs explicitly named). These records serve as the authoritative reference for *why* the system is built the way it is — and what was rejected along the way.

---

## Table of Contents

| # | Decision | Status |
|---|----------|--------|
| [ADR-001](#adr-001-boilerplate-over-live-saas) | Boilerplate over Live SaaS | Accepted |
| [ADR-002](#adr-002-modular-monolith-over-microservices) | Modular Monolith over Microservices | Accepted |
| [ADR-003](#adr-003-timescaledb-postgresql-over-influxdb) | TimescaleDB (PostgreSQL) over InfluxDB | Accepted |
| [ADR-004](#adr-004-arq-over-celery) | ARQ over Celery | Accepted |
| [ADR-005](#adr-005-jwt-auth-over-session-based) | JWT Auth over Session-Based | Accepted |
| [ADR-006](#adr-006-nextjs-over-reflex) | Next.js over Reflex | Accepted |
| [ADR-007](#adr-007-textual-tui-over-web-only) | Textual TUI over Web-Only | Accepted |
| [ADR-008](#adr-008-timescaledb-continuous-aggregates-over-application-level-rollups) | TimescaleDB Continuous Aggregates over App-Level Rollups | Accepted |
| [ADR-009](#adr-009-docker-compose-over-kubernetes) | Docker Compose over Kubernetes | Accepted |
| [ADR-010](#adr-010-seed-data-as-sql-scripts-over-application-fixtures) | Seed Data as SQL Scripts over Application Fixtures | Accepted |

---

## ADR-001: Boilerplate over Live SaaS

### Status

Accepted

### Context

URJA was originally conceived as a live SaaS product charging $500–$2,500/MW/month — competing directly with enterprise platforms like Power Factors ($50K+/year), Fluence Mosaic, and Wärtsilä GEMS. The target customers (10–200MW solar/wind farm operators, consultants, and system integrators) are underserved by enterprise software because:

1. **Cost barrier**: $50K+/year is unaffordable for small-to-mid-sized operators (the vast majority of the market).
2. **Deployment friction**: Enterprise SaaS requires 6–12 month consultancy engagements to set up.
3. **Trust deficit**: Operators in this segment prefer owning their infrastructure over vendor lock-in.

During market validation, we discovered an empty niche: renewable energy boilerplates. Generic boilerplates (ShipFast, Supastarter, Syntax) collectively serve 7,000+ customers at $129–$399 with zero energy domain logic. No boilerplate exists for the renewable energy sector.

### Options Considered

| Option | Revenue Model | Upfront Effort | Support Burden | Competitive Position |
|--------|---------------|----------------|----------------|---------------------|
| **Live SaaS** | $500–$2,500/MW/month recurring | High (hosting, infra, multi-tenancy) | High (SLA, uptime, support) | Direct battle with funded incumbents |
| **Boilerplate (one-time)** | $149–$499 per sale | Medium (code + docs only) | Low (no hosting, no SLA) | Empty niche, zero competitors |
| **Open-source + consulting** | Free code, paid consulting/services | Medium (community mgmt) | Medium (issues, PRs) | Hard to monetize; consulting doesn't scale |
| **Hybrid (free core + paid modules)** | $0 core, $99–$299 per module | High (module extraction) | Medium | Proven model; splits attention across modules |

### Decision

Sell URJA as a self-hosted boilerplate on Gumroad at $149 (Basic), $249 (Pro), and $499 (Enterprise). No hosted SaaS. No recurring billing. The buyer receives a private GitHub repository, full documentation, and a commercial license.

### Consequences

**Positive:**
- Zero hosting costs, zero infrastructure SLA, zero on-call — the buyer runs their own stack.
- Cash-flow positive from day 1 of launch — every sale is pure margin after Gumroad's 8% fee.
- Empty competitive niche — no other boilerplate provides renewable energy domain models, carbon MRV pipeline, or Textual TUI.
- Developer-led sales via Gumroad has a proven indie-hacker playbook (ShipFast: $3M+ revenue, Supastarter: $1M+ revenue).
- Infinite scalability — no server capacity planning, no database sharding concerns.

**Negative:**
- Lower per-customer revenue ($149–$499 one-time vs. $50K+/year recurring from enterprise SaaS). Requires approximately 50 sales/month at $199 ASP to reach $9,950/month revenue — achievable but requires consistent marketing.
- No recurring revenue moat — buyers purchase once and receive updates voluntarily. If updates stop, buyers don't churn (they keep what they bought).
- No direct relationship with end-users — the buyer is the operator of the boilerplate. URJA doesn't see usage data, crash reports, or feature adoption metrics.
- Support expectations must be carefully managed — "you buy the code, not the support." Priority support is a Pro tier differentiator to manage this.
- Piracy risk — once purchased, the code can be redistributed. Mitigated by commercial license enforcement for Enterprise tier and watermark-based attribution for Basic/Pro.

### Trade-Off Summary

**Chosen: One-time boilerplate.** Rejected: SaaS recurring revenue. The trade-off is lower revenue ceiling per customer in exchange for zero delivery cost, zero operational burden, and an uncontested niche. The SaaS route would require competing against funded incumbents with enterprise sales teams — a losing battle for a solo developer. The boilerplate route leverages existing distribution channels (Gumroad) and the indie-hacker playbook that has been validated across 7,000+ boilerplate buyers.

---

## ADR-002: Modular Monolith over Microservices

### Status

Accepted

### Context

URJA has six bounded contexts: Asset, Telemetry, Dispatch, Carbon, Health, and Auth. Each has distinct responsibilities, but they share data and must operate as a coherent system. The question is how to organize these contexts at the deployment level.

The target deployment environment is a single VPS or on-prem server with 2–4 GB RAM and 2–4 vCPUs. The target buyer is a solo developer, consultant, or small team — not an enterprise DevOps org with Kubernetes expertise.

### Options Considered

| Option | Deployment Unit | Inter-Context Communication | Scaling | DevOps Complexity | Developer Velocity |
|--------|----------------|---------------------------|---------|-------------------|-------------------|
| **Monolith** | 1 binary | In-process function calls | Scale vertically only | Minimal | High — fast iteration |
| **Modular Monolith** | 1 binary with enforced module boundaries | In-process via interfaces/events | Scale vertically only | Minimal | High — with architectural discipline |
| **Microservices** | 6+ services | HTTP/gRPC/RPC across network | Independent scaling per service | High (service mesh, discovery, tracing) | Medium — deployment overhead slows iteration |

### Decision

Modular monolith with six bounded contexts enforced at the Python package level. Each context lives in its own directory under `backend/services/` with:

- A clear public interface (`__init__.py` exposing only intended API)
- Private implementation modules prefixed with `_`
- Cross-context communication via explicit service-to-service function calls (not shared database access)
- Events for async notification between contexts (e.g., `TelemetryIngested` → `HealthScorer` picks it up)

```python
# Example boundary enforcement:
# backend/services/telemetry/__init__.py
from .service import TelemetryService
from .schemas import TelemetryReading, TelemetryBatch

# backend/services/telemetry/_ingest.py  (private)
# backend/services/telemetry/_validation.py  (private)
```

No HTTP calls between contexts within the same process. No shared mutable state across contexts. Each context has its own SQLAlchemy models and repository layer.

### Consequences

**Positive:**
- Single deployment unit — one Docker container for the entire API. Buyers start with `docker compose up` and get everything.
- Zero network overhead between contexts — no serialization, no latency, no partial failure handling for intra-process calls.
- Single connection pool to PostgreSQL — simpler connection management, lower memory footprint.
- Faster development velocity — no API contract negotiation between services; change a function signature and all callers are updated in the same commit.
- Easier debugging — a single process means a single set of logs, a single trace, a single point of failure.
- The boilerplate audience buys a codebase they can understand — a modular monolith is far more approachable than a distributed system.

**Negative:**
- Cannot scale individual contexts independently. If the telemetry ingest path is CPU-bound while the dashboard is idle, both share the same process resources. Mitigation: the target deployment has <50 assets and <200 requests/hour — vertical scaling is sufficient.
- A mistake in one context (e.g., OOM in telemetry ingest) takes down the entire API. Mitigation: ARQ workers run in separate processes for background tasks, isolating compute-heavy workloads from the API process.
- Module boundaries must be self-enforced through code review. There is no network boundary preventing a Telemetry service from directly calling into Carbon internals. Mitigation: CI lint rules (`flake8`-based import checker) prevent cross-context imports of private modules.
- Future extraction to microservices requires identifying the natural split points. Mitigation: event-driven cross-context communication today makes future service extraction straightforward — replace a function call with an async event handler.

### Trade-Off Summary

**Chosen: Modular monolith.** Rejected: Microservices. The trade-off is giving up independent scaling and fault isolation in exchange for dramatically simpler deployment, faster development, and lower cognitive load for boilerplate buyers. This is the right call for a $149–$499 product deployed by a single developer on a single server. If an Enterprise buyer needs HA, the modular architecture supports extraction to services — they pay for that consulting call.

---

## ADR-003: TimescaleDB (PostgreSQL) over InfluxDB

### Status

Accepted

### Context

URJA's primary data is time-series telemetry — 15-minute generation readings for each inverter, weather data, grid prices, health metrics, and curtailment events. A 50MW solar farm with 40 inverters generates ~1.4M rows/year of generation telemetry alone. The database must handle:

1. **High-frequency writes**: Batch inserts of telemetry (up to 1,000 records/batch) arriving every 15 minutes per asset.
2. **Time-bucketed queries**: Hourly/daily/monthly aggregation for dashboards and reports.
3. **Relational data**: Assets, users, organizations, dispatch rules, carbon credits — all are relational entities with FKs and joins.
4. **Historical rollups**: Pre-computed aggregates for fast dashboard rendering.

The choice is between a purpose-built time-series database (InfluxDB) and a PostgreSQL extension (TimescaleDB) that adds time-series capabilities to a full SQL database.

### Options Considered

| Dimension | TimescaleDB | InfluxDB | Prometheus + Thanos |
|-----------|-------------|----------|---------------------|
| **Query language** | Full SQL (PostgreSQL) | Flux (proprietary) | PromQL (pull-based) |
| **Relational data** | Same DB — FKs, joins, transactions | Separate InfluxDB bucket or a second DB | Requires separate relational DB |
| **Continuous aggregates** | Built-in, automatic refresh | Tasks system (limited, higher latency) | Recording rules |
| **Ecosystem** | Full PostgreSQL ecosystem (pgAdmin, PostGIS, pgvector, 300+ extensions) | Influx-specific (Telegraf, Chronograf) | Prometheus-specific |
| **Learning curve** | Low — any developer knows SQL | Medium — Flux is a new query language | Medium — PromQL + Thanos query |
| **Memory footprint** | ~20% more per row than InfluxDB | Lower per-row overhead | Lowest (pull model, no write amplification) |
| **Backup/restore** | pg_dump / pg_restore (standard tools) | influx backup/restore (custom) | Thanos sidecar + object storage |
| **Connection pooling** | pgbouncer, pgpool, built-in pool | No native pooling | No pooling needed (pull model) |
| **License** | Community (Apache 2.0) + Timescale License | MIT (InfluxDB OSS v2) | Apache 2.0 |

### Decision

PostgreSQL 16 + TimescaleDB 2.17. All time-series data lives in hypertables within the same database as relational tables. Continuous aggregates handle hourly and daily rollups. Compression policies reduce storage by 92–96% for historical data.

### Consequences

**Positive:**
- One database to learn, administer, and back up. A single `pg_dump` captures all relational and time-series data. Buyers who know PostgreSQL already know URJA's database.
- Full SQL means any PostgreSQL-compatible tool (DBeaver, DataGrip, Tableau, Grafana) works with URJA's data out of the box.
- Relational integrity — `asset_id` FKs on every hypertable ensure no orphaned telemetry. Transactions span relational and time-series tables.
- PostgreSQL ecosystem — PostGIS for spatial queries on asset locations, pgvector for future ML embedding storage, 300+ extensions available.
- TimescaleDB continuous aggregates are declarative — define the rollup once, and TimescaleDB keeps it up to date automatically. No cron jobs, no application-level aggregation logic.
- Compression is automatic and transparent — queries transparently decompress only the chunks they need.

**Negative:**
- ~20% higher memory footprint per row compared to InfluxDB for raw telemetry. At 1.4M rows/year for a 50MW farm, this is ~161 MB uncompressed. After compression (92–96%), the difference is negligible (~12 MB compressed vs. ~10 MB in InfluxDB).
- TimescaleDB community is smaller than InfluxDB's. Fewer blog posts, fewer Stack Overflow answers, fewer pre-built integrations. Mitigation: PostgreSQL community is vast and overlaps significantly.
- TimescaleDB-specific operations (chunk management, compression policies, continuous aggregate administration) require learning TimescaleDB internals — not just PostgreSQL. Mitigation: all operations are wrapped in Alembic migrations — buyers don't need to interact with TimescaleDB directly.
- Hypertable schema changes (ALTER TABLE DROP COLUMN) require a full table rewrite — more restrictive than regular PostgreSQL tables. Mitigation: migration strategy document explicitly covers hypertable constraints.

### Trade-Off Summary

**Chosen: TimescaleDB.** Rejected: InfluxDB. The trade-off is a slightly higher per-row memory footprint in exchange for eliminating the complexity of managing two databases (one for time-series, one for relational). For a boilerplate buyer deploying on a single server, running two databases doubles operational overhead. TimescaleDB's full SQL support eliminates the Flux learning curve — any developer who knows SQL can query time-series data immediately. The PostgreSQL ecosystem (pgAdmin, PostGIS, pgvector, Grafana datasource) is a force multiplier that InfluxDB cannot match.

---

## ADR-004: ARQ over Celery

### Status

Accepted

### Context

URJA requires background task processing for six workloads:

| Task | Frequency | Duration | Data Volume |
|------|-----------|----------|-------------|
| `telemetry_ingest` | On each POST /ingest | <500ms per batch | Up to 1,000 records |
| `carbon_mint` | On demand (daily/weekly) | 2–10 seconds per batch | Monthly generation data |
| `health_scan` | Cron, every 15 minutes | 5–30 seconds for 40 assets | Recent telemetry window |
| `refresh_weather` | Cron, every 6 hours | 1–3 seconds per API call | Forecast data |
| `refresh_pricing` | Cron, every 1 hour | 1–3 seconds per API call | Price signals |
| `daily_rollup` | Cron, daily | 10–60 seconds | Full day's data |

All tasks are lightweight (none exceeds 60 seconds). The API is built on FastAPI (asyncio-native). Redis is already in the stack for caching.

### Options Considered

| Dimension | ARQ | Celery | Plain asyncio |
|-----------|-----|--------|---------------|
| **Runtime** | asyncio-native | thread/multiprocess | Pure async |
| **Broker** | Redis only | Redis, RabbitMQ, SQS, Amazon SQS | None (in-process) |
| **Dependencies** | `redis-py` only | `celery` + `redis`/`rabbitmq` + broker lib | None |
| **Worker memory** | ~5MB per worker | ~50MB per worker | N/A (same process) |
| **Cron support** | Built-in (`cron_jobs`) | Via `celery beat` (separate process) | Via `asyncio` scheduler |
| **Retry logic** | Built-in (`max_tries`, `timeout`) | Built-in (max_retries, countdown) | Manual implementation |
| **Task serialization** | Pickle, JSON, MessagePack | Pickle, JSON, YAML, custom | Direct Python call |
| **Monitoring** | `arq-monitor` (basic) | Flower (full UI) | None built-in |
| **Community** | Small (~2K GitHub stars) | Large (~25K GitHub stars) | N/A |
| **Documentation** | Good, concise | Excellent, extensive | N/A |
| **Latency overhead** | ~1ms per task enqueue | ~50ms per task (with broker connection) | Zero (in-process) |

### Decision

ARQ on Redis for all background task processing. Tasks are defined as async functions in `backend/services/tasks/` and registered with ARQ's `Worker` and `cron_jobs` configuration.

```python
# backend/services/tasks/worker.py
import asyncio
from arq import create_pool
from arq.connections import RedisSettings
from arq.cron import cron

async def startup(ctx):
    ctx['redis'] = await create_pool(RedisSettings())

async def shutdown(ctx):
    await ctx['redis'].close()

class WorkerSettings:
    functions = [
        'backend.services.tasks.telemetry:ingest_batch',
        'backend.services.tasks.carbon:mint_credits',
        'backend.services.tasks.health:run_scan',
        'backend.services.tasks.weather:refresh_forecast',
        'backend.services.tasks.pricing:refresh_prices',
        'backend.services.tasks.rollup:compute_daily',
    ]
    cron_jobs = [
        cron(run_scan, minute=0, second=0),   # every 15 minutes
        cron(refresh_forecast, hour='*/6'),    # every 6 hours
        cron(refresh_prices, hour='*'),        # every hour
        cron(compute_daily, hour=0, minute=5), # daily at 00:05
    ]
    redis_settings = RedisSettings(host='redis', port=6379)
    on_startup = startup
    on_shutdown = shutdown
```

### Consequences

**Positive:**
- Runs entirely on Redis — which is already in the stack for caching. No RabbitMQ dependency, no second message broker to deploy and maintain.
- Asyncio-native — matches FastAPI's async architecture. No thread pool overhead, no GIL contention, no multiprocessing complexity. Tasks share the same event loop model as the API.
- Dramatically lighter on memory and CPU — ~5MB per worker vs. ~50MB for Celery. Critical for the Latitude 3460 CPU-bound constraint and target buyers deploying on 2GB RAM VPS.
- Built-in cron support — no separate `celery beat` process to deploy. A single `WorkerSettings` class defines both the task functions and their schedules.
- Simple retry logic — `max_tries=3` and `timeout=120` are first-class parameters on each task function decorator.
- Enqueuing a task is a single line: `await ctx['redis'].enqueue_job('ingest_batch', data)` — no routing keys, no exchange bindings, no queue declarations.

**Negative:**
- Smaller community than Celery — fewer blog posts, fewer Stack Overflow answers, fewer pre-built integrations (no Flower-style monitoring UI). Mitigation: ARQ is simple enough that most buyers won't need community support. The documentation covers all common patterns.
- Fewer delivery guarantees — ARQ uses Redis streams (not persistent queues like RabbitMQ). If Redis goes down during a task burst, in-flight tasks are lost. Mitigation: Redis persistence (RDB + AOF) is configured. The tasks themselves are idempotent — re-running them is safe.
- No built-in task routing — all tasks go to a single worker pool. There is no way to route "telemetry_ingest" to a high-priority queue and "daily_rollup" to a low-priority queue. Mitigation: for the target workload (<50 assets, 6 tasks, none >60s), a single worker pool is sufficient. If needed, multiple ARQ worker instances can be launched with different function lists.
- No native result backend — ARQ can store job results in Redis, but there's no built-in dashboard for viewing task history, retries, or timing. Mitigation: ARQ job results are logged to the `audit_log` table for traceability.
- ARQ's `Pickle` serialization is a security concern for multi-tenant deployments. Mitigation: URJA uses JSON serialization for all task arguments. The boilerplate is self-hosted — there is no cross-tenant task injection risk.

### Trade-Off Summary

**Chosen: ARQ.** Rejected: Celery. The trade-off is losing Celery's mature ecosystem and delivery guarantees in exchange for dramatically lighter resource usage, asyncio-native operation, and zero additional infrastructure (no RabbitMQ). For a boilerplate running on a 2GB RAM VPS with <50 assets, Celery's feature depth is unnecessary overhead. ARQ's simplicity — Redis-only, async-native, single `WorkerSettings` class — is the right fit for the target deployment profile.

---

## ADR-005: JWT Auth over Session-Based

### Status

Accepted

### Context

URJA serves two authentication use cases:

1. **Human users** (admin, operator, viewer roles) accessing the web dashboard and TUI — need short-lived sessions with refresh capability.
2. **Machine-to-machine (M2M)** consumers — SCADA integrations, external monitoring tools, automation scripts — need long-lived credentials for programmatic API access.

The auth system must be self-contained within the boilerplate — no external identity provider dependency. Buyers should be able to deploy, create a user, and start using the system without configuring OAuth, SAML, or LDAP.

### Options Considered

| Dimension | JWT (Access + Refresh) | Session Cookies (Server-Side) | OAuth2 Proxy |
|-----------|----------------------|------------------------------|--------------|
| **Server-side storage** | None for access tokens (stateless); DB for refresh tokens | Full server-side session store required (DB or Redis) | External proxy handles sessions |
| **Token revocation** | Hard (short TTL mitigates); refresh token can be revoked | Easy (delete session from DB) | Easy (proxy handles it) |
| **API key support** | Natural fit — API key → JWT exchange or direct validation | Awkward — requires session-for-API-key mapping | Proxy handles auth, API forwarded |
| **Deployment simplicity** | High — no session store configuration | Medium — requires session backend (DB or Redis) | Low — requires separate proxy process |
| **Mobile/TUI auth** | Simple — store token in memory/file | Requires cookie jar/session persistence | Requires cookie forwarding |
| **M2M auth** | API keys (native) | Not designed for M2M | Out of scope (proxy) |
| **Statelessness** | Fully stateless for access tokens | Stateful | Stateful (proxy) |
| **CSRF protection** | Not needed (Bearer token in Authorization header) | Required (CSRF token) | Provided by proxy |
| **Implementation complexity** | Medium — JWT signing, refresh rotation, API key hashing | Medium — session store, cookie config, CSRF | Low (if using managed proxy) |

### Decision

JWT-based authentication with the following design:

- **Access token**: JWT signed with HS256, 15-minute TTL. Stored in JavaScript memory (web dashboard) or file (TUI). Sent as `Authorization: Bearer <token>`.
- **Refresh token**: JWT signed with HS256, 7-day TTL. Stored in httpOnly, Secure, SameSite=Strict cookie (web) or secure file (TUI). Hashed SHA-256 stored in the `sessions` table for revocation.
- **API key**: Pre-generated UUID v4 with `urja_` prefix. SHA-256 hash stored in `api_keys` table. Raw key shown once on creation, then irrecoverable. Scoped to `read`, `write`, or `admin`.

Token payload:
```json
{
  "sub": "user_abc123",
  "org": "org_xyz789",
  "roles": ["admin"],
  "iat": 1712345678,
  "exp": 1712346578
}
```

### Consequences

**Positive:**
- No server-side session store for access tokens — the API validates JWTs without querying the database on every request. This reduces database load and latency.
- Stateless JWT validation means any API container can authenticate any request without shared state — important if the buyer horizontally scales (e.g., behind a load balancer).
- API keys are a natural fit for M2M use cases — SCADA systems push telemetry via API keys, Grafana dashboards pull data via API keys, automation scripts trigger carbon minting via API keys.
- httpOnly cookies for refresh tokens prevent XSS-based token theft. Access tokens in memory mean they are not persisted to `localStorage` (a common vulnerability).
- Short-lived access tokens (15 min) limit the blast radius of a compromised token. An attacker has at most 15 minutes to use a stolen access token.
- Refresh token rotation (issue new refresh token on each refresh) with old token revocation (stored in DB) limits refresh token abuse. If a refresh token is stolen, the next rotation invalidates the old one for that user.

**Negative:**
- Cannot revoke individual access tokens before expiry. If an admin revokes a user's access, their existing access tokens remain valid for up to 15 minutes. Mitigation: 15-minute TTL is short enough that this is acceptable. The refresh token is revoked immediately (session row marked as revoked), preventing new access tokens from being issued.
- JWT signing key must be kept secret. If leaked, an attacker can forge arbitrary access tokens. Mitigation: the HS256 secret is stored in an environment variable (`JWT_SECRET`), never hardcoded, never committed. The secret is rotated in the deployment guide.
- Token storage in browser memory means the user must re-authenticate after page refresh (access token lost). Mitigation: the frontend transparently uses the refresh token cookie to obtain a new access token. The user experiences a seamless session as long as the refresh token is valid.
- API keys are long-lived by nature — if leaked, they grant access until explicitly revoked. Mitigation: API keys have configurable expiry (`expires_at` column). Key usage is logged in the audit log. Operators can revoke keys from the settings UI instantly.
- Session table grows unboundedly with refresh token entries. Mitigation: a daily ARQ cron job cleans up expired sessions (`DELETE FROM sessions WHERE expires_at < now() - INTERVAL '7 days'`).

### Trade-Off Summary

**Chosen: JWT access + refresh tokens + API keys.** Rejected: Server-side session cookies. The trade-off is giving up immediate token revocation capability in exchange for stateless authentication that works naturally across web, TUI, and M2M consumers. API keys are a first-class citizen — not an afterthought bolted onto a session-based system. The 15-minute access token TTL and refresh token revocation list provide adequate security for a self-hosted boilerplate.

---

## ADR-006: Next.js over Reflex

### Status

Accepted

### Context

URJA needs a web dashboard with KPI cards, real-time charts (Recharts), an interactive map (Leaflet), data tables, and forms. The frontend must be statically analyzable, SEO-friendly for the landing/login pages, and fast for end users. The target buyer is a developer or integrator who expects to customize the frontend.

The team is a solo developer with proficiency in both Python (FastAPI, Textual) and TypeScript/React (Next.js). The question is whether to use a Python-native full-stack framework (Reflex, which uses React under the hood but lets developers write UI in Python) or stay with the standard Next.js + TypeScript stack.

### Options Considered

| Dimension | Next.js 16 (App Router) | Reflex (Python) | Plain React (Vite) |
|-----------|------------------------|-----------------|-------------------|
| **Developer language** | TypeScript/JSX | Python (pynecone) | TypeScript/JSX |
| **Rendering** | RSC (Server Components) + CSR | CSR (SPA model) | CSR (SPA model) |
| **SEO / SSR** | Built-in (Server Components, SSR) | Limited (CSR-first, SSG possible) | Requires Next.js or Remix |
| **Routing** | File-based (App Router) | File-based (`pages/`) | React Router (manual) |
| **Ecosystem** | Largest React ecosystem (Recharts, Leaflet, shadcn/ui, SWR) | Growing but small — limited library support | Same as Next.js (no SSR) |
| **Type safety** | TypeScript — compile-time safety | Python type hints — runtime only (no TS-level guarantees for component props) | TypeScript |
| **API layer** | Client components call API directly | Python functions call FastAPI directly | API calls from JavaScript |
| **Market adoption** | ~40% of web developers | ~0.1% — niche, early-stage | ~60% (React ecosystem) |
| **Boilerplate buyer expectation** | Expected — 90% of boilerplate buyers expect Next.js | Surprising — buyers would be hesitant to learn Reflex | Acceptable but less common |
| **Learning curve for buyer** | Low (React is widely known) | Medium (new framework concepts) | Low |
| **Bundle size** | Optimized (RSC, code splitting) | Larger (full Python runtime not in browser — React bundle only) | Depends on setup |
| **Build tooling** | Turbopack, SWC, TypeScript compiler | Webpack-based (slower) | Vite (fast) |
| **Maintenance surface** | 3 files (layout, page, component) | 1 file (Python component — but mixing UI + logic in single file is harder to maintain at scale) | More boilerplate (routing, state mgmt) |

### Decision

Next.js 16 with App Router, TypeScript, Tailwind v4, shadcn/ui, Recharts, and react-leaflet. The frontend is a separate `frontend/` directory that communicates with the FastAPI backend via REST API calls.

Architecture:
- **Server Components** (default): Landing page, login form shell, layout, navigation — minimal JavaScript delivered to browser.
- **Client Components** (explicit `"use client"`): Dashboard components (KPI cards, charts, map, tables) — interactive UI that requires JavaScript.
- **SWR** (stale-while-revalidate) for data fetching — provides caching, deduplication, and auto-revalidation on a configurable interval (matching the 15s polling architecture).

### Consequences

**Positive:**
- Maximum market reach — 90% of boilerplate buyers expect Next.js. The job market for Next.js developers is the largest among web frameworks. Buyers who want to customize URJA's frontend can hire from a vast talent pool.
- Server Components reduce JavaScript bundle size significantly — initial page load for a KPI dashboard is smaller than a comparable SPA. Loading states (Skeleton components) render from the server before the client hydrates.
- shadcn/ui provides copy-paste components (not a dependency) — buyers can modify any component without fighting the framework's abstraction. Tailwind v4 utility classes give fine-grained control over styling.
- Recharts is composable and React-native — `AreaChart` for generation curves, `ComposedChart` for duck curves with bar overlays, `LineChart` for health trends. All are pure React components with responsive containers.
- react-leaflet wraps Leaflet maps in React components — markers with popups for inverter locations, color-coded by health status.
- SWR provides automatic polling (every 15s) with deduplication — matching the TUI's polling interval. Cache-first rendering means the dashboard feels instant even on slow connections.
- TypeScript provides compile-time type safety for component props, API responses, and state management. The shared types between frontend and backend (via OpenAPI codegen) prevent contract drift.
- Next.js 16's Turbopack provides fast HMR during development — critical for iteration speed during dashboard development.

**Negative:**
- Larger frontend bundle than a pure-terminal application — but this is a web dashboard, not a CLI tool. The bundle is comparable to any modern admin dashboard.
- Requires TypeScript expertise — buyers who only know Python cannot customize the frontend without learning React. Mitigation: the PRD's target personas (consultants, integrators, developers) are all expected to have some frontend proficiency. The TUI provides a Python-only alternative for operators.
- Two codebases (backend Python, frontend TypeScript) means two sets of dependencies, two build systems, two test frameworks. Mitigation: Docker Compose manages both containers. Shared OpenAPI spec bridges the two codebases.
- React Server Components are a paradigm shift over traditional React — the mental model of "what runs on server vs. client" takes time to learn. Mitigation: URJA follows a simple pattern — server components for data fetching, client components for interactivity. The pattern is documented in the codebase conventions.
- Next.js 16 is bleeding-edge — API surface may shift during development. Mitigation: pin `next` version in `package.json`. Test version upgrades on a branch before merging.

### Comparison: Reflex (if Python-only were preferred)

If the team were Python-only, Reflex would be an interesting option — write UI in Python, and Reflex transpiles it to React. However:

- Reflex's component library is small compared to shadcn/ui. Implementing a professional dashboard requires building custom chart wrappers, table components, and map integrations from scratch.
- Reflex generates a React SPA — no Server Components, no streaming SSR. Initial load performance is worse than Next.js.
- The Reflex community is early-stage. Finding solutions for edge cases (custom Leaflet markers, Recharts tooltips with custom formatting) would require reading Reflex source code.
- Boilerplate buyers would be skeptical — "Python in the frontend" is not a proven model for production dashboards.

For a solo developer building a $149 boilerplate, Next.js is the safer bet. Reflex might be viable in 2–3 years if the ecosystem matures, but it's not ready for a production boilerplate today.

### Trade-Off Summary

**Chosen: Next.js 16 with TypeScript.** Rejected: Reflex (Python-only frontend). The trade-off is accepting TypeScript as a second language in the codebase in exchange for maximum market reach, the richest UI component ecosystem (shadcn/ui, Recharts, Leaflet), and Server Components for performance. Reflex's Python-native approach is appealing in theory but lacks the ecosystem maturity to deliver a professional dashboard in the same development time.

---

## ADR-007: Textual TUI over Web-Only

### Status

Accepted

### Context

URJA targets farm operators and ops teams who work on-site — in control rooms, near equipment, or in environments where a graphical web browser is not ideal. These users spend their day in terminals: SSH sessions, command-line tools, and terminal multiplexers (tmux, screen). A terminal UI is an interface they are already in.

The competitive landscape analysis showed that no renewable energy management product offers a terminal dashboard. Power Factors, Fluence, Wärtsilä, and Tesla Autobidder are all web-only. A terminal dashboard is a genuine differentiator for the boilerplate market.

The Textual framework (Python) enables building TUI applications with widgets, CSS-like styling, and async event loops. It can also run in a browser via `textual-web`, making it accessible to users who prefer web interfaces but want the TUI experience.

### Options Considered

| Dimension | Textual TUI + Web Dashboard | Web-Only Dashboard | CLI Tools (Click + Rich) |
|-----------|---------------------------|-------------------|--------------------------|
| **Interface** | Terminal + Browser (via textual-web) | Browser only | Terminal only |
| **Interaction** | Keyboard-driven (Tab, /search, arrows) | Mouse + keyboard | Command-based (flags, subcommands) |
| **Real-time updates** | 15s polling (async widget refresh) | 15s polling (SWR) | No built-in refresh |
| **Development effort** | ~3 weeks for 4 screens | Already built (Next.js) | ~2 weeks for 10 CLI commands |
| **Differentiator** | Strong — no competitor has it | Standard — expected | Weak — every project has CLI |
| **Ops team appeal** | High — terminal is their habitat | Medium — browser-based | Medium — CLI is functional but limited |
| **Learning curve** | Low for ops (keyboard-driven), Medium for dev (Textual widgets) | Low (familiar web UX) | Low (standard CLI patterns) |
| **Accessibility** | Terminal-based (screen readers work with terminals) | Web-based (WCAG compliance) | Terminal-based |
| **Maintenance surface** | Additional Python codebase (~1,500 lines for 4 screens) | None (web is the default) | Minimal (~500 lines of Click commands) |

### Decision

Build a first-class Textual TUI as the `dashboard-tui/` package in the URJA monorepo. The TUI runs as a standalone Python application (or Docker container) that polls the FastAPI REST API and renders real-time data in the terminal. It runs natively in terminals AND in browsers via `textual-web`.

Four TUI screens:

1. **Overview Screen**: Live MW generation data table, header row with key stats (total MW, curtailment %, revenue lost today, active alerts count), and an alert strip showing the 5 most recent alerts.
2. **Curtailment Screen**: Table of active/recent curtailment events with revenue impact, revenue lost static widget, dispatch decision log (RichLog widget).
3. **Carbon Screen**: Last 10 credit issuances table, portfolio summary totals.
4. **Health Screen**: Asset health scores table (sorted by score ascending), active alerts count badge.

All screens share a common navigation header and poll the API at a configurable interval (default 15s). Keyboard-driven navigation: `Tab` to switch panels, `/` to search assets, `q` to quit.

```python
# Example screen stub — dashboard-tui/screens/overview.py
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, DataTable, Static
from textual.containers import Horizontal, Vertical

class OverviewScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header()
        yield Horizontal(
            Static(id="total-mw", classes="stat"),
            Static(id="curtailment-pct", classes="stat"),
            Static(id="revenue-lost", classes="stat"),
            Static(id="active-alerts", classes="stat"),
        )
        yield DataTable(id="generation-table")
        yield Footer()

    async def on_mount(self) -> None:
        self.set_interval(15, self.refresh_data)
        await self.refresh_data()
```

### Consequences

**Positive:**
- **Strong differentiator** — no competitor offers a terminal dashboard. The TUI is a headline feature in the README and Gumroad listing. It appeals directly to ops teams who live in terminals.
- **Same codebase, two surfaces** — the TUI and web dashboard share the same FastAPI backend. Build the API once, consume it from two frontends. No backend duplication.
- **Textual-web bridge** — the TUI runs in browsers too (`textual-web` serves the TUI over WebSocket). Operators who prefer browsers can access the TUI experience without opening a terminal.
- **Keyboard-driven efficiency** — ops teams navigate the TUI faster than clicking through a web dashboard. `/` to search, arrows to scroll, `q` to quit. No mouse needed.
- **Low bandwidth** — terminal output is text + ANSI colors. The TUI works over SSH from a remote site with poor internet connectivity.
- **Python-native** — the TUI shares Python types with the backend. The API client layer uses `httpx` with the same Pydantic models. No cross-language serialization.
- **Offline-capable** — the TUI can cache the last known state and display it if the API is unreachable (with an `[OFFLINE]` indicator). Useful for operators in areas with intermittent connectivity.

**Negative:**
- **Additional maintenance surface** — ~1,500 lines of Python for 4 screens that must be kept in sync with the web dashboard's API consumption patterns. If an API endpoint changes, both frontends must be updated. Mitigation: shared API client types in `backend/api/schemas/` — any API change that breaks the TUI also breaks the web dashboard (caught at compile/test time).
- **Fraction of buyers will use the TUI** — the vast majority will access the web dashboard. The TUI development effort (~3 weeks) could have been spent on web dashboard features. Mitigation: the TUI is a headline differentiator for marketing (Dev.to posts, X/Twitter build-in-public content) even if only 20–30% of buyers use it daily.
- **Textual is a young framework** — v1.0 was released in 2024. API changes, bugs, and edge cases are more common than with mature web frameworks. Mitigation: pin Textual version. Test TUI screens with integration tests (snapshot testing against Textual's `pilot` API).
- **Not all terminals are equal** — Windows Command Prompt has poor ANSI color support. macOS Terminal and Linux (GNOME Terminal, kitty, Alacritty) work well. Mitigation: document that the TUI is optimized for Linux/macOS terminals. WSL2 on Windows works. Native Windows terminal is best-effort.
- **TUI cannot match web dashboard's visual richness** — no charts (Recharts), no maps (Leaflet), no rich animations. The TUI is text-only with color coding. Mitigation: the TUI and web dashboard serve different use cases. The web dashboard is for deep analysis and configuration. The TUI is for "at-a-glance" monitoring. They complement each other.

### Trade-Off Summary

**Chosen: Textual TUI as a first-class interface alongside the web dashboard.** Rejected: Web-only. The trade-off is accepting ~3 weeks of additional development time and ~1,500 lines of maintenance surface for a genuine market differentiator that no competitor offers. The TUI transforms URJA from "yet another web dashboard" into a control plane that ops teams genuinely enjoy using. Even if only 20% of buyers use the TUI daily, it drives purchasing decisions through demo appeal and Dev.to content.

---

## ADR-008: TimescaleDB Continuous Aggregates over Application-Level Rollups

### Status

Accepted

### Context

URJA's dashboards query time-bucketed summaries: hourly generation curves, daily energy totals, monthly carbon credits, and weekly health trends. These are computed from raw telemetry data stored at 15-minute granularity.

Two approaches exist for pre-computing these summaries:

1. **Application-level rollups**: A scheduled task (ARQ cron job) reads raw telemetry, computes aggregates, and writes results to summary tables.
2. **Database-level rollups**: TimescaleDB continuous aggregates — declarative materialized views that the database refreshes automatically in the background.

The raw telemetry table (`telemetry_generation`) grows at ~1.4M rows/year for a 50MW farm. Querying `SUM(generation_kw)` over a 12-month window from raw data takes 5–30 seconds depending on chunk compression state. This is too slow for dashboard loading.

### Options Considered

| Dimension | TimescaleDB Continuous Aggregates | Application-Level Rollups (ARQ) | PostgreSQL Materialized Views (Manual Refresh) |
|-----------|-----------------------------------|--------------------------------|-----------------------------------------------|
| **Refresh mechanism** | Automatic, incremental, in-database | Scheduled task in application code | Manual `REFRESH MATERIALIZED VIEW` via cron |
| **Recency** | End offset configurable (e.g., 1 hour lag) | Depends on schedule (e.g., hourly) | Depends on refresh schedule |
| **Correctness** | TimescaleDB handles late-arriving data automatically | Must manually handle late data (recompute window) | Full refresh recalculates everything |
| **Performance** | Incremental — only new/modified chunks refreshed | Full recompute or complex delta tracking | Full table scan on refresh |
| **Query syntax** | Standard SQL — query the materialized view like a table | Query application summary tables | Standard SQL | 
| **Backfill** | Automatic — continuous aggregate covers entire hypertable | Must script backfill logic | Full refresh covers everything |
| **Maintenance** | Zero — TimescaleDB manages refresh scheduling | ARQ cron job + manual recompute logic | Cron job calling `REFRESH MATERIALIZED VIEW` |
| **Dependency** | TimescaleDB-specific feature | Works on any PostgreSQL | Works on any PostgreSQL |
| **Debugging** | `timescaledb_information` views for policy/refresh status | Application logs | PostgreSQL log |

### Decision

TimescaleDB continuous aggregates for all time-bucketed summaries. Four continuous aggregates defined:

| Name | Source | Bucket | Refresh Policy | Used By |
|------|--------|--------|----------------|---------|
| `hourly_generation` | `telemetry_generation` | 1 hour | Every 1 hr, 3-hr lag | Duck curve, hourly charts |
| `daily_generation` | `hourly_generation` | 1 day | Every 1 day, 1-day lag | Dashboard KPI, daily reports |
| `daily_curtailment` | `curtailment_events` | 1 day | Every 1 day, 1-day lag | Curtailment summary cards |
| `daily_health` | `health_metrics` | 1 day | Every 1 day, 1-day lag | Health trend charts |

```sql
-- Example: hourly_generation
CREATE MATERIALIZED VIEW hourly_generation
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', ts) AS bucket,
    organization_id,
    asset_id,
    SUM(generation_kw) * 0.25 AS energy_kwh,
    AVG(generation_kw) AS avg_kw,
    MAX(generation_kw) AS peak_kw,
    MIN(generation_kw) AS min_kw,
    COUNT(*) AS reading_count
FROM telemetry_generation
GROUP BY bucket, organization_id, asset_id
WITH NO DATA;

SELECT add_continuous_aggregate_policy('hourly_generation',
    start_offset    => INTERVAL '3 days',
    end_offset      => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour'
);
```

The continuous aggregate chain is:
```
telemetry_generation (raw, 15-min)
    │
    └──▶ hourly_generation (continuous aggregate, 1-hr)
            │
            └──▶ daily_generation (continuous aggregate, 1-day, from hourly_generation)
```

### Consequences

**Positive:**
- **Automatic, incremental refresh** — TimescaleDB tracks which chunks have changed and only refreshes the affected buckets. No full table scans, no manual scheduling logic, no delta tracking in application code.
- **Correct with late-arriving data** — the `end_offset` parameter (e.g., `1 hour`) means the aggregate does not include data from the last hour, giving telemetry time to arrive. TimescaleDB automatically re-aggregates chunks when new data arrives within the lag window.
- **Sub-millisecond query times** — dashboard queries hit the continuous aggregate (1,000–10,000 rows for a year of hourly data) instead of the raw hypertable (1.4M rows). Dashboard loads in <100ms instead of 5–30 seconds.
- **Zero application code** — continuous aggregates are defined in the migration SQL. The application never manages rollups. No ARQ cron jobs, no summary tables, no backfill scripts. Less code = fewer bugs.
- **Hierarchical aggregation** — `daily_generation` aggregates from `hourly_generation` (not raw data), creating a hierarchical refresh that is faster than recomputing from raw.
- **Transparent to queries** — applications query continuous aggregates as if they were regular tables. No special query syntax. If a query asks for hourly data, the application queries `hourly_generation` instead of `telemetry_generation`.

**Negative:**
- **TimescaleDB-specific feature** — continuous aggregates are not standard PostgreSQL. If a buyer wants to migrate away from TimescaleDB to plain PostgreSQL, they lose continuous aggregates and must implement application-level rollups. Mitigation: the boilerplate is tied to TimescaleDB for its hypertable design — this is an accepted dependency.
- **Refresh lag** — continuous aggregates are always slightly stale. `hourly_generation` has a 1-hour lag (`end_offset`). Dashboard queries for "the last 15 minutes" must query raw data. Mitigation: dashboard queries for "last 24 hours" use the continuous aggregate (1-hour lag is acceptable). The "latest reading" KPI cards query raw data with a `DISTINCT ON` pattern — this is fast because it hits the `(asset_id, ts DESC)` index and reads only the most recent chunk.
- **No fine-grained control over refresh timing** — TimescaleDB's refresh scheduler runs in the background. There is no way to say "refresh at 00:05 daily" — only "refresh every 1 day." Mitigation: the offset parameters provide enough control. If exact timing matters, schedule the query that reads the aggregate (the API) rather than the aggregate refresh itself.
- **Storage overhead** — continuous aggregates store materialized data in addition to raw data. For `hourly_generation`, this is ~1/4 the raw data size (1-hour buckets vs. 15-minute raw). `daily_generation` adds another ~1/24 of hourly. Total overhead: ~30% of raw data size. Post-compression: negligible (<1MB). Mitigation: compression policies apply to continuous aggregates as well.
- **Changes require drop + recreate** — changing a continuous aggregate definition requires dropping and recreating it. During the recreate window, the aggregate is unavailable and queries fall back to raw data. Mitigation: the migration guide covers this pattern. Continuous aggregates are recreated from raw data, which is always available.

### Trade-Off Summary

**Chosen: TimescaleDB continuous aggregates.** Rejected: Application-level rollups via ARQ cron jobs. The trade-off is coupling to a TimescaleDB-specific feature in exchange for automatic, correct, zero-maintenance aggregation. Application-level rollups require custom logic for incremental refresh, late-arriving data handling, and backfill — all of which are bugs waiting to happen. Continuous aggregates are declarative — define what you want and TimescaleDB keeps it current. For a boilerplate where buyers should not need to troubleshoot aggregation scripts, continuous aggregates are the right choice.

---

## ADR-009: Docker Compose over Kubernetes

### Status

Accepted

### Context

URJA must be deployable by a single developer on a single server. The target deployment environment is a $10–$20/month VPS (2 vCPUs, 2–4 GB RAM) or an on-prem Linux server. The buyer is a clean energy consultant, system integrator, or farm operator — not a DevOps engineer.

The system has five containers:

| Container | Image | Purpose |
|-----------|-------|---------|
| `api` | Built from `./backend/Dockerfile` | FastAPI REST API |
| `frontend` | Built from `./frontend/Dockerfile` | Next.js web dashboard |
| `tui` | Built from `./dashboard-tui/Dockerfile` | Textual terminal UI |
| `db` | `timescale/timescaledb:2.17-pg16` | PostgreSQL + TimescaleDB |
| `redis` | `redis:7-alpine` | Redis for ARQ + caching |

The deployment target must work on: Ubuntu 24.04, macOS 15, Windows WSL2, and any Linux distribution with Docker Engine.

### Options Considered

| Dimension | Docker Compose | Kubernetes (K8s) | Single Binary (PyInstaller) | Nomad / Docker Swarm |
|-----------|---------------|------------------|---------------------------|----------------------|
| **Complexity** | Low — one `docker-compose.yml` | High — cluster setup, ingress, RBAC, storage classes | Lowest — single binary | Medium |
| **Resource overhead** | ~1 GB RAM (containers) | ~2 GB RAM just for control plane | ~500 MB (no container runtime) | ~500 MB (agent + server) |
| **Learning curve** | Low — any developer has used Docker Compose | Very high — requires Kubernetes expertise | Lowest — run the binary | Medium |
| **High availability** | None — single node | Built-in (replicas, self-healing) | None — single process | Built-in (Swarm mode) |
| **Rolling updates** | Manual (docker compose restart) | Built-in (rolling update strategy) | Manual (restart binary) | Built-in |
| **Auto-scaling** | None | Built-in (HPA) | None | Swarm (manual scale) |
| **Secret management** | .env file | Secrets + ConfigMap | .env file | Docker secrets |
| **Persistent storage** | Docker volumes | PVC + storage class | Local filesystem | Docker volumes |
| **Portability** | Universal (Docker everywhere) | Cluster-dependent | Universal (single binary) | Docker-based |
| **Debugging** | `docker compose logs` | `kubectl logs`, `stern`, `k9s` | Application logs | `docker service logs` |
| **Offline deploy** | Yes (if images cached/pulled) | No (requires registry) | Yes | Yes |

### Decision

Docker Compose for v1. A single `docker-compose.yml` (or `docker compose.yml`) in the repository root that all five containers reference. A `docker-compose.override.yml` for development (hot reload, debug ports) and a `docker-compose.prod.yml` for production (health checks, resource limits, restart policies).

```yaml
# docker-compose.yml (simplified)
version: "3.9"
services:
  db:
    image: timescale/timescaledb:2.17-pg16
    environment:
      POSTGRES_DB: urja
      POSTGRES_USER: urja
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD", "pg_isready", "-U", "urja"]
      interval: 10s

  redis:
    image: redis:7-alpine
    volumes:
      - redisdata:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s

  api:
    build: ./backend
    depends_on:
      db: { condition: service_healthy }
      redis: { condition: service_healthy }
    environment:
      DATABASE_URL: postgresql+asyncpg://urja:${DB_PASSWORD}@db:5432/urja
      REDIS_URL: redis://redis:6379/0
      JWT_SECRET: ${JWT_SECRET}

  frontend:
    build: ./frontend
    ports: ["3000:3000"]
    depends_on: [api]

  tui:
    build: ./dashboard-tui
    ports: ["8080:8080"]
    depends_on: [api]
    environment:
      URJA_API_URL: http://api:8000/api/v1

volumes:
  pgdata:
  redisdata:
```

### Consequences

**Positive:**

- **Single-command deployment** — `docker compose up -d` starts everything. The buyer runs one command and has a fully operational control plane. This is the #1 requirement for a boilerplate — frictionless first run.
- **Widely understood** — Docker Compose is the most common container orchestration tool for local development and small-scale production. Every developer knows it; every CI system supports it.
- **Low resource overhead** — no Kubernetes control plane consuming 2 GB RAM. The five URJA containers run comfortably on a 2 GB RAM VPS (database: 512 MB, API: 256 MB, frontend: 128 MB, TUI: 64 MB, Redis: 64 MB = ~1 GB total, leaving headroom).
- **Volume management** — `pgdata` and `redisdata` Docker volumes provide easy backup/restore: `docker run --volumes-from urja_db -v $(pwd):/backup ubuntu tar cvf /backup/pgdata.tar /var/lib/postgresql/data`.
- **Environment variables** — one `.env` file for configuration. Buyers copy `.env.example` to `.env`, edit secrets, and run `docker compose up`. No RBAC, no ConfigMaps, no secrets API.
- **Offline deploy** — buyers can download Docker images on a connected machine, save them as tarballs, transfer them to an air-gapped server, and `docker load` them. This is a real requirement for on-prem energy infrastructure.
- **Health checks** — Docker Compose's `depends_on: condition: service_healthy` ensures containers start in the correct order. No init containers, no sidecars, no startup probes.

**Negative:**

- **No high availability** — all containers run on a single node. If the server goes down, URJA goes down. Mitigation: target buyers run URJA for monitoring and optimization, not for real-time control. 30 minutes of downtime for patching is acceptable. For buyers who need HA, the architecture is simple enough to run behind a load balancer with a hot-standby server and PostgreSQL replication.
- **No rolling updates** — `docker compose up -d` stops and restarts containers. There is a brief service interruption. Mitigation: for a monitoring dashboard, <30 seconds of downtime during updates is acceptable. The TUI reconnects automatically after the API restarts.
- **No auto-scaling** — cannot scale the API container horizontally to handle traffic spikes. Mitigation: target traffic is <200 requests/hour. A single API container with 256 MB RAM handles this comfortably. If a buyer needs to scale, they can use `docker compose up -d --scale api=3` behind a reverse proxy — Compose supports basic scaling.
- **No service discovery** — Docker Compose uses DNS-based service discovery within the Compose network, which works for the 5-container setup but does not provide advanced features (circuit breakers, retry budgets, load shedding). Mitigation: these patterns are over-engineered for the target deployment size. If they become necessary, the buyer can add a reverse proxy (Caddy/Traefik) as a sidecar container.
- **No built-in monitoring** — Docker Compose does not provide container metrics, log aggregation, or alerting. Mitigation: the boilerplate includes a `docker-compose.monitoring.yml` override that adds Prometheus + Grafana (opt-in). Documentation covers how to set up basic monitoring.
- **Harder to version infrastructure** — Compose files are YAML committed to the repo, but managing environment-specific overrides (`docker-compose.override.yml`, `docker-compose.prod.yml`) can become unwieldy with many environments. Mitigation: URJA targets 1–2 environments (development, production). The override pattern is well-understood.

### Future: Kubernetes Helm Chart (v2)

For Enterprise tier buyers who need HA, a Kubernetes Helm chart is a v2 roadmap item. The modular monolith architecture makes the transition straightforward:

- `api` → Deployment (2+ replicas) + Service + Ingress
- `frontend` → Deployment (2+ replicas) + Service + Ingress
- `tui` → Deployment (1 replica) + Service (for textual-web)
- `db` → StatefulSet with PVC (TimescaleDB operator) or managed RDS/Crunchy Bridge
- `redis` → StatefulSet with PVC or managed ElastiCast/Memorystore

The Helm chart is a consulting deliverable for the Enterprise tier ($499), as it requires buyer-specific configuration (cloud provider, storage class, ingress domain, TLS certificates).

### Trade-Off Summary

**Chosen: Docker Compose.** Rejected: Kubernetes. The trade-off is giving up high availability, rolling updates, and auto-scaling in exchange for single-command deployment that works on any Linux server with Docker. For a $149–$249 boilerplate sold to solo developers and small teams, Kubernetes is excessive infrastructure. The target buyers deploy on a single VPS — they need `docker compose up`, not `kubectl apply -f manifests/`. Enterprise buyers who need HA pay for the consulting call to set up Kubernetes.

---

## ADR-010: Seed Data as SQL Scripts over Application Fixtures

### Status

Accepted

### Context

URJA ships with sample data for a 50MW solar farm with 12 months of operational history. The "wow moment" — seeing a fully populated dashboard — must happen within 5 minutes of running `docker compose up`. The seed data includes:

- 1 organization, 3 users, 4 sites, 40 inverters (as assets), 4 batteries, 4 meters
- 1,402,560 generation telemetry rows (12 months, 15-min intervals, 40 inverters)
- 35,040 weather telemetry rows
- ~300 curtailment events
- ~5,000 carbon credits (12 batches)
- 1,402,560 health metrics rows
- 35,040 grid price rows
- 50 maintenance work orders
- 4 dispatch rules

Total: ~2.9M rows across all tables (~300 MB uncompressed, ~23 MB compressed).

The question is what mechanism to use for loading this data on first run.

### Options Considered

| Dimension | SQL Seed Scripts (`.sql` files) | Python Fixtures (seed.py + factories) | JSON/CSV Import (COPY FROM) | Hybrid (SQL schema + Python data gen) |
|-----------|-------------------------------|---------------------------------------|----------------------------|---------------------------------------|
| **Load speed** | Fastest — `psql -f seed.sql` or `pg_restore` on a dump | Slowest — ORM inserts row-by-row | Fast — bulk COPY is near-C speed | Medium — Python generates then COPY |
| **Determinism** | Fully deterministic — same SQL file = same data | Non-deterministic unless random seed is fixed | Deterministic if JSON/CSV is static | Deterministic (fixed seed) |
| **Maintainability** | Hard — 2.9M rows in SQL is unreadable | Easy — Python generators with factories | Medium — large JSON files are unreadable | Medium — split across SQL + Python |
| **Change tracking** | Git diff shows changed SQL lines | Git diff shows changed Python code | JSON/CSV diffs are large and unreadable | Mixed |
| **Repo size** | Large (~50MB SQL file → Git LFS) | Small (~2KB seed.py + ~500B factory code) | Large (~50MB JSON/CSV → Git LFS) | ~15MB (compressed SQL dump) |
| **Portability** | Any PostgreSQL client can load it | Requires Python environment + ORM | Requires PostgreSQL COPY or `\copy` | Requires Python + PostgreSQL |
| **Regeneration** | Must re-export SQL script if data changes | Run seed.py to regenerate | Must re-export JSON/CSV | Run seed.py to regenerate |
| **Compression** | Yes — gzip the SQL file (~3MB compressed) | Not applicable | Yes — gzip JSON/CSV | Yes — compress the final SQL dump |

### Decision

Hybrid approach:

1. **SQL schema + continuous aggregate definitions**: Traditional Alembic migrations (same as any URJA deployment).
2. **Compressed SQL dump** (`seed/seed_data.sql.gz`): Pre-generated dump containing all seed data in SQL `INSERT` statements. Loaded via `gunzip -c seed_data.sql.gz | psql -U urja -d urja`.
3. **Seed generation script** (`scripts/seed_generator.py`): Python script that generates the seed data using deterministic random (fixed seed). This script is not run by buyers — it is used by developers to regenerate the SQL dump when the schema changes.

The seed data is shipped as a compressed SQL dump stored in the `seed/` directory, tracked with Git LFS. On `docker compose up`, a startup script (`scripts/seed.py`) checks if the database is empty and runs the SQL dump if needed.

```python
# scripts/seed.py (simplified — runs on container startup)
async def seed_if_empty():
    async with async_session() as session:
        result = await session.execute(
            text("SELECT COUNT(*) FROM assets")
        )
        count = result.scalar()
        if count > 0:
            logger.info("Database already seeded — skipping")
            return
    
    logger.info("Seeding database with sample data...")
    proc = await asyncio.create_subprocess_exec(
        "sh", "-c",
        "gunzip -c /app/seed/seed_data.sql.gz | "
        "psql $DATABASE_URL",
    )
    await proc.wait()
    logger.info(f"Seed complete (exit code: {proc.returncode})")
```

### Consequences

**Positive:**

- **Fastest possible load** — `pg_restore` from a compressed dump or `psql` from a compressed SQL file is 10–100x faster than ORM-based inserts. The 2.9M row dataset loads in ~30 seconds instead of 5–10 minutes. Speed matters for the "wow moment."
- **Fully deterministic** — every buyer gets exactly the same data. No random variation, no "my dashboard looks different from the screenshot in the README." The 50MW solar farm always produces the same generation curve, curtailment events, and carbon credits.
- **Minimal code path** — the seed script checks if the DB is empty and runs a SQL command. No ORM configuration, no Pydantic models, no factory boy patterns. Fewer dependencies, fewer failure points.
- **Easily inspectable** — developers can decompress the SQL file and read the exact data. "Why did carbon credit #423 have a retired status?" — search the SQL file.
- **Test reproducibility** — integration tests can load the seed data and assert against known values. "The daily generation for asset X on 2026-01-15 should be exactly 42,500 kWh."

**Negative:**

- **Large repo size** — the compressed SQL dump is ~15MB (or ~3MB with higher compression). This is too large for a regular Git repository but manageable with Git LFS. Mitigation: Git LFS tracks the `seed/` directory. The initial `git clone` downloads LFS files lazily — buyers pull the seed data on first `docker compose up`.
- **Schema coupling** — if the database schema changes (new column, renamed column, new table), the seed SQL dump must be regenerated. The INSERT statements reference specific columns — any schema drift breaks the seed load. Mitigation: the `seed_generator.py` script is updated alongside migrations, and CI validates that the seed loads cleanly after migrations.
- **Static data** — the seed data does not reflect the current date. The dashboard shows "12 months ago" as the seed date range. Mitigation: the seed data covers 2025-07-01 to 2026-07-01. On launch (late 2026), this shows data ending "a few months ago." Buyers who deploy in 2027 see data ending ~6 months ago. Acceptable — the purpose is to show a populated dashboard, not real-time accuracy. The `seed_generator.py` can be updated yearly to shift the date range.
- **No "today's data" on day 1** — because the seed data is static, the "latest reading" KPI card shows stale data immediately. Mitigation: once the buyer connects real telemetry (or even one test POST), the dashboard starts showing live data alongside the seeded history. The seed data provides historical context; live telemetry provides current context.
- **Git LFS bandwidth costs** — storing 15MB seed files on GitHub LFS costs ~$0.50/month for bandwidth. For a $149–$499 product, this is negligible. Mitigation: the seed data can also be distributed as a separate download (Google Drive, Gumroad attached file) for buyers who want to save LFS bandwidth.

### Alternative Considered: Python Fixtures with Factory Boy

Application fixtures using SQLAlchemy async factories and `factory_boy` were rejected because:

1. **2.9M rows via ORM is slow** — at ~500 inserts/second (async session with batch flush), the seed takes ~100 minutes to complete. Buyers will not wait that long for a demo.
2. **Non-deterministic** — even with a fixed random seed, ORM-level non-determinism (auto-generated UUIDs, timestamps) creates slight variations between runs. This breaks test assertions.
3. **Python dependency** — the seed script requires the full Python environment (SQLAlchemy, Pydantic, asyncio, ORM models to be importable). If the codebase doesn't compile, the seed script cannot run. This couples seed loading to application health.
4. **Hard to debug** — if a seed fails at row 1,402,559, the error message is a SQLAlchemy traceback. With a SQL dump, the failing INSERT statement is directly visible.

### Trade-Off Summary

**Chosen: Compressed SQL dump generated by a Python script.** Rejected: Application-level Python fixtures. The trade-off is accepting a ~15MB file in the repository (tracked via Git LFS) in exchange for deterministic, fast-loading seed data that works regardless of the application code's health. For a boilerplate where the first-run experience is the critical "wow moment," loading 2.9M rows in 30 seconds via `psql` is far superior to waiting 5–10 minutes for ORM-based inserts. The `seed_generator.py` script provides a path to regenerate the dump when the schema evolves.

---

## Appendix: Decision Summary Matrix

| ADR | Decision | Key Trade-Off | Risk Level |
|-----|----------|---------------|------------|
| 001 | Boilerplate over Live SaaS | One-time revenue vs. recurring; zero ops burden vs. lower revenue ceiling | Medium — revenue depends on sales volume |
| 002 | Modular Monolith over Microservices | Simpler deployment vs. no independent scaling | Low — target deployment fits single node |
| 003 | TimescaleDB over InfluxDB | Full SQL + single DB vs. ~20% memory overhead | Low — well-established extension |
| 004 | ARQ over Celery | Lightweight + async-native vs. smaller community | Low — fits workload profile |
| 005 | JWT Auth over Session-Based | Stateless simplicity vs. harder token revocation | Low — 15-min TTL mitigates |
| 006 | Next.js over Reflex | Maximum market + ecosystem vs. TypeScript learning curve | Medium — two codebases to maintain |
| 007 | Textual TUI over Web-Only | Strong differentiator vs. ~3 weeks additional dev | Medium — Textual is young framework |
| 008 | Continuous Aggregates over App Rollups | Automatic + correct vs. TimescaleDB-specific | Low — documented migration pattern |
| 009 | Docker Compose over Kubernetes | Single-command deploy vs. no HA/auto-scaling | Low — v1 deployment fits |
| 010 | SQL Seed Scripts over Python Fixtures | Fast + deterministic vs. 15MB repo file (Git LFS) | Low — standard pattern for boilerplates |

---

## Appendix: Superseded ADRs

*None yet. This section records ADRs that have been deprecated or superseded by newer decisions.*

---

*Document v1.0 — For questions about these decisions, open a GitHub Issue with the `architecture` label.*
