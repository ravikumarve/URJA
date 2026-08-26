# PRD: URJA — Renewable Asset Management & Carbon Arbitrage Control Plane
**Status**: Draft
**Author**: Alex (Product Manager)  **Last Updated**: 2026-07-22  **Version**: 1.0
**Stakeholders**: Engineering Lead, Design Lead, Marketing Lead

---

## 1. Problem Statement

### The Curtailment Crisis

Renewable energy producers are leaving billions of dollars on the table. When the grid cannot absorb generated electricity — due to oversupply, transmission bottlenecks, or low demand — operators are forced to curtail (shut down) their solar arrays and wind turbines. This is not a rare edge case; it is a structural, growing problem:

- **€7.2 billion** in lost revenue across just 7 European countries in 2024 (Aurora Energy Research)
- **1,700+ GW** of clean energy projects stranded in interconnection queues worldwide (Lawrence Berkeley National Lab, 2024)
- **$34B+** total addressable curtailment problem across global markets (IEA estimates)
- In California ISO, curtailment grew **400%** between 2019 and 2024, reaching 2.5+ TWh annually

The operators most affected are small-to-mid-sized solar and wind farm owners (10MW–200MW). They cannot afford the enterprise solutions used by large utilities:

| Dimension | Enterprise Solution (Power Factors, Fluence) | What Small Operators Have Today |
|-----------|---------------------------------------------|--------------------------------|
| Annual cost | $50K–$500K+ | Excel spreadsheets or nothing |
| Deployment | 6–12 month consultancy | DIY or abandoned projects |
| Customization | Proprietary — vendor-locked | Should be fully owned |
| Carbon MRV | Separate product, extra cost | Manual, error-prone, unauditable |
| Predictive health | Add-on module at 6-figure premium | Reactive maintenance only |

### Who Feels This Pain, How Often, and at What Cost

**Clean Energy Consultants** lose bidding wars because they lack a ready-made monitoring platform. Every new client engagement starts from scratch — building dashboards, setting up databases, wiring SCADA integrations. A single consultant spends 3–6 months per deployment re-solving the same problems. At $200/hr billable, that's $48K–$96K in opportunity cost per project.

**System Integrators** take on SCADA + EMS + carbon MRV projects that require 4+ engineers for 6+ months. Without a reusable foundation, each project is a bespoke build — no leverage, thin margins, high risk.

**Solar/Wind Farm Operators** with 10–200MW fleets face a stark choice: pay $50K+/year for enterprise software they can't customize, or build in-house with a team they don't have. Most choose nothing, flying blind on curtailment losses, carbon revenue, and equipment health.

**Developers entering the energy space** face a brutal learning curve. The domain knowledge spans power systems, time-series databases, carbon methodology, and ML — all before writing a single line of production code. There is no "learn by building" resource that ships a complete, modern, deployable system.

### Cost of Not Solving This

- **For the market**: Curtailment losses grow year-over-year as renewable penetration increases. Every percentage point of curtailment avoided represents millions in recovered generation value and accelerated decarbonization.
- **For us as a business**: Zero revenue from a validated, zero-competition market niche. Generic boilerplates (ShipFast, Supastarter) collectively serve 7,000+ customers at $129–$399 with zero domain logic. The renewable energy equivalent is empty, despite a market that is orders of magnitude more valuable.

---

## 2. Goals & Success Metrics

| Goal | Metric | Current Baseline | Target | Measurement Window |
|------|--------|-----------------|--------|--------------------|
| First sale | Total paid purchases | $0 | 1 sale within 30 days of GA | 30 days post-launch |
| Revenue run rate | Monthly sales × ASP | $0 | $9,950/month (50 sales × avg $199) | 6 months post-launch |
| Buyer activation | % of buyers who deploy `docker compose up` successfully | N/A | >80% (tracked via GitHub issues / support) | 30 days post-purchase |
| Buyer satisfaction | Support tickets per 100 purchases | N/A | <10 tickets/100 purchases | 90 days post-launch |
| Community growth | GitHub stars (public repo) | 0 | 500 stars | 90 days post-launch |
| Content reach | Dev.to tutorial series views | 0 | 50,000 cumulative views across 4-part series | 120 days post-launch |
| Competitive moat | Developer forks / clones from demo repo | 0 | 200+ clones | 120 days post-launch |
| Gumroad conversion | Free tier → paid conversion | N/A | >5% conversion rate | 180 days post-launch |

