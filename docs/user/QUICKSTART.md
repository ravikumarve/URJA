# URJA ⚡ — Quick Start Guide

**From zero to live renewable asset dashboard in 5 minutes.**

---

## What You Get

URJA is a complete production-ready boilerplate for grid-scale renewable asset management. You get a full-stack control plane — real-time telemetry ingestion, curtailment-aware dispatch optimization, a carbon credit MRV pipeline, predictive maintenance alerts, and a terminal UI — all self-contained in Docker containers with pre-loaded sample data for a 50MW solar farm.

## Prerequisites

- **Docker** 24.0+ and **Docker Compose** 2.20+

That's it. PostgreSQL, Redis, Python, Node.js — everything else is containerized.

## Quick Start

```bash
git clone https://github.com/ravikumarve/URJA.git
cd URJA
cp .env.example .env
docker compose up -d
docker compose exec api alembic upgrade head
docker compose exec api python scripts/seed.py
```

Open **http://localhost:3000** and log in with:

```
Email:    admin@urja.local
Password: change-me-on-first-login
```

![Screenshot: URJA login page]

## What You'll See

The dashboard opens to six KPI cards across the top showing **live generation (MW)**, **total revenue**, **carbon credits issued**, **active alerts**, **fleet availability %**, and **CO₂ avoided (tonnes)**. Below is an interactive duck curve chart with grid price overlay and a mini Leaflet map of your asset locations.

Navigate using the sidebar:
- **Dashboard** — Live ops at a glance
- **Assets** — Asset table with hierarchy tree and clickable map markers
- **Yield** — Curtailment events with revenue-lost calculator and dispatch rules
- **Carbon** — Credit portfolio table, mint form, and MRV audit trail
- **Health** — Health score grid (0–100%) for each asset, active alerts, maintenance work orders
- **Settings** — Branding editor, API key manager, alert thresholds

![Screenshot: Dashboard with KPI cards, duck curve chart, and asset map]

## 10-Minute Tour

1. **Dashboard** — 6 KPI cards showing live generation, revenue, carbon credits, active alerts, availability %, and CO₂ avoided. Duck curve chart overlays generation vs. grid price over 24 hours. Alert ticker streams latest warnings.

2. **Assets Map** — Leaflet-powered map with color-coded markers for each solar inverter / wind turbine. Click any marker for a detail panel showing generation curve, health gauge, and SOC gauge (battery assets).

3. **Carbon Portfolio** — Every issued credit with methodology version, CO₂ eq, retirement status, and a full MRV audit trail (blockchain-ready for Verra + Hedera Guardian). Export ESG reports in one click.

4. **Health** — Per-asset health score (0–100%) with trend history. ML-based anomaly detection flags power drops, temperature spikes, and vibration outliers. Acknowledge alerts and schedule maintenance work orders from this view.

5. **TUI Dashboard** — Open a terminal and run:
   ```bash
   docker compose exec tui python dashboard-tui/app.py
   ```
   Or access it in your browser at **http://localhost:8080**. Navigate with Tab/Arrow keys across Overview, Curtailment, Carbon, and Health screens — all live-polling the API at 15-second intervals.

![Screenshot: Textual TUI with Overview screen showing live MW generation table]

## Next Steps

- **[TUTORIAL.md](../TUTORIAL.md)** — Full walkthrough: from boilerplate to 50MW solar farm in 10 minutes
- **[API-SPEC.md](../api/API-SPEC.md)** — Complete REST API reference with endpoint examples
- **[DEPLOYMENT.md](../ops/DEPLOYMENT.md)** — Production deployment on a VPS with Caddy TLS
- **[ARCHITECTURE.md](../technical/ARCHITECTURE.md)** — System architecture deep dive with C4 diagrams
- **[SETUP.md](../development/SETUP.md)** — Manual setup guide (native dev without Docker)

---

*URJA — Deploy clean energy intelligence. Own your infrastructure.*
