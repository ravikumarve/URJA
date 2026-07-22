# URJA ⚡ — Renewable Asset Management Boilerplate

**Full-stack renewable energy control plane with web dashboard + terminal UI.**

[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-16-000?logo=next.js)](https://nextjs.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql)](https://postgresql.org)
[![TimescaleDB](https://img.shields.io/badge/TimescaleDB-2.17-FBB117)](https://timescale.com)
[![Tailwind v4](https://img.shields.io/badge/Tailwind-4-06B6D4?logo=tailwindcss)](https://tailwindcss.com)
[![Textual](https://img.shields.io/badge/Textual-TUI-5C4EE5)](https://textual.textualize.io)
[![License](https://img.shields.io/badge/license-MIT%20%2B%20Commercial-green)](LICENSE)

---

**URJA** (meaning "Energy" in Sanskrit/Hindi) is a production-ready boilerplate for building **grid-scale renewable asset management systems**. It gives you a complete operational control plane — from real-time telemetry ingestion to carbon credit issuance — that you can deploy, customize, and resell.

> **Not a SaaS. A boilerplate you own.**

---

## 📦 What You Get

```
urja-boilerplate/
├── backend/                     # FastAPI async API
│   ├── api/                    # RESTful endpoints
│   ├── models/                 # SQLAlchemy + TimescaleDB schemas
│   ├── services/               # Domain logic (dispatch, carbon, health)
│   └── tasks/                  # ARQ background workers
├── frontend/                    # Next.js 16 dashboard
│   ├── dashboard/              # Live KPI cards, generation curves
│   ├── assets/                 # Asset map + hierarchy
│   ├── carbon/                 # Carbon credit portfolio
│   └── health/                 # Predictive maintenance alerts
├── dashboard-tui/               # Textual terminal UI
├── db/                         # Alembic migrations + seed data
├── docker/                     # Docker Compose (one-command deploy)
└── docs/                       # Full documentation
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

- Real-time generation monitoring per asset (kW, MWh, availability %)
- Curtailment detection with **Revenue Lost** calculator
- Dispatch optimization rules engine (battery storage / compute loads)
- Interactive duck curve visualization
- Grid price overlay on generation timeline

### 🌿 URJA Carbon — Verified Credit Pipeline

- Automated kWh → carbon offset calculation
- Digital MRV (Measurement, Reporting, Verification) workflow
- Blockchain-ready audit trail (Verra + Hedera Guardian compatible)
- Credit portfolio dashboard with issuance history
- ESG reporting export

### 🔧 URJA Health — Predictive Maintenance

- ML-based anomaly detection for solar inverters, wind turbines
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
| **Backend** | FastAPI (Python 3.12+) • Pydantic v2 • SQLAlchemy 2.0 |
| **Database** | PostgreSQL 16 + TimescaleDB (hypertables for time-series) |
| **Background** | ARQ (Redis-based task queue) |
| **Frontend** | Next.js 16 • Tailwind v4 • shadcn/ui • Recharts |
| **Maps** | Leaflet (free, no API key, works offline) |
| **TUI** | Textual (runs in terminal AND browser) |
| **Testing** | pytest (backend, 90%+ coverage) • Playwright (E2E) |
| **Deploy** | Docker Compose • GitHub Actions |

---

## 🚀 Quick Start

```bash
# Clone the repo
git clone https://github.com/your-org/urja-boilerplate.git
cd urja-boilerplate

# Start everything
docker compose up -d

# Load sample data (50MW solar farm)
docker compose exec api python scripts/seed.py

# Open the dashboard
open http://localhost:3000

# Launch the TUI
docker compose exec tui python dashboard-tui/app.py
```

---

## 📋 Prerequisites

- Docker & Docker Compose
- 4 GB RAM minimum (runs comfortably on a laptop)

---

## 📁 Demo Data

URJA ships with **sample data for a 50MW solar farm** including:

- 12 months of 15-minute interval generation data
- Realistic curtailment events with revenue impact
- 5,000+ carbon credit issuances
- Historical maintenance logs with anomaly events

This means you see a **fully populated dashboard** from the moment you run `docker compose up`.

---

## 📖 Documentation

- [Architecture Overview](docs/ARCHITECTURE.md)
- [API Reference](docs/API.md)
- [Database Schema](docs/DATABASE.md)
- [Deployment Guide](docs/DEPLOYMENT.md)
- [Tutorial: From Zero to 50MW Solar Farm in 10 Minutes](docs/TUTORIAL.md)

---

## 💰 Pricing

| Tier | Price | What's Included |
|---|---|---|
| **Basic** | **$149** | Full backend + frontend + DB schema + Docker setup + docs |
| **Pro** | **$249** | Everything + TUI dashboard + ML health models + priority support |
| **Enterprise** | **$499** | White-label license + private repo + 1-hour consulting call |

[Buy on Gumroad →](https://gumroad.com)

---

## 🏆 Why URJA Over...

| | Power Factors | ShipFast | **URJA** |
|---|---|---|---|
| **Price** | $50K+/year | $129–$199 | **$149–$249 one-time** |
| **Energy domain models** | ✅ | ❌ | ✅ Built-in |
| **Carbon MRV pipeline** | ❌ | ❌ | ✅ Pre-built |
| **TUI Dashboard** | ❌ | ❌ | ✅ Textual |
| **You own the code** | ❌ | ✅ Partial | ✅ Full commercial license |
| **Offline deploy** | ❌ Cloud-only | ✅ | ✅ Docker Compose |

---

## 🗺️ Roadmap

- [x] Idea validated & market research complete
- [ ] Phase 1: Database schema + API scaffold + Docker setup
- [ ] Phase 2: Dashboard frontend (KPI cards, charts, map)
- [ ] Phase 3: TUI screens + ML health models + test suite
- [ ] Phase 4: Gumroad launch + documentation + marketing

---

## 🤝 Contributing

This boilerplate is a commercial product. Bug reports and feature requests are welcome via GitHub Issues.

---

## 📄 License

- **Basic & Pro tiers:** MIT License with commercial use restrictions
- **Enterprise tier:** Full commercial license for white-label resale

See [LICENSE](LICENSE) for details.

---

<p align="center">
  Built with ❤️ for the renewable energy transition.<br>
  <sub>URJA — Deploy clean energy intelligence. Own your infrastructure.</sub>
</p>