### North Star Metric

**Monthly recurring revenue equivalent (MRR equiv.)**: Monthly sales volume × average selling price. At 50 sales/month × $199 avg = $9,950/month. This is the single number that tells us whether URJA is a viable product or a hobby project.

---

## 3. Non-Goals

The following are explicitly out of scope for v1:

- **Real SCADA hardware integration**: v1 ships with sample telemetry data and an API for ingestion. Physical IEC 61850, Modbus, or OPC-UA gateway integration will be documented in tutorials but not shipped as code. Integration code for specific hardware (SMA inverters, Siemens PLCs) is a v2 feature if customer demand warrants it.
- **Mobile app**: The web dashboard is responsive but not mobile-native. Analytics from our target personas show <5% usage in mobile browsers for operational dashboards. A React Native or Flutter app is deferred indefinitely unless buyer feedback says otherwise.
- **Multi-tenancy / SaaS hosting**: URJA is a self-hosted boilerplate. There is no auth system, no organization management, no billing integration. Each buyer deploys their own instance. Multi-tenant support would contradict the core value proposition (you own and control your infrastructure).
- **Real-time push notifications**: v1 uses polling for TUI and web dashboard updates. WebSockets or Server-Sent Events are deferred to v2. The polling interval (configurable, default 15s) is acceptable for the monitoring use case.
- **AI/ML forecasting models**: v1 Health module uses statistical anomaly detection (z-score, moving average deviation). Full ML models (LSTM, XGBoost) are a Pro tier differentiator and will be validated against the sample dataset before being shipped.
- **Data export to specific accounting systems**: No native integration with NetSuite, SAP, or other ERP. v1 exports CSV and JSON. API-based integrations are buyer-responsible.
- **Localization / i18n**: English only. The target buyers (developers, integrators, consultants) are English-literate. Localization is a v2 value-add for Enterprise tier.
- **Regulatory compliance certifications**: No SOC 2, ISO 27001, or similar certifications are pursued. The boilerplate includes security best practices (env-based secrets, HTTPS-ready, parameterized queries) but buyers are responsible for their own compliance.

---

## 4. User Personas & Stories

### Persona 1: Priya — Clean Energy Consultant

**Context**: Priya runs a 5-person consulting firm in India that helps solar farm operators optimize their plants. She has 8 clients with fleets ranging from 5MW to 50MW. She bills $150/hr and spends 4–6 months per client building a monitoring and reporting system from scratch.

**Tech profile**: Python-literate, comfortable with Docker, uses React for internal tools. Not a full-time developer — her value is domain expertise.

**Buying motivation**: Stop rebuilding the same dashboard for every client. Deploy URJA, customize the logo and colors, and deliver a professional platform in 2 weeks instead of 6 months.

**Story 1**: As Priya, I want to deploy URJA for a new 20MW solar farm client in under 2 hours so that I can show them a live dashboard on day 1 of engagement instead of month 3.

**Acceptance Criteria**:
- [ ] Running `docker compose up -d` starts all services (API, DB, Redis, frontend) and completes within 5 minutes on a standard cloud VM
- [ ] Seed data for a 20MW solar farm populates the dashboard with realistic KPIs, generation curves, and curtailment events
- [ ] I can change the site name and logo by editing two environment variables and restarting the frontend
- [ ] Performance: Dashboard loads in under 2 seconds on first paint with seeded 12-month data

**Story 2**: As Priya, I want to configure a custom curtailment revenue threshold so that each client sees their specific tariff rate reflected in the Revenue Lost widget, not a default placeholder.

**Acceptance Criteria**:
- [ ] An admin settings page lets me set price per kWh (configurable per asset)
- [ ] The Revenue Lost widget recalculates historical and real-time losses based on this config
- [ ] The config persists across container restarts (stored in DB, not env)
- [ ] A reset-to-default option exists

**Story 3**: As Priya, I want to export a monthly ESG report for my client in PDF format so that I can satisfy their investor reporting requirements without manual work.

**Acceptance Criteria**:
- [ ] Carbon module has an "Export Report" button
- [ ] Generated PDF includes: total generation (MWh), avoided CO2 (tons), credits issued, revenue from carbon sales
- [ ] Report covers a user-specified date range
- [ ] Generated in under 10 seconds for 12 months of data

---

### Persona 2: Dmitri — System Integrator

**Context**: Dmitri works at a 50-person systems integration firm based in Germany. His team builds SCADA + EMS solutions for wind farm operators across Europe. They typically use 4–6 engineers on a 9-month project and deliver custom solutions that are hard to maintain.

**Tech profile**: Senior software architect. Deep experience with Python, TimescaleDB, and React. Operates at the systems level — cares about architecture, testability, modularity.

**Buying motivation**: Cut project delivery time by 60% by starting from a production-ready foundation. Modify and extend specific modules (e.g., replace the dispatch engine with their proprietary algorithm) without rebuilding the entire stack.

**Story 1**: As Dmitri, I want to replace the default dispatch optimization engine with my own algorithm so that I can deliver a custom solution to a client without forking the entire codebase.

**Acceptance Criteria**:
- [ ] The dispatch service is a pluggable module with a documented interface (`BaseDispatchStrategy` class)
- [ ] Registering a custom strategy requires implementing 2 methods (`optimize()` and `validate()`) and registering via a single-line config
- [ ] The existing default strategy (price-optimized battery dispatch) remains functional as a reference
- [ ] Unit tests for the strategy interface exist and pass with the custom strategy

**Story 2**: As Dmitri, I want to integrate a live SCADA feed from a Siemens S7-1500 PLC so that my client's real-time telemetry populates the URJA dashboard without custom middleware.

**Acceptance Criteria**:
- [ ] The telemetry ingestion endpoint accepts data in a documented JSON schema
- [ ] A sample integration script for Siemens S7 (using python-snap7) is provided in `/examples/scada-integrations/`
- [ ] The ingestion endpoint handles batch inserts (up to 1000 records) in under 500ms
- [ ] Validation: malformed payloads return 422 with field-level error messages

**Story 3**: As Dmitri, I want the backend API to return consistent, documented error responses so that the frontend team can build robust error handling without reverse-engineering the API.

**Acceptance Criteria**:
- [ ] All API errors follow RFC 7807 (Problem Details for HTTP APIs)
- [ ] Each endpoint has an OpenAPI schema covering all error responses
- [ ] Backend tests cover at least 90% of error paths
- [ ] Frontend shows user-friendly error messages for the 5 most common failure scenarios

---

### Persona 3: Elena — Solar Farm Operator

**Context**: Elena manages a 45MW solar farm in Andalusia, Spain. She has a small technical team (2 people) who handle day-to-day operations. They use a mix of spreadsheets and the inverter manufacturer's web portal. She knows she's losing money to curtailment but doesn't know how much.

**Tech profile**: Not a developer. Comfortable with web apps, needs simple UI. Her team member Carlos handles basic IT.

**Buying motivation**: See exactly how much revenue curtailment is costing, so she can justify investing in a battery system or compute load arbitrage. Understand which panels are underperforming before they fail.

**Story 1**: As Elena, I want to open a dashboard and see today's generation, curtailment, and revenue lost in large numbers at the top so that I instantly know if today is a good day or a bad day.

**Acceptance Criteria**:
- [ ] Dashboard loads with 3 prominent KPI cards: "Today's Generation (MWh)", "Curtailment (MWh)", "Revenue Lost (€)"
- [ ] KPI cards update within 15 seconds of new telemetry data arriving
- [ ] Color coding: green (normal), yellow (moderate curtailment), red (high curtailment >20%)
- [ ] KPI cards are visible above the fold at 1366×768 resolution

**Story 2**: As Elena, I want to see a map of my solar farm with each inverter's health status so that I can visually identify problem areas without reading through tables.

**Acceptance Criteria**:
- [ ] Leaflet map shows all 15+ inverter locations on the 45MW farm
- [ ] Each marker is color-coded: green (healthy), yellow (warning), red (critical)
- [ ] Clicking a marker shows a tooltip with: inverter ID, current power (kW), health score, last maintenance date
- [ ] Map renders in under 3 seconds on a mid-range laptop

**Story 3**: As Elena, I want to receive an alert when an inverter's output drops below 80% of expected for 15+ consecutive minutes so that I can dispatch Carlos to inspect it before it fails completely.

**Acceptance Criteria**:
- [ ] Health module detects anomalies using z-score deviation on 15-minute telemetry windows
- [ ] Alert appears in the dashboard (notification bell + alert list) within 1 minute of detection
- [ ] Alert includes: asset name, metric (kW), observed value, expected value, deviation %, timestamp
- [ ] Alerts are configurable: threshold (%) and duration (minutes) can be adjusted per asset group
- [ ] I can dismiss or acknowledge an alert, and acknowledged alerts are visually distinct

---

### Persona 4: Marcus — Developer in Energy

**Context**: Marcus is a full-stack developer who wants to break into the clean energy sector. He has 5 years of experience with React and Python but zero domain knowledge in renewables. He wants to learn by building real projects.

**Tech profile**: Strong full-stack developer. Uses Next.js, FastAPI, Docker daily. Reads Hacker News and Dev.to. Contributes to open source.

**Buying motivation**: Get a complete, modern, well-architected renewable energy system to study, modify, and showcase in his portfolio. The domain value + technical quality justifies the $149 price.

**Story 1**: As Marcus, I want to run URJA with a single command and have a fully populated dashboard within 5 minutes so that I can evaluate whether the codebase quality and docs meet my standards before purchasing.

**Acceptance Criteria**:
- [ ] Public GitHub repo exists with a free tier (limited features, some modules disabled)
- [ ] `docker compose up` works on a clean Ubuntu 24.04, macOS 15, and Windows WSL2
- [ ] Seed data generates a realistic 50MW solar farm with 12 months of history
- [ ] All three modules (Yield, Carbon, Health) are populated with sample data
- [ ] The README makes a clear case for why a developer should buy URJA over building their own

**Story 2**: As Marcus, I want comprehensive API docs (OpenAPI/Swagger) so that I can understand the data model and start building my own integrations immediately.

**Acceptance Criteria**:
- [ ] `GET /docs` returns a fully navigable Swagger UI with all endpoints documented
- [ ] Every endpoint has request/response examples
- [ ] Every model has field descriptions, types, and constraints documented
- [ ] The API spec is lint-free (no OpenAPI spec violations)

**Story 3**: As Marcus, I want the backend code to have >90% test coverage and clear test patterns so that I can confidently modify the code without fear of breaking things.

**Acceptance Criteria**:
- [ ] `pytest --cov=backend --cov-fail-under=90` passes
- [ ] Tests are organized mirroring the source structure (tests/api, tests/services, tests/models)
- [ ] Every service module has unit tests for core logic
- [ ] Integration tests exist for API endpoints (using TestClient + test database)
- [ ] A Makefile or script exists to run tests with one command

---

## 5. Solution Overview

URJA is a full-stack renewable asset management boilerplate — a production-ready, deployable codebase that gives buyers an operational control plane for solar and wind energy monitoring, curtailment-aware dispatch optimization, digital carbon credit issuance, and predictive equipment health monitoring.

### What the Buyer Actually Receives

When a buyer purchases URJA on Gumroad at $149–$499, they receive:

1. **A private GitHub repository** (or zip download) containing the complete codebase — approximately 40,000–60,000 lines of well-structured Python, TypeScript, and SQL across ~300 files
2. **Sample data** for a 50MW solar farm with 12 months of 15-minute interval telemetry, curtailment events, carbon credit issuances, and maintenance logs — a fully populated dashboard on `docker compose up`
3. **Documentation suite**: ARCHITECTURE.md, API.md (auto-generated from OpenAPI), DATABASE.md, DEPLOYMENT.md, and a step-by-step tutorial
4. **Commercial license**: restricted commercial license for Basic/Pro (own-product use, no redistribution); full white-label license for Enterprise

### Key UX Flows

**Flow 1: First Run Experience (0–60 minutes)**
```
docker compose pull && docker compose up -d
→ Auto-runs migrations, loads seed data
→ Opens at http://localhost:3000 with live dashboard
→ Buyer sees: 6 KPI cards (MW generation, curtailment %, revenue lost, carbon credits, avg health score, active alerts)
→ Generation curve (Recharts) with duck curve overlay
→ Asset map (Leaflet) with inverter health markers
```

**Flow 2: Curtailment Analysis & Dispatch (Daily Use)**
```
Dashboard → Yield Module
→ See "Revenue Lost Today" in large green/yellow/red KPI card
→ Duck curve shows generation vs. grid price vs. curtailment events
→ "What If" slider: adjust battery capacity → see projected revenue recovered
→ Dispatch rule editor: configure battery threshold (€/MWh) and compute load routing
```

**Flow 3: Carbon Credit Generation (Weekly/Monthly)**
```
Dashboard → Carbon Module
→ Generation data auto-converts to CO2 equivalent via IPMVP methodology
→ "Mint Credits" button: creates Verra-compatible audit record
→ Audit trail shows: generation batch ID → kWh → methodology → CO2 eq → credit ID → timestamp
→ Portfolio view: total credits issued, pending, sold, retired
→ Export ESG report (PDF)
```

**Flow 4: Health Monitoring & Alerts (Ongoing)**
```
Dashboard → Health Module
→ Asset health score (0–100%) for each inverter/turbine
→ Trend chart showing health over last 30 days
→ Alert list: active, acknowledged, resolved
→ Configure alert thresholds per device type
→ Maintenance scheduler: create work order from alert
```

**Flow 5: TUI Dashboard (Ops Team, On-Site)**
```
Terminal → python dashboard-tui/app.py
→ Live overview screen: MW gen, curtailment alert, top 5 health issues
→ Carbon ledger: last 10 issuances with credit IDs
→ Keybindings: Tab to switch panels, / to search assets, q to quit
→ Color-coded: green (normal), yellow (warning), red (critical)
→ Updates every 15 seconds via ARQ worker
```

### Key Design Decisions

- **Decision 1 — Boilerplate over SaaS**: We chose a one-time purchase model over subscription SaaS because (a) no hosting costs or SLAs, (b) cash-flow positive from day 1, (c) zero direct competition in the boilerplate space, and (d) developer-led sales via Gumroad have a proven indie-hacker playbook (ShipFast, Supastarter, Syntax.fm). Trade-off: lower per-customer revenue ($149–$499 vs. $50K+/year) but zero delivery cost and infinite scalability.
- **Decision 2 — TimescaleDB over InfluxDB**: Full SQL + time-series hypertables means one database to learn, continuous aggregates for pre-computed rollups, and compatibility with the entire PostgreSQL ecosystem. Trade-off: slightly higher memory footprint per row vs. purpose-built TSDB.
- **Decision 3 — Textual TUI as differentiator**: The terminal dashboard is a unique selling point — no competitor offers it, and ops teams genuinely prefer terminal-based monitoring. Trade-off: requires additional development effort (~3 weeks for 3 screens) and documentation for non-terminal-native users.
- **Decision 4 — Sample data included**: We ship a full 12-month dataset because the "wow moment" for any buyer happens in the first 5 minutes. An empty dashboard is a terrible first impression. Trade-off: ~50MB in the repo (mitigated by Git LFS or compressed seed SQL dump).
- **Decision 5 — Three modules from day one**: Yield, Carbon, and Health ship together even though the dispatch engine and carbon pipeline are the core differentiators. Health gives operators a reason to keep the dashboard open daily. Trade-off: broader scope in v1, but each module is shallow enough to be completed in 2–3 weeks.

---

## 6. Technical Considerations

### Dependencies

| Dependency | Why Needed | Owner | Timeline Risk |
|-----------|-----------|-------|---------------|
| PostgreSQL 16 + TimescaleDB extension | Time-series hypertables for telemetry; continuous aggregates for hourly/daily rollups | Backend lead | Low — well-established OSS |
| Redis 7 | ARQ task queue; optional caching layer | Backend lead | Low — standard infra |
| ARQ (Python library) | Lightweight async task queue for telemetry ingest, carbon minting, health scoring | Backend lead | Low — mature library with active maintenance |
| SQLAlchemy 2.0 + Alembic | ORM and migrations; async-compatible | Backend lead | Low — industry standard |
| Next.js 16 App Router | Frontend framework; React Server Components for fast initial loads | Frontend lead | Medium — Next.js 16 is cutting-edge; API may shift during development |
| Tailwind v4 + shadcn/ui | Utility-first CSS + pre-built components; rapid dashboard development | Frontend lead | Low — mature ecosystem |
| Recharts | Composable React charts for generation curves, duck curves, health trends | Frontend lead | Low — stable library |
| react-leaflet | Map component for asset geo-visualization | Frontend lead | Low — stable, well-documented |
| Textual (Python TUI library) | Terminal UI framework | Backend lead | Low — mature; asyncio-native |
| pytest + pytest-asyncio | Backend testing | Backend lead | Low |
| Playwright | E2E frontend testing | Frontend lead | Low |
| Docker Compose | Container orchestration | DevOps | Low |

