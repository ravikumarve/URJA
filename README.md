# URJA ⚡ — Renewable Asset Management Boilerplate

**Full-stack renewable energy control plane — 40 API endpoints, 6 background workers, 20 database models — ready to deploy.**

<p align="center">
  <img src="https://img.shields.io/github/stars/ravikumarve/URJA?style=social" />
  <img src="https://img.shields.io/github/license/ravikumarve/URJA" />
  <img src="https://img.shields.io/badge/status-active-brightgreen" />
</p>

[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-16-000?logo=next.js)](https://nextjs.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql)](https://postgresql.org)
[![TimescaleDB](https://img.shields.io/badge/TimescaleDB-2.17-FBB117)](https://timescale.com)
[![Tailwind v4](https://img.shields.io/badge/Tailwind-4-06B6D4?logo=tailwindcss)](https://tailwindcss.com)
[![Textual](https://img.shields.io/badge/Textual-TUI-5C4EE5)](https://textual.textualize.io)
[![License](https://img.shields.io/badge/license-Commercial-green)](LICENSE)

---

**URJA** (meaning "Energy" in Sanskrit/Hindi) is a production-ready boilerplate for building **grid-scale renewable asset management systems**. It gives you a complete operational control plane — from real-time telemetry ingestion to carbon credit issuance — that you can deploy, customize, and resell.

> **Not a SaaS. A boilerplate you own.**

---

## 📦 What You Get

```
urja/
├── backend/                         # FastAPI async API (6,487 LOC)
│   ├── api/                        # 40 RESTful endpoints (7 routers)
│   │   ├── auth.py                 # JWT + API key authentication
│   │   ├── assets.py               # Asset & site CRUD
│   │   ├── telemetry.py            # Time-series ingest & query
│   │   ├── dispatch.py             # Curtailment dispatch rules
│   │   ├── carbon.py               # Carbon credit MRV pipeline
│   │   └── health.py               # Health scores & maintenance
│   ├── models/                     # 20 SQLAlchemy tables (TimescaleDB)
│   ├── schemas/                    # Pydantic v2 request/response models
│   ├── services/                   # Domain logic modules
│   │   ├── auth.py                 # Password hashing, JWT, API keys
│   │   ├── asset.py                # Asset & site management
│   │   ├── yield_optimizer.py      # Curtailment revenue loss, dispatch
│   │   ├── carbon_vault.py         # CO₂ calculation, hash chain, MRV
│   │   └── health_scorer.py        # Anomaly detection, 3-sigma scoring
│   └── tasks/                      # 6 ARQ background workers
│       ├── telemetry_ingest.py     # Ingest validation & enrichment
│       ├── carbon_mint.py          # Credit minting with chain hashes
│       ├── health_scan.py          # 15-min anomaly scan (cron)
│       ├── refresh_weather.py      # 6-hr weather refresh (cron)
│       ├── refresh_pricing.py      # 1-hr grid pricing (cron)
│       └── daily_rollup.py         # Nightly aggregate rollup (cron)
├── docker/                         # Docker Compose (one-command deploy)
├── scripts/                        # Seed data generator (50MW farm)
├── db/                             # Alembic async migrations
└── docs/                           # 20 documents, ~692KB
```

---

## 🎯 Who Is This For?

| Role | How They Use URJA |
|---|---|
| **Clean Energy Consultants** | Deploy for solar/wind farm clients — white-label and customize |
| **System Integrators** | Use as foundation for SCADA + EMS + carbon MRV projects |
| **Developers in Energy** | Learn the full stack of modern renewable asset management |
| **Solar/Wind Farm Operators** | Self-host and own your monitoring infrastructure |

---

## ✨ Features

### 📊 URJA Yield — Curtailment-Aware Dispatch
- **40 REST API endpoints** — Auth, assets, telemetry, dispatch, carbon, health, maintenance
- Real-time generation monitoring per asset (kW, MWh, availability %)
- Curtailment detection with **Revenue Lost** calculator
- Dispatch optimization rules engine (battery storage / compute loads)
- Grid price overlay on generation timeline

### 🌿 URJA Carbon — Verified Credit Pipeline
- Automated kWh → carbon offset calculation (URJA-VCS-1.0 methodology)
- Digital MRV (Measurement, Reporting, Verification) workflow
- **SHA-256 hash chain** — tamper-evident credit audit trail
- Credit portfolio tracking (issued, retired, available)
- Blockchain-ready (Verra + Hedera Guardian compatible)

### 🔧 URJA Health — Predictive Maintenance
- Statistical anomaly detection (3-sigma) for inverters, turbines
- Configurable alert thresholds (temperature, vibration, power drop)
- Asset health score (0–100%) with trend history
- Maintenance scheduler with work order tracking

### 🖥️ TUI Dashboard — Terminal-First Ops
Built with [Textual](https://textual.textualize.io) — runs in your terminal **or** browser:
- Real-time MW generation overview
- Live curtailment alerts
- Carbon credit ledger
- Asset health indicators at a glance
- Keyboard-driven navigation for ops teams

---

## 🏗️ Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | FastAPI (Python 3.12+) • Pydantic v2 • SQLAlchemy 2.0 async |
| **Database** | PostgreSQL 16 + TimescaleDB (hypertables + continuous aggregates) |
| **Background** | ARQ (Redis-based task queue) • 6 workers • cron scheduling |
| **Auth** | JWT (access + refresh tokens) • API key authentication • bcrypt |
| **Frontend** | Next.js 16 • Tailwind v4 • shadcn/ui • Recharts |
| **Maps** | Leaflet (free, no API key, works offline) |
| **TUI** | Textual (runs in terminal AND browser) |
| **Testing** | pytest 8.x (backend, 90%+ coverage) • Playwright (E2E) |
| **Deploy** | Docker Compose (dev + prod) • GitHub Actions CI/CD |
| **Schema** | Alembic async migrations • Seed data (50MW farm) |

---

## 🚀 Quick Start

### 🐳 Docker (Production-Ready)

```bash
# Clone the repo
git clone https://github.com/your-org/urja-boilerplate.git
cd urja-boilerplate

# One-command setup
./scripts/setup.sh

# Or manually:
docker compose -f docker/docker-compose.yml up -d
docker compose exec api alembic upgrade head
docker compose exec api python scripts/seed.py

# Open the dashboard
open http://localhost:3000
```

### 💻 Local Dev (No Docker)

```bash
# Backend
source backend/.venv/bin/activate   # Python venv (deps pre-installed)
uvicorn app.main:app --reload        # → http://localhost:8000/docs

# Frontend (in another terminal)
cd frontend && npm run dev           # → http://localhost:3000

# TUI Dashboard (in another terminal)
source backend/.venv/bin/activate
python dashboard-tui/app.py

# Tests
pytest -v                            # 124 tests across 7 modules
pytest --cov=app --cov-report=term-missing   # With coverage

# Migrations (requires DB running)
alembic upgrade head
alembic current
```

### 🎮 TUI Keybindings

| Key | Screen | Description |
|-----|--------|-------------|
| `1` | Overview | KPI cards, generation, alerts |
| `2` | Curtailment | Events, dispatch log |
| `3` | Carbon | Credit ledger, batches |
| `4` | Health | Asset scores, active alerts |
| `r` | — | Refresh data |
| `q` | — | Quit |

---

## 📋 Prerequisites

### Docker Path
- Docker & Docker Compose v2
- 4 GB RAM minimum

### Local Dev Path
- Python 3.12+
- Node.js 20+
- PostgreSQL 16 + TimescaleDB
- Redis 7

---

## 📁 Demo Data

URJA ships with **sample data for a 50MW solar farm** including:

- **432,000 telemetry data points** — 12 months of 15-minute interval generation
- **20 assets** — Inverters, transformers, batteries, meters, weather stations
- **3 sites** — Solar farm, wind farm, hybrid park
- Realistic curtailment events with revenue impact calculation
- Historical maintenance logs with anomaly events
- Carbon credit chain with audit trail

This means you see a **fully populated dashboard** from the moment you run `docker compose up`.

---

## 📖 Documentation

| Category | Documents |
|---|---|
| **Product** | [PRD](docs/product/PRD.md) • [Roadmap](docs/product/ROADMAP.md) • [Pricing](docs/product/PRICING.md) • [Competitive Analysis](docs/product/COMPETITIVE.md) |
| **Technical** | [Architecture](docs/technical/ARCHITECTURE.md) • [API Spec](docs/technical/API-SPEC.md) • [Database Schema](docs/technical/DATABASE.md) • [ADRs](docs/technical/ADRS.md) |
| **Dev UX** | [Setup Guide](docs/development/SETUP.md) • [Guidelines](docs/development/GUIDELINES.md) • [Testing](docs/development/TESTING.md) • [CI/CD](docs/development/CI-CD.md) |
| **User** | [Quickstart](docs/user/QUICKSTART.md) • [Tutorial](docs/user/TUTORIAL.md) • [Configuration](docs/user/CONFIGURATION.md) • [TUI Guide](docs/user/TUI-GUIDE.md) |
| **Deploy** | [Deployment](docs/technical/DEPLOYMENT.md) • [Security](docs/technical/SECURITY.md) |

---

## 💰 Pricing

| Tier | Price | What's Included |
|---|---|---|
| **Basic** | **$149** | Full backend + frontend + DB schema + Docker setup + docs |
| **Pro** | **$249** | Everything + TUI dashboard + ML health models + priority support |
| **Enterprise** | **$499** | White-label license + private repo + 1-hour consulting call |

[Buy on Gumroad →](https://ravikumarve.gumroad.com)

---

## 🏆 Why URJA Over...

| | Power Factors | ShipFast | **URJA** |
|---|---|---|---|
| **Price** | $50K+/year | $129–$199 | **$149–$249 one-time** |
| **Energy domain models** | ✅ | ❌ | ✅ 20 tables, TimescaleDB |
| **Carbon MRV pipeline** | ❌ | ❌ | ✅ SHA-256 hash chain |
| **TUI Dashboard** | ❌ | ❌ | ✅ Textual terminal UI |
| **API endpoints** | 200+ (bloated) | ~10 (generic) | **40 (focused)** |
| **Background workers** | ❌ | ❌ | ✅ 6 ARQ workers, 4 cron |
| **You own the code** | ❌ | ✅ Partial | ✅ Full commercial license |
| **Offline deploy** | ❌ Cloud-only | ✅ | ✅ Docker Compose |

---

## 🎮 CLI Command Reference

```bash
# ─── Backend ─────────────────────────────────────────────
uvicorn app.main:app --reload                    # Dev server (port 8000)
uvicorn app.main:app --host 0.0.0.0 --port 8000   # Production

# ─── Database ────────────────────────────────────────────
alembic upgrade head                              # Apply migrations
alembic downgrade -1                              # Rollback one step
alembic current                                   # Show current version
alembic history                                   # List all migrations
python scripts/seed.py                            # Load 432K demo rows

# ─── Tests ───────────────────────────────────────────────
pytest -v                                         # 124 tests, 7 modules
pytest -v -x                                      # Stop on first failure
pytest --cov=app --cov-report=term-missing        # Coverage report
pytest tests/test_api/test_auth.py -v             # Single test file

# ─── Workers ─────────────────────────────────────────────
python -m app.tasks.worker                        # Start ARQ worker
# Cron schedule: health=15min, weather=6h, pricing=1h, rollup=midnight

# ─── Frontend ────────────────────────────────────────────
cd frontend && npm run dev                        # Dev server (port 3000)
cd frontend && npm run build                      # Production build
cd frontend && npx tsc --noEmit                   # Type check

# ─── TUI Dashboard ───────────────────────────────────────
python dashboard-tui/app.py                       # Launch terminal UI
```

---

## 🗺️ Roadmap

- [x] Idea validated & market research complete
- [x] **Phase 1: Database schema + API scaffold + Docker setup — DONE**
- [x] **Phase 2: Dashboard frontend — DONE** (7 pages, Recharts, Leaflet map, RadarCanvas)
- [x] **Phase 3: TUI screens + test suite — DONE** (124 tests, 90%+ coverage, 4 TUI screens)
- [ ] Phase 4: Gumroad launch + documentation + marketing

**Shipped:** 40 API endpoints · 20 SQLAlchemy models · 6 ARQ workers · 124 pytest tests · 7 dashboard pages · Leaflet asset map · Radar canvas · 4-screen TUI · Alembic migrations · Seed data (432K rows) · Docker Compose · 20 docs.

---

## 🤝 Contributing

This boilerplate is a commercial product. Bug reports and feature requests are welcome via GitHub Issues.

---

## 📄 License

URJA is sold under a **Commercial License** — not open source.

- **Basic & Pro tiers:** Use, modify, and deploy for your own products. No redistribution or resale of the source.
- **Enterprise tier:** Full white-label rights — rebrand and deliver to your clients.

See [LICENSE](LICENSE) for full terms.

## 🛒 Support the Project

Star the repo, share it, or grab the Pro tier: [Buy on Gumroad](https://ravikumarve.gumroad.com)

---

<p align="center">
  Built with ❤️ for the renewable energy transition.<br>
  <sub>URJA — Deploy clean energy intelligence. Own your infrastructure.</sub>
</p>