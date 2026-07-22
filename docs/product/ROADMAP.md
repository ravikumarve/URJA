# ROADMAP: URJA — Renewable Asset Management Boilerplate

**Status**: Active  
**Author**: Alex (Product Manager)  
**Last Updated**: 2026-07-22  
**Version**: 1.0  
**Framework**: Now / Next / Later

> This roadmap is a **strategic direction document**, not a release schedule. Initiatives move between columns based on validation signals (sales data, buyer feedback, market shifts), not calendar dates. Confidence levels indicate how much we know about the problem space. Low confidence = learn first, build later.

---

## Roadmap Philosophy

URJA is a **boilerplate**, not a SaaS platform. This has specific implications for the roadmap:

- **Most features ship as optional modules** — buyers activate what they need. A clean energy consultant needs Carbon MRV; a solar farm operator needs Health alerts; a developer wants all three to study.
- **Enterprise features are gated by buyer demand** — we don't build multi-tenancy or Helm charts until someone pays for them.
- **"Done" means shipped in a release and documented** — features that don't have docs, tests, and a migration path are not done.
- **Revenue is the signal** — at 50 sales/month, we have a business. At <10 sales/month, we pivot or cut scope.

---

## Now (Active — Current Month)

**Theme: Ship the foundation. Make `docker compose up` magical.**

### Phase 1: Database Schema + API Scaffold + Docker Setup

| Item | Confidence | Effort | Success Gate |
|------|-----------|--------|-------------|
| SQLAlchemy 2.0 models for all 6 bounded contexts (Asset, Telemetry, Dispatch, Carbon, Health, Auth) | High (standard ORM patterns) | 5 days | Models match ADR-003 (TimescaleDB hypertables + continuous aggregates). Alembic migrations run clean on empty DB. |
| FastAPI REST scaffold with health check, versioned router (`/api/v1`), CORS, middleware stack | High (FastAPI is mature) | 2 days | `GET /api/v1/health` returns `{"status": "ok"}`. Swagger UI at `/docs` renders without lint errors. |
| Docker Compose with 5 containers (api, frontend, tui, db, redis) | High (ADR-009 ratified) | 2 days | `docker compose up -d` completes in <2 minutes on Ubuntu 24.04, macOS 15, Windows WSL2. All health checks pass. |
| Alembic + TimescaleDB continuous aggregate setup for hourly/daily rollups | Medium (TimescaleDB-specific) | 3 days | 4 continuous aggregates defined per ADR-008. `hourly_generation` refreshes automatically within 1-hour lag window. |
| ARQ worker with cron jobs for health scan (15min), weather refresh (6h), pricing refresh (1h), daily rollup (midnight) | High (ADR-004 ratified) | 2 days | Worker starts with `WorkerSettings`, cron jobs execute on schedule, logs show successful task completion. |
| Seed data pipeline: compressed SQL dump + startup check script | High (ADR-010 ratified) | 2 days | `docker compose up` on empty DB loads 2.9M rows in <30 seconds. Dashboard is populated on first load. |

**Phase 1 complete when**: A buyer runs `docker compose up -d`, opens `http://localhost:3000`, and sees a functional (if unstyled) dashboard with seeded data.

### Phase 2: Dashboard Frontend

