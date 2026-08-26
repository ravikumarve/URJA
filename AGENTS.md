# URJA — Project Context

**Stack:** FastAPI (Python 3.12+) + PostgreSQL 16 / TimescaleDB + Next.js 16 + Tailwind v4 + shadcn/ui + Textual (TUI)

**Status:** Phase 1 backend done. Design language defined. Landing page prototyped. TUI dashboard built.

---

## Session Log

### [2026-08-26] — Frontend Pass Audit: Build ✅ / Integration ❌
- **State:** Audit complete — build passes, ZERO backend integration found
- **Build Status:** `npm run build` PASS (Next.js 16.2.11 Turbopack, 9 routes static), `tsc --noEmit` clean. Removed stray empty dirs (app/dashboard/, components/maps/ — untracked by git anyway).
- **Critical Finding:** Entire frontend is a static mockup. No API client (lib/=utils.ts only), no fetch calls anywhere, all pages hardcoded arrays. Login button = console.log stub. No middleware/auth guard, no token storage, no logout. Backend's 40 endpoints consumed: 0.
- **Missing for sellable dashboard flow:** (1) lib/api.ts client + NEXT_PUBLIC_API_URL, (2) real auth flow (login→JWT→guard→logout), (3) wire Overview to /telemetry/latest + /health/alerts + /carbon/portfolio, (4) wire yield/carbon/health/assets/settings pages, (5) loading/error/empty states, (6) ESLint setup.
- **Next Turn Directive:** Sprint — build api client + auth flow first (blocks everything else), then wire Overview page as the reference pattern for remaining 5 pages.

### [2026-08-26] — Pre-Sale Audit + MIT → Commercial License Conversion
- **State:** Success — commit 50d1413, working tree clean
- **Pre-Sale Status:** Backend (40 endpoints, 124 tests), Frontend (7 pages), TUI, Docker, seed data, 20 docs — all complete & pushed. Blockers identified: MIT license (FIXED), no Gumroad assets, no v1.0.0 tag, fresh-install flow unverified.
- **Architectural Decision:** Pure Commercial License (AETHER precedent — direct-sell only). Tiered grants: Basic/Pro = own-product use, no redistribution; Enterprise ($499) = white-label. Updates via Gumroad re-download only. Zero MIT grant anywhere; sole remaining "MIT" is InfluxDB's license in ADRS comparison table (correct).
- **Files Changed:** LICENSE (full rewrite), README.md, PRICING.md, PRD.md, CI-CD.md (badge → Commercial)
- **Next Turn Directive:** Gumroad prep — verify fresh-clone install flow end-to-end, `npm run build` frontend pass, tag v1.0.0, then listing copy.

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

### [2026-07-22] — Full Documentation Suite Completed (20 docs)
- **State:** Success — 24 files, ~692KB total documentation
- **MCP Data Used:** websearch (competitor research, boilerplate market), agency-agents (9 agent types deployed)
- **Agents Deployed:** @product-manager, @software-architect, @database-optimizer, @api-platform-engineer, @security-architect, @backend-architect + @frontend-developer, @devops-automator, @test-automation-engineer, @technical-writer
- **Documents Created:**
  - Phase 1 (Foundation): PRD.md, ARCHITECTURE.md, DATABASE.md, ADRS.md
  - Phase 2 (Specification): API-SPEC.md, SECURITY.md, GUIDELINES.md
  - Phase 3 (Operations): DEPLOYMENT.md, CI-CD.md, TESTING.md (E2E pipeline)
  - Phase 4 (Developer Experience): SETUP.md, QUICKSTART.md, TUTORIAL.md, TUI-GUIDE.md, CONFIGURATION.md
  - Phase 5 (Business): ROADMAP.md, PRICING.md, COMPETITIVE.md, LICENSE, CONTRIBUTING.md, CHANGELOG.md
- **Key Output:** Complete documentation architecture covering product, technical, development, user, and business domains
- **Next Turn Directive:** Phase 1 implementation — database schema SQL + FastAPI scaffold + Docker Compose + seed data

### [2026-07-22 19:30] — Design Language Analyzed & Landing Page Fixed
- **State:** Success — 3 HTML prototypes analyzed, design system documented
- **MCP Data Used:** direct file reads (all 3 HTML files)
- **Files Created:** `docs/product/design-language.md` — full design spec (palette, typography, layout, components, effects, Tailwind config)
- **Landing Page Fixes:**
  - Added meta tags: description, keywords, OG/Twitter cards, favicon (inline SVG)
  - Fixed broken links: `urja-tui-tactical.html` → `urja_tui_simulator_amber.html`
  - Fixed broken links: `urja-dashboard-tactical.html` → `urja_tactical_dashboard.html`
  - Added missing `#pricing` section (3-tier bento card grid with feature lists + buy buttons)
- **Next Turn Directive:** Phase 2 — Frontend scaffold (Next.js 16 + shadcn/ui + Recharts + Leaflet) or TUI Textual dashboard or Git push

### [2026-07-22 18:30] — URJA Phase 1 Backend Implementation Complete
- **State:** Success — 40 API endpoints, 6 ARQ task workers, full FastAPI backend
- **MCP Data Used:** code_tree (project structure verification), webresearch (competitor docs), grep_app (ARQ patterns)
- **Agency Agents Deployed:** @backend-architect (delegated via general agents for implementation)
- **Files Created/Modified:**
  - 6 routers (auth, assets, telemetry, dispatch, carbon, health) — 40 total routes
  - 6 schema modules (auth, asset, telemetry, dispatch, carbon, health)
  - 5 service modules (auth, asset, yield_optimizer, carbon_vault, health_scorer)
  - 9 task modules (worker, scheduler, telemetry_ingest, carbon_mint, health_scan, refresh_weather, refresh_pricing, daily_rollup)
  - 48 Python files total, 6,487 lines of code
  - 20 SQLAlchemy models (10 model files)
  - Full Docker Compose setup (dev + prod, init-db, setup script)
  - 1,134-line seed data script (432K telemetry rows for 50MW solar farm)
- **Import Status:** All 40 routes, all services, all tasks — 100% clean imports
- **Next Turn Directive:** Phase 2 — Frontend scaffold (Next.js 16 + shadcn/ui + Recharts + Leaflet) or TUI Textual dashboard or Git push

### [2026-07-22 20:30] — TUI Dashboard Built (Amber CRT Terminal)
- **State:** Success — 12 files, 738 lines
- **MCP Data Used:** file reads (TUI-GUIDE.md spec, urja_tui_simulator_amber.html prototype)
- **Files Created:**
  - `dashboard-tui/app.py` — Main app (6 key bindings, 4 screens)
  - `dashboard-tui/api.py` — Async httpx client with mock data fallback
  - `dashboard-tui/config.py` — Env-based settings (API URL, poll interval)
  - `dashboard-tui/theme.tcss` — Full amber CRT theme (188 lines)
  - `dashboard-tui/screens/overview.py` — KPIs + asset table + worker log
  - `dashboard-tui/screens/curtailment.py` — Events table + dispatch log
  - `dashboard-tui/screens/carbon.py` — Credit ledger with batch table
  - `dashboard-tui/screens/health.py` — Health scores + active alerts
  - `dashboard-tui/widgets/kpi_card.py` — Reactive KPI card widget
  - `dashboard-tui/requirements.txt` — textual, rich, httpx
- **Design:** Amber monochrome CRT aesthetic (#0a0500 bg, #ffb703 primary, #8a6300 dim, #ff5e00 alert). All screens auto-refresh every 5s. Graceful mock data fallback when API unreachable.
- **Next Turn Directive:** Frontend scaffold (Next.js 16 + shadcn/ui + Recharts + Leaflet) or Docker Compose tui service

## Architecture Decisions

1. **Boilerplate over SaaS** — No hosting costs. No support SLA. Cash-flow positive from Day 1. Niche is empty.
2. **TimescaleDB over InfluxDB** — Full SQL + time-series hypertables = one database to learn.
3. **ARQ over Celery** — Runs on Redis (already needed). No RabbitMQ dependency. Lighter on CPU.
4. **Leaflet over Google Maps** — Free, no API keys, works offline.
5. **Textual TUI** — Differentiator. Ops teams love terminals. Runs in terminal AND browser.
6. **Three modules retained** — Yield (dispatch), Carbon (MRV), Health (predictive maintenance) — all as reusable features, not standalone products.