### Known Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Next.js 16 breaking changes during development | Medium | High | Pin Next.js version in package.json; test upgrades on a branch before merging; maintain fallback compatibility document |
| TimescaleDB hypertable performance at scale users | Low | Medium | Seed data covers 12 months of 15-min telemetry = ~35K rows/asset; benchmark with 50 assets (1.75M rows) to validate query performance; document scaling guidance |
| No Docker support for ARM-based M-series Macs (PostGIS) | Low | Medium | TimescaleDB has ARM64 images; document native macOS dev setup as alternative for Apple Silicon users |
| Low adoption due to niche market | High | Business risk | Mitigated by zero competition; target 50 sales/month is modest; if unconverted after 6 months, reposition as developer learning resource rather than production boilerplate |
| Buyers expect SaaS-level support | Medium | Medium | Set expectations clearly in README and Gumroad listing: "You buy the code, not the support." Priority support is Pro tier differentiator; Enterprise includes 1-hour call |
| Textual TUI compatibility with Windows terminals | Low | Low | Document that TUI is optimized for Linux/macOS; WSL2 on Windows works; native Windows terminal is best-effort |

### Open Questions (Must Resolve Before Dev Start)

- [ ] **Should the free tier (public GitHub repo) include the Carbon module?** If yes, we cannibalize the main differentiator. If no, the free tier is less compelling. — Owner: Alex — Deadline: 1 week from PRD sign-off
- [ ] **What telemetry ingestion rate does the sample seed target?** 15-minute intervals (standard for solar monitoring) vs. 1-minute (real-time, but 15x more data). — Owner: Backend Lead — Deadline: During architecture spike
- [ ] **Should we ship with a "lite" SQLite mode for development without Docker?** Makes evaluation faster but adds a second database codepath to maintain. — Owner: Backend Lead — Deadline: Sprint 1 planning
- [ ] **Gumroad or Lemon Squeezy for distribution?** Gumroad is proven (ShipFast, many boilerplates). Lemon Squeezy is newer but provides EU VAT handling and affiliate support. — Owner: Alex — Deadline: 2 weeks before launch
- [ ] **What is the minimal viable free tier?** Must demonstrate value without giving away the full product. Candidates: 1 module only (Yield), or time-limited full access (30-day trial code). — Owner: Alex — Deadline: Pre-launch sprint

---

## 7. Launch Plan

| Phase | Timeline | Audience | Success Gate |
|-------|----------|----------|-------------|
| **Internal Alpha** | Week 1–3 | Dev team + 2 external design partners (energy consultants known via personal network) | All 3 modules compile and run; `docker compose up` works on clean Ubuntu; seed data loads; core dashboard renders with real KPIs |
| **Closed Beta** | Week 4–6 | 20–30 buyers from early waitlist (sourced from X/Twitter build-in-public + Indie Hackers) | <5% critical error rate; all tier features functional; 80%+ of beta users complete `docker compose up` successfully on first attempt |
| **Public GA** | Week 7–8 | General public via Gumroad + GitHub | Metrics on track; zero open P0/P1 bugs; help docs and FAQ published; support channel established |
| **Post-Launch** | Week 9–16 | All buyers | Track revenue vs. target; analyze support tickets for common issues; write 4-part Dev.to tutorial series; iterate on top feedback |

### Rollback & Contingency

- **Rollback trigger**: If seed data fails to load in >5% of deployments, or if a security vulnerability is reported, pause sales and issue fix before resuming.
- **Communication**: Email Gumroad buyers with fix timeline within 24 hours of confirmed issue.
- **If launch fails (<10 sales in first 30 days)**: Conduct buyer exit interviews. Evaluate repositioning as a learning resource ($49 tier) or open-sourcing core with premium modules. Do not sink more time without evidence of demand.

---

## 8. Appendix

- [Idea Validation & Market Research](./idea/idea.md) — Full competitive analysis, curtailment market data, boilerplate positioning rationale
- [README.md](../../README.md) — Public-facing product page with features, tech stack, pricing, quick start
- [AGENTS.md](../../AGENTS.md) — Project context, session log, architecture decisions
- [Competitive Landscape Table](./idea/idea.md#2-competitive-landscape) — 6 competitors analyzed with gaps identified
- **Reference Products**: Power Factors Unity (enterprise SaaS), Fluence Mosaic (AI bidding), ShipFast (boilerplate distribution model), Verra + Hedera (carbon MRV methodology)

---

*PRD v1.0 — Next step: Schedule design sprint for database schema and API contract.*