| Item | Confidence | Effort | Success Gate |
|------|-----------|--------|-------------|
| KPI cards (Today's Generation, Curtailment %, Revenue Lost, Carbon Credits, Health Score, Active Alerts) | High (shadcn/ui cards) | 3 days | 6 cards render above the fold at 1366×768. Color-coded (green/yellow/red). Update within 15s of new telemetry. |
| Generation curve with duck curve overlay (Recharts AreaChart) | Medium (complex chart) | 4 days | Chart shows 24h generation vs. grid price. Duck curve visible for solar assets. Tooltip shows exact values on hover. |
| Asset map (Leaflet with health-colored markers) | Medium (map integration) | 3 days | 40 inverter markers on a Leaflet map. Green/yellow/red based on health score. Click shows tooltip with asset details. |
| Carbon credit portfolio page | Medium (multi-tab layout) | 4 days | Portfolio view: total credits (issued, pending, sold, retired). Issuance history table with export button. |
| Health page with asset score trend + alert list | Medium (data table + chart) | 4 days | Asset health scores sorted ascending. 30-day trend chart. Alert list with acknowledge/dismiss workflow. |
| Responsive layout + dark mode | Medium (Tailwind v4) | 3 days | Dashboard usable on tablet (768px). Dark mode toggle works across all pages. |

**Phase 2 complete when**: All persona stories for Elena (farm operator) and Priya (consultant) are demonstrable. Dashboard loads in <2s on first paint with 12-month seeded data.

### Phase 3: Textual TUI + ML Health Models + Test Suite

| Item | Confidence | Effort | Success Gate |
|------|-----------|--------|-------------|
| Overview TUI screen (MW gen, alerts, stats) | Medium (Textual is young) | 4 days | 4 stat widgets + generation table + alert strip. Updates every 15s. Keyboard-nav: Tab, /search, q to quit. |
| Curtailment TUI screen (events, revenue impact, dispatch log) | Medium | 3 days | Active curtailment events table. Revenue lost widget. RichLog for dispatch decisions. |
| Carbon TUI screen (last 10 issuances, portfolio summary) | Medium | 2 days | Credit issuances table. Portfolio totals (issued, pending, sold, retired). |
| Health TUI screen (asset scores, active alerts) | Medium | 2 days | Asset health scores sorted ascending. Active alerts count. Configurable threshold display. |
| ML anomaly detection (z-score, moving average deviation) | Low (needs validation) | 5 days | Detects >20% power drop sustained for 15+ minutes. False positive rate <5% against seeded data. |
| Backend test suite (pytest, 90%+ coverage) | High (standard practice) | 5 days | `pytest --cov=backend --cov-fail-under=90` passes. Tests mirror source structure. |
| Frontend E2E tests (Playwright) | Medium | 3 days | Critical flows tested: dashboard load, map interaction, carbon export, health alert cycle. |

**Phase 3 complete when**: All 3 modules have test coverage >90%. TUI runs in terminal AND browser (via textual-web). Health module detects anomalies on seeded data.

### Phase 4: Gumroad Launch + Documentation + Marketing

| Item | Confidence | Effort | Success Gate |
|------|-----------|--------|-------------|
| Gumroad product listing with tiered pricing ($149/$249/$499) | High (proven distribution) | 1 day | Listing live with screenshots, feature table, FAQs. Purchase→GitHub access flow automated. |
| ARCHITECTURE.md + API.md + DATABASE.md + DEPLOYMENT.md | High (docs are critical) | 5 days | Every document reviewed for accuracy. Architecture doc matches ADR decisions. API doc generated from OpenAPI. |
| Dev.to 4-part tutorial series (draft) | Medium (content marketing) | 5 days | Series: "From Zero to 50MW Solar Farm" — Part 1: Setup, Part 2: Dashboard, Part 3: Carbon, Part 4: TUI. |
| Build-in-public thread on X/Twitter (weekly updates) | Medium (audience building) | Ongoing | 2–3 posts/week showing progress, screenshots, learnings. Target: 500 followers by launch. |
| Free tier GitHub repo (public, limited features) | Medium (conversion funnel) | 2 days | Public repo with README, docker-compose.yml (basic), seed data. Carbon module disabled. "Buy Pro to unlock" callout. |
| Launch checklist + contingency plan | High | 1 day | Rollback triggers defined. Support channel (GitHub Issues) established. Post-launch metrics dashboard ready. |

**Phase 4 complete when**: First paid purchase confirmed. `docker compose up` works for the buyer. Zero P0/P1 bugs in first 72 hours.

---

## Next (Next 1-2 Quarters)

**Theme: Expand coverage. Validate revenue. Build moat.**

### External API Integrations

| Initiative | Confidence | Est. Effort | Expected Outcome |
|-----------|-----------|-------------|------------------|
| Weather provider integration (OpenWeatherMap, or SolarGIS) | Medium — depends on API availability | 2 weeks | Automated weather telemetry ingestion. Solar irradiance data enhances generation forecasting. |
| Grid price API integration (Nord Pool, CAISO, ERCOT) | Medium — regional fragmentation | 3 weeks | Live price overlay on generation curve. Dispatch optimization uses real-time prices. |
| ARQ connector framework (pluggable data sources) | Medium | 2 weeks | Buyers write a 20-line Python class to add a new data source. Documented interface with example. |

**Success metric**: >30% of Pro/Enterprise buyers activate at least one external integration within 30 days of purchase.  
**Confidence**: Medium — this is a table-stakes feature for integrators (Dmitri persona). Risk is API fragmentation across regions.

### Real SCADA Protocol Support (Sample Connectors)

| Initiative | Confidence | Est. Effort | Expected Outcome |
|-----------|-----------|-------------|------------------|
| Modbus TCP sample connector (in `examples/scada/`) | Medium — hardware varies | 2 weeks | Working example: read holding registers from a simulated Modbus device. Maps to URJA telemetry schema. |
| IEC 61850 sample connector (using pyIEC61850 or libiec61850) | Low — protocol is complex | 3 weeks | Working example: read measurements from a simulated IED. Documentation covers MMS, GOOSE, Sampled Values. |
| OPC-UA sample connector (using opcua-asyncio) | Medium — well-documented | 2 weeks | Working example: browse address space, subscribe to data changes. Maps to URJA telemetry schema. |

**Success metric**: 3 sample connectors documented and tested. At least 1 community contribution (PR or issue) showing a real hardware integration.  
**Confidence**: Low-Medium — SCADA integration depth depends on hardware availability for testing. Sample connectors validate the ingestion API design.

### Email Alert Notifications

| Initiative | Confidence | Est. Effort | Expected Outcome |
|-----------|-----------|-------------|------------------|
| Alert → email notification pipeline (SendGrid / SMTP) | High (standard pattern) | 1 week | Configurable alert rules → email dispatch. Buyer sets SMTP settings in env. Rate-limited (max 5 emails/asset/hour). |
| Digest email (daily/weekly summary) | High | 1 week | Automated email with KPI summary, top alerts, carbon credit status. HTML template customizable. |

**Success metric**: >50% of buyers configure email notifications within 14 days.  
**Confidence**: High — email is the most requested feature in beta feedback.

### Export/Import: CSV, PDF Reports for ESG Compliance

| Initiative | Confidence | Est. Effort | Expected Outcome |
|-----------|-----------|-------------|------------------|
| CSV export for all data tables | High (standard feature) | 3 days | Every table page has "Export CSV" button. Includes date range filter. <2s for 12-month dataset. |
| PDF report generation (WeasyPrint or Playwright) | Medium — PDF layout is fiddly | 2 weeks | ESG report: generation (MWh), avoided CO2 (tons), credits issued, revenue from carbon sales. White-labelable (buyer logo). |
| Scheduled export (daily/weekly email or webhook) | Medium | 1 week | ARQ cron job generates report and emails or POSTs to webhook URL. |

**Success metric**: Priya persona Story 3 acceptance criteria met. PDF generates in <10s for 12-month dataset.  
**Confidence**: Medium — PDF generation quality depends on template investment. CSV is trivial.

### User Roles & Team Management

| Initiative | Confidence | Est. Effort | Expected Outcome |
|-----------|-----------|-------------|------------------|
| Role-based access control (Admin, Operator, Viewer) | High (JWT claims already designed) | 2 weeks | 3 roles with different permissions. Admin: full control. Operator: can acknowledge alerts, run dispatch. Viewer: read-only. |
| Team invite flow (email invitation → accept → role assignment) | Medium | 1 week | Admin enters email, system sends invite link. Recipient creates account, assigned to org with selected role. |
| Audit log for all user actions | High | 1 week | Every create/update/delete logged with user, timestamp, old/new values. Viewable by Admin only. |

**Success metric**: Enterprise buyers ($499) can add 5+ team members within 10 minutes of deployment.  
**Confidence**: High — standard auth pattern. Risk is invite email deliverability.

### Kubernetes Helm Chart (Enterprise)

| Initiative | Confidence | Est. Effort | Expected Outcome |
|-----------|-----------|-------------|------------------|
| Helm chart for production deployment | Medium — depends on buyer demand | 2 weeks | Chart with Deployment, Service, Ingress, PVC, ConfigMap. Works on EKS, AKS, GKE. |
| Documentation: "URJA on Kubernetes" | Medium | 3 days | Step-by-step guide with `helm install`. Covers TLS, scaling, backup. |

**Success metric**: 3+ Enterprise buyers request and use the Helm chart.  
**Confidence**: Low-Medium — ADR-009 explicitly deferred K8s. Only build if buyers pay for it.

---

## Later (3-6 Month Horizon)

**Theme: Scale reach. Open the platform. Explore adjacencies.**

### White-Label / Multi-Tenant Admin Console

| Initiative | Confidence | Est. Effort | Expected Outcome |
|-----------|-----------|-------------|------------------|
| Multi-org admin panel (super admin view across all deployments) | Low — contradicts boilerplate model | 4 weeks | Dashboard of all buyer deployments (if they opt-in). Usage stats, version tracking, update notifications. |
| Branding customization UI (logo, colors, domain) | Medium | 2 weeks | Admin settings page for brand config. Changes apply without code deploy. |
| Reseller license management | Low | 2 weeks | Enterprise buyers can generate sub-licenses for their clients. Usage tracking per sub-license. |

**Decision gate**: Only build if Enterprise tier consistently generates >50% of revenue and buyers explicitly request white-label tooling. Earlier Investment in this direction would distract from core product.  
**Confidence**: Low — the self-hosted model makes multi-tenant admin inherently awkward. Revisit at 500+ sales.

### Mobile App (Dashboard-Only, React Native)

| Initiative | Confidence | Est. Effort | Expected Outcome |
|-----------|-----------|-------------|------------------|
| React Native app with dashboard views (Yield, Carbon, Health) | Low — PRD deferred this | 6 weeks | KPI cards, generation curve, asset map, health alerts. Read-only. Same API backend. |
| Push notifications (via Expo or Firebase) | Low | 2 weeks | Alert → push notification on mobile. Configurable per alert type. |
| App Store / Play Store submission | Low | 2 weeks | iOS and Android builds. Minimal app store listing. |

**Decision gate**: PRD section 3 explicitly defers mobile. Only build if >20% of buyers request it via support or survey. Even then, a responsive PWA may suffice.  
**Confidence**: Very Low — mobile is a distraction for v1–v2. The target personas use desktops and terminals.

### Plug-In Marketplace

| Initiative | Confidence | Est. Effort | Expected Outcome |
|-----------|-----------|-------------|------------------|
| Dispatch strategy plug-in registry | Medium — PRD Story for Dmitri | 3 weeks | `BaseDispatchStrategy` interface. Third-party strategies installable via `pip install urja-dispatch-my-algo`. |
| Weather provider plug-in registry | Medium | 3 weeks | Same pattern: base class + pip-installable providers. Documented in 2-page tutorial. |
| Carbon methodology plug-in registry | Medium | 3 weeks | Beyond IPMVP: Verra, Gold Standard, CDM methodologies as plug-ins. |
| Simple plug-in directory in docs | Medium | 1 week | List of community/partner plug-ins. Submission guidelines. |

**Decision gate**: Ship the dispatch strategy plug-in in Next (Dmitri's Story 1). Weather and carbon plug-ins are Later because they depend on a critical mass of buyers to create the ecosystem.  
**Confidence**: Medium — the plug-in pattern is architecturally sound (ADR-002 modular monolith supports it), but ecosystem development is unpredictable.

### Real-Time WebSocket Push for Telemetry

| Initiative | Confidence | Est. Effort | Expected Outcome |
|-----------|-----------|-------------|------------------|
| WebSocket endpoint for live telemetry stream | Medium — PRD deferred | 3 weeks | WebSocket handshake, JWT auth, telemetry event stream. Dashboard and TUI both subscribe. |
| Server-Sent Events fallback for environments where WS is blocked | Medium | 1 week | SSE endpoint with same event schema. Auto-detect in frontend: prefer WS, fallback to SSE, fallback to polling. |

**Decision gate**: Only build if polling performance is a documented pain point in buyer feedback. Initial polling at 15s intervals is acceptable for monitoring (per PRD).  
**Confidence**: Medium — technical risk is low, but it's a significant refactor of the frontend data-fetching pattern.

### Integration with Verra Registry API

| Initiative | Confidence | Est. Effort | Expected Outcome |
|-----------|-----------|-------------|------------------|
| Verra registry API client for automated credit issuance | Low — API access may require partnership | 4 weeks | POST credit issuance to Verra (or Hedera Guardian). Poll for verification status. Update URJA credit status. |
| Verra methodology template (VM0004, ACM0002, etc.) | Low — methodology expertise needed | 3 weeks | Pre-built methodology configs for common solar/wind carbon methodologies. Buyer selects methodology during credit minting. |

**Decision gate**: This is a high-value differentiator but requires either (a) a Verra API partnership or (b) Hedera Guardian as an intermediary. Investigate Hedera Guardian integration first — it's open-source and the PRD mentions it as a reference. Only build if a carbon credit buyer (consultant or developer) explicitly commits to using the Verra pipeline.  
**Confidence**: Very Low — regulatory and partnership dependencies are outside our control.

---

## What We're Not Building (and Why)

| Feature | Reason for Exclusion | Future Possibility |
|---------|---------------------|-------------------|
| **SCADA hardware gateway** | We provide API templates and sample connectors. Hardware-specific integration (SMA inverters, Siemens PLCs) is the buyer's responsibility or a consulting engagement. | Sample connectors for top 3 inverter brands (SMA, SolarEdge, ABB) as community contributions. |
| **Carbon credit certification** | URJA provides the MRV pipeline (measurement, reporting, verification-ready data). Certification against Verra, Gold Standard, or CDM is the buyer's responsibility — we cannot certify credits without being a registry-approved verification body. | Pre-built methodology templates reduce certification friction but do not replace third-party verification. |
| **Enterprise SaaS platform** | URJA is a self-hosted boilerplate. We do not operate a multi-tenant SaaS, manage customer infrastructure, or provide uptime SLAs. This is the core business model decision (ADR-001). | If buyer demand justifies it, a managed cloud option could be a separate product line at a different price point. Not before 1,000+ sales. |
| **Competing with Power Factors / Fluence** | Those companies serve 500MW+ utility-scale operators with enterprise sales teams and $50K+/year contracts. URJA serves developers, consultants, and small operators (10–200MW). Different market, different sales model. | URJA's architecture can scale up. The Enterprise tier ($499) is for buyers who want to do exactly that — but they do the scaling work. |
| **Real-time control systems** | URJA is a monitoring and optimization platform, not a real-time control system. We do not send commands to inverters, breakers, or batteries. Dispatch optimization produces recommendations, not direct SCADA commands. | Read-only → read-write is a major scope expansion. Only consider if explicitly requested by multiple Enterprise buyers. |
| **Mobile app (v1)** | PRD section 3 explicitly defers mobile. Target personas use desktops and terminals. <5% of dashboard usage is mobile. | React Native app at Later horizon if buyer demand materializes. |
| **Localization / i18n** | English only. Target buyers (developers, consultants, integrators) are English-literate. i18n would add ~20% to every UI change cost. | Enterprise tier could include i18n if a buyer pays for it. |
| **SOC 2 / ISO 27001 compliance certifications** | The boilerplate includes security best practices (env-based secrets, parameterized queries, JWT auth) but we are not certified and do not intend to be. Compliance is the buyer's responsibility. | Documentation for how to achieve compliance using URJA's architecture could be a paid add-on. |
| **ERP integrations (NetSuite, SAP, etc.)** | v1 exports CSV and JSON. Integration with specific accounting/ERP systems is the buyer's responsibility. API is documented for custom integrations. | Pre-built ERP connectors as plug-ins if specific buyer demand emerges. |

---

## Success Metrics & Confidence Levels

### North Star Metric

**Monthly Revenue Equivalent (MRE)**: Monthly sales volume × average selling price.  
**Target**: $9,950/month = 50 sales × $199 avg ASP.  
**Validation window**: 180 days post-launch.

### Initiative Confidence Scoring

| Level | Meaning | Action |
|-------|---------|--------|
| **High** | Problem understood. Solution well-defined. Low technical risk. | Build now. Ship fast. |
| **Medium** | Problem validated. Solution has some unknowns. | Build with validation gates. Prototype before full investment. |
| **Low** | Problem or solution unvalidated. Multiple unknowns. | Learn before building. Spike or defer. |
| **Very Low** | Speculative. Requires external factors. | Do not build. Collect evidence first. |

### Tracking Progress

| Phase | Timeline (Target) | Confidence | Actual | Status |
|-------|------------------|------------|--------|--------|
| Phase 1: DB + API + Docker | Month 1 | High | — | ⬜ Not started |
| Phase 2: Dashboard frontend | Month 2 | High | — | ⬜ Not started |
| Phase 3: TUI + ML + Tests | Month 3 | Medium | — | ⬜ Not started |
| Phase 4: Launch | Month 4 | Medium | — | ⬜ Not started |
| External integrations | Months 5–8 | Medium | — | ⬜ Not started |
| SCADA sample connectors | Months 5–8 | Low-Medium | — | ⬜ Not started |
| Email notifications | Months 5–8 | High | — | ⬜ Not started |
| Export/Import (CSV, PDF) | Months 5–8 | Medium | — | ⬜ Not started |
| User roles & team mgmt | Months 5–8 | High | — | ⬜ Not started |
| Helm chart (Enterprise) | Months 5–8 | Low-Medium | — | ⬜ Not started |
| White-label admin console | Months 9–14 | Low | — | ⬜ Not started |
| Mobile app | Months 9–14 | Very Low | — | ⬜ Not started |
| Plug-in marketplace | Months 9–14 | Medium | — | ⬜ Not started |
| WebSocket push | Months 9–14 | Medium | — | ⬜ Not started |
| Verra registry integration | Months 9–14 | Very Low | — | ⬜ Not started |

### Review Cadence

- **Weekly**: Phase tracking. Update status column. Flag blockers.
- **Monthly**: Initiative confidence reassessment. Market signal review (sales, support tickets, buyer interviews).
- **Quarterly**: Full roadmap refresh. Add/remove/reprioritize initiatives based on revenue data and buyer feedback.

### Pivot / Kill Criteria

| Signal | Action |
|--------|--------|
| <10 sales in first 30 days post-launch | Conduct buyer exit interviews. Evaluate repositioning as learning resource ($49 tier) or open-sourcing core with premium modules. |
| Support tickets >50/100 purchases | Hire part-time support person or simplify onboarding. Problem is expectations misalignment, not product complexity. |
| Zero sales of Pro tier ($249) in 90 days | Merge Pro features into Basic ($149), drop Pro tier. Simplify pricing to 2 tiers. |
| >50% of support requests are "how do I customize X?" | Invest in customization tutorial video. If pattern persists, ship customization UI instead of env-var config. |
| Competitor enters boilerplate space with energy domain | Reassess differentiation. Double down on TUI + Carbon MRV + ML — hardest to replicate. |

---

## Appendix: Initiative Dependency Map

```
Phase 1 (Foundation)
  └── Phase 2 (Dashboard)
       └── Phase 3 (TUI + ML + Tests)
            └── Phase 4 (Launch)
                 │
                 ├── External Integrations ───┐
                 ├── SCADA Connectors ────────┤
                 ├── Email Notifications ─────┤
                 ├── Export/Import ───────────┤
                 ├── User Roles ──────────────┤
                 └── Helm Chart ──────────────┘
                                            │
                     ┌──────────────────────┘
                     ▼
              White-Label Admin Console
              Mobile App
              Plug-in Marketplace
              WebSocket Push
              Verra Integration
```

---

*ROADMAP v1.0 — Next step: Begin Phase 1 implementation. Move initiatives from "Not started" to "In progress" as they are scoped and assigned.*
