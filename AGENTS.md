# URJA — Project Context

**Stack:** FastAPI (Python 3.12+) + PostgreSQL 16 / TimescaleDB + Next.js 16 + Tailwind v4 + shadcn/ui + Textual (TUI)

**Status:** Idea phase → Boilerplate validated

---

## Session Log

### [2026-07-22] — URJA Idea Validation & Boilerplate Pivot
- **State:** Complete — idea.md upgraded
- **Validation Method:** Web research (curtailment market, competitive landscape, boilerplate market, carbon MRV tech)
- **Key Findings:**
  - Curtailment is a $34B+ growing problem (€7.2B lost in 2024 across 7 EU countries alone)
  - Zero competitors in the "renewable energy boilerplate" space (Power Factors, Fluence, Wärtsilä are all enterprise SaaS)
  - Generic boilerplates (ShipFast, Supastarter) have zero energy domain logic
  - Carbon DMRV is a hot but fragmented space — perfect for a pre-built pipeline
  - Textual TUI for ops teams is a strong differentiator
- **Pivot Decision:** From Live SaaS ($500-$2,500/MW/month) → Boilerplate ($149-$249 one-time)
- **Tech Stack Finalized:** FastAPI + TimescaleDB + ARQ + Next.js 16 + Tailwind v4 + shadcn/ui + Recharts + Leaflet + Textual TUI + Docker Compose
- **Competitive Adaptations:** Power Factors (KPI cards, SCADA patterns), Fluence (revenue uplift viz), Tesla Autobidder (SOC gauge), Verra+Hedera (DMRV pipeline)
- **Next Turn Directive:** Phase 1 implementation — database schema, API scaffold, Docker setup, seed data

### [2026-07-22] — README.md Created
- **State:** Success
- **MCP Data Used:** websearch (competitive landscape, boilerplate market comparison)
- **Files Created:** README.md, AGENTS.md
- **Key Output:** Professional README with features, tech stack, pricing tiers ($149/$249/$499), competitive comparison table, and quick start guide
- **Next Turn Directive:** Phase 1 implementation — database schema, API scaffold, Docker setup, seed data

---

## Architecture Decisions

1. **Boilerplate over SaaS** — No hosting costs. No support SLA. Cash-flow positive from Day 1. Niche is empty.
2. **TimescaleDB over InfluxDB** — Full SQL + time-series hypertables = one database to learn.
3. **ARQ over Celery** — Runs on Redis (already needed). No RabbitMQ dependency. Lighter on CPU.
4. **Leaflet over Google Maps** — Free, no API keys, works offline.
5. **Textual TUI** — Differentiator. Ops teams love terminals. Runs in terminal AND browser.
6. **Three modules retained** — Yield (dispatch), Carbon (MRV), Health (predictive maintenance) — all as reusable features, not standalone products.
