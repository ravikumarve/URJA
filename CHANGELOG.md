# Changelog

All notable changes to URJA will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] — 2026-08-28

### Added
- **40 API endpoints** (7 routers: auth, assets, telemetry, dispatch, carbon, health) + 20 SQLAlchemy models + 6 ARQ workers (health_scan 15m, weather 6h, pricing 1h, daily_rollup)
- **Frontend** 7 pages (Overview, Assets, Yield, Carbon, Health, Settings, Login) — Next.js 16, Tailwind v4, shadcn/ui, Recharts 2.15 (ComposedChart price overlay), Leaflet OSM (no watermark)
- **TUI** 4 screens (Overview, Curtailment, Carbon, Health) @145×36 amber CRT — Textual 8.2 + fallback mock data
- **Pricing** `GET /v1/pricing` (raw/hourly/daily time_bucket) + `GET /v1/pricing/latest` (INR/kWh), `refresh_pricing` LSTM wiring (Colab burst)
- **Health** IsolationForest 200 trees (432K synthetic, 5D) — Colab T4 burst, Latitude inference-only with 3-sigma fallback
- **Demo** `docs/images/urja-tui-demo.gif` (148K) + `urja-web-demo.gif` (201K) + gallery PNGs
- **Colab** 6 notebooks (health_train, yield_forecast, carbon_mrv, telemetry_synth, frontend_build, load_test)
- **Docs** 20 documents, ~692KB — PRD, ARCHITECTURE, DATABASE, API-SPEC, SECURITY, ADRS, etc.
- **Project documentation suite** (initial scaffold)
- README with features, tech stack, pricing, competitive comparison
- AGENTS.md for AI-assisted development memory
