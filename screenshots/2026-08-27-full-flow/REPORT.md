# URJA Full Flow Visual QA — 2026-08-27

**Scope:** CLI TUI (4 screens) + WEB (7 routes, 10 screenshots)  
**Env:** Dell Latitude 3460 · mock API :8000 (python /tmp/opencode/urja_mock_api.py) · Next.js 16.2.11 :3000 · Textual 8.2.8 headless 132×36  
**Artifacts:** `screenshots/2026-08-27-full-flow/` · 17 images (10 WEB + 4 TUI + 3 SVG source)

---

## Index — Every Image Saved

| # | File | Route / Screen | Capture |
|---|------|----------------|---------|
| 01 | `01-login.png` | WEB /login (fresh) | Full page |
| 02 | `02-login-error.png` | WEB /login (wrong creds) | Full page |
| 03 | `03-overview-top.png` | WEB / (overview KPI + chart top) | Full page |
| 04 | `04-overview-chart.png` | WEB / (chart scrolled) | Viewport |
| 05 | `05-assets.png` | WEB /assets (KPIs + map top) | Full page |
| 05b | `05-assets-table.png` | WEB /assets (sites + assets table scrolled) | Viewport |
| 06 | `06-yield-top.png` | WEB /yield (KPIs + tables top) | Full page |
| 06b | `06-yield-chart.png` | WEB /yield (generation curve) | Viewport |
| 07 | `07-carbon.png` | WEB /carbon | Full page |
| 08 | `08-health-top.png` | WEB /health (KPIs top) | Full page |
| 08b | `08-health-bottom.png` | WEB /health (tables scrolled) | Viewport |
| 09 | `09-settings.png` | WEB /settings | Full page |
| 10 | `10-logout-login.png` | WEB logout → /login | Full page |
| T1 | `tui-01-overview.png` (.svg) | TUI Overview (key 1) | Headless SVG→PNG via browser |
| T2 | `tui-02-curtailment.png` (.svg) | TUI Curtailment (key 2) | Headless |
| T3 | `tui-03-carbon.png` (.svg) | TUI Carbon (key 3) | Headless |
| T4 | `tui-04-health.png` (.svg) | TUI Health (key 4) | Headless |

---

## WEB — Per-Image Verdict

### 01 — `01-login.png` ✅ CLEAN
Centered tactical panel, `URJA` amber wordmark + lightning bolt (#ff5e00), tagline `DEPLOY CLEAN ENERGY INTELLIGENCE.` in sand-muted, two inputs (EMAIL/PASSWORD) with sand border on surface-mid, orange primary `SIGN IN` full-width, footer `[ TACTICAL OPS ]` with orange brackets. Corner hairline brackets intentional. No overflow, no contrast issues.

### 02 — `02-login-error.png` ✅ CLEAN
Same as 01 after submitting `wrong@example.com / wrongpass`. Error banner appears directly below password: ` [!] Invalid email or password` on `bg-tactical-red/10` with `border-tactical-red/40`, text red, rounded. Layout does not shift. Correct `role=alert`.

### 03 — `03-overview-top.png` ⚠️ **FLAGGED — REVENUE OVERFLOW (CRITICAL)**
6 KPI cards in single row (`GEN_MONITOR`, `YIELD_MONITOR`, `ALERTS`, `CARBON`, `REVENUE`, `FLEET HEALTH`). Data correct (16.1 MW / 6 assets, 71 MWh, 2 alerts, 3,450.5 credits, 78.0/100).
**Issue:** `REVENUE` card value `80,250` with suffix `₹/` is clipped at the right card border — `₹/kWh` is truncated to `₹/` . The value uses `text-3xl` amber and the card padding is insufficient at 1280w. Same row `FLEET HEALTH 78.0 /100` is tight but fits. The `REVENUE` card's `EST @ ₹5.00/KWH` subtitle + large value exceed available width. Repro on every load. Fix: reduce `text-3xl` to `text-2xl` on that card, or add `truncate`/`min-w-0` + `whitespace-nowrap`, or widen card / use `flex-wrap`.
Also note `ALERTS` card has strong orange glow (border + shadow) — intentional for active alerts.

### 04 — `04-overview-chart.png` ✅ (with minor notes)
`GENERATION CURVE — TODAY [LIVE]` — ComposedChart with dual axes. Amber fill area (MW left 0–12) + orange price line (₹/kWh right 0–8) both render. Hours 00–13. Tooltip at 08 shows `price : 1.75` (amber) and `mw : 0` — functional. Minor: tooltip key casing `price` vs `mw` vs axis label `MW` — inconsistent case. Not blocking. No fragment-empty–SVG bug — this is the fixed single-ComposedChart build (commit d5da8a1).

### 05 — `05-assets.png` 🚩 **FLAGGED — MAP WATERMARK (CRITICAL)**
KPI row: 6 assets / 30.0 MW / 1 sites / 75.8 health — consistent. `SITE ASSET MAP — 6 GEOLOCATED` panel renders Leaflet with 6 dot markers (3 amber/orange + 3 green by health) + legend (`≥80%`, `50-79%`, `<50%`). **Map tiles are broken:** diagonal repeating watermark `API KEY REQUIRED carto.com/basemaps/apikey` covers the entire map. Carto basemap now requires API key — the current `NEXT_PUBLIC_MAP_STYLE` or Leaflet tile URL is invalid for demo/fresh clones. Impact: Gumroad buyers see a broken map on first run. Fix: switch to free `https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png` or Stadia `alidade_smooth_dark` without key, or proxy via `carto-light` free variant. Markers themselves are correctly positioned and color-coded.

### 05b — `05-assets-table.png` ✅ CLEAN
Scrolled view reveals `SITES (1)` table: `ALPHA-DESERT-01 | ADS-01 | 50.0 MW | Asia/Kolkata | 6 assets | ACTIVE` and `ASSETS (6 SHOWN)` table 6 rows (INV-01 88% … INV-06 55% MAINTENANCE). Health color gradient flows amber→green→red correctly, status `ONLINE` green vs `MAINTENANCE` orange. No clipping, zebra-free, tactical borders present.

### 06 — `06-yield-top.png` ⚠️ **FLAGGED — MOCK DATA DUPLICATION (MODERATE)**
4 KPI cards: `REVENUE_LOST ₹51,030 DECREASING` (orange glow) correctly highlighted vs 3 others stable. `CURTAILMENT EVENTS (3)` table shows 3 rows but **all rows are identical clones:** `16:02:00 INV-02 18m 4,200 ₹2.80 ₹11,760` with only Status differing (ACTIVE / RESOLVED / RESOLVED). Same for `DISPATCH DECISIONS LOG` on right: three identical lines `16:02:44 grid_curtail_response · INV-02 [CURTAILMENT] reduced 4.2MW`. This is mock_api.py generating duplicate timestamps — not a layout bug but a data-realism bug that will be obvious to buyers during demo. Fix: vary `time`, `asset`, `curtailed` in mock handler (like health/curtailment mock does elsewhere).

### 06b — `06-yield-chart.png` ✅ CLEAN
Same chart component as overview, hourly data: amber MW area from hour 11→13 ramp ~11 MW + orange price line from hour 05 flat 1.75 then rising to ~5 at hour 13. Dual axes labeled `MW` left + `₹/kWh` right (vertical orange). Grid `#2c2723`, gradient fill. No overflow.

### 07 — `07-carbon.png` ⚠️ **FLAGGED — TRUNCATION (MINOR)**
4 KPI cards: `TOTAL_ISSUED 3,450.5`, `PENDING 0`, `RETIRED 850`, `AVAILABLE 9` — Increasing/Stable badges correct. `CREDIT LEDGER (5)` table: credit IDs shown as `c-100000…` with ellipsis + methodology `IPMVP` — acceptable. **Right panel `PORTFOLIO SUMMARY` → `REGISTRY TX VCS-2026-08-` is truncated mid-hash** (cuts at hyphen, no wrapping). Fix: add `truncate` + `title` tooltip or `break-all` on that value. Otherwise clean, no table overflow.

### 08 — `08-health-top.png` ✅ CLEAN
KPIs: `ACTIVE_ALERTS 2` (orange glow), `AVG_HEALTH 72/100`, `CRITICAL 1` (orange glow), `WARNINGS 1`. Correct.

### 08b — `08-health-bottom.png` ⚠️ **FLAGGED — SCROLL CROPPING (MODERATE)**
Scrolled view: `HEALTH SCORES (6)` table 6 rows with score→anomaly→flags, colors correct (48% red, 67–87% amber→green). `ACTIVE ALERTS (2)` + `ALERT FEED — MOST RECENT FIRST` (2 rows). **Visual cropping bug:** when scrolling `main`, the top KPI row gets sliced mid-card (the `2` and `72 /100` are cut horizontally). The `main` scroll container + sticky header interaction leaves a hard cut line. Fix: add `scroll-pt` / `overflow-anchor` or ensure `main` has `pb` that accounts for header height; test scroll to 400–600px. Not critical but visible in QA screenshots.

### 09 — `09-settings.png` ✅ CLEAN
2×2 bento: `API KEYS` (PRODUCTION API ACTIVE, masked `urja_prod_a1b2…` + SCOPE/EXPIRES + COPY), `TEAM` (Ravi Kumar ADMIN ACTIVE, Field Tech VIEWER), `SITE INFO` (instruction to `PUT /v1/sites/{site_id}` + amber code style), `THEME` (AMBER CRT TACTICAL ACTIVE yellow border + `SAVE CHANGES` orange). No overflow, all borders render.

### 10 — `10-logout-login.png` ✅ CLEAN
LOGOUT button → redirect to `/login` confirmed (302 → guarded route). Login panel returns empty, no stale token. Auth guard works.

**Global WEB notes:**
- Typography consistent: JetBrains Mono for data, tactical amber `#ffb703` + orange `#ff5e00` on near-black `#0a0500`. No font-loading FOIT observed.
- Sidebar `TACTICAL COMMAND CENTER` header with `OP_MODE: TACTICAL` + operator pill correct on all pages.
- `v1.0.4` in sidebar — version string stale vs backend (minor, update on release).
- No horizontal scroll, no modal pop-in, no console errors (checked during pricing sprint).

---

## CLI TUI — Per-Image Verdict

Rendered headless 132×36 via `UrjaTUI().run_test()` + `save_screenshot()` (SVG with Rich Fira Code), rasterized via browser for this report. All 4 screens use `theme.tcss` amber CRT (`#0a0500` bg, `#ffb703` primary, `#8a6300` dim).

### T1 — `tui-01-overview.png` ⚠️ **FLAGGED — LARGE EMPTY VOID (MODERATE)**
Header: `URJA_CLI // TACTICAL_OPS` black on amber, `[DUST_STORM_ACTIVE]` orange pill, `SITE: ALPHA-01` — correct. KPI row: 4 bordered cards (`YIELD_MONITOR 21.2 MW`, `WEATHER_SYSTEM 42.0 KM/H`, `SOILING_RATIO 83%`, `REVENUE_LOST ₹256,382`) centered — titles at bottom orange, values amber. `ASSET_DIAGNOSTICS (3-SIGMA)` DataTable 12 rows with color per health (INV-02 62% 61C THERMAL_THROTTLE orange, ARR-A1 41% 48C HEAVY_SOILING red, INV-07 62% 78C OVERHEAT red) — correct. `ARQ_WORKER_TAIL` RichLog 2 lines. **Layout:** ~35% of screen below the worker log is solid black empty space before the footer. The `Vertical` compose does not expand `RichLog`/`DataTable` to fill height; `1fr` distribution missing. Fix: set `DataTable { height: 1fr }` + `RichLog { height: 8 }` or similar, or `Screen { layout: vertical }` with explicit sizes.
Minor: worker tail label `ARQ_WORKER_TAIL` double underscore; log line `[08:25:33] ingest  : DNI dropped 52%` has extra space before colon.

### T2 — `tui-02-curtailment.png` ⚠️ **SAME VOID**
Header `CURTAILMENT EVENTS — LAST 24H` with `₹287,260 TOTAL LOST` pill — correct. `CURTAILMENT EVENTS` table 4 rows (TIME–STATUS, color by status red/orange/dim), `DISPATCH DECISIONS` 4 lines — correct. Same empty void below. No other defects.

### T3 — `tui-03-carbon.png` ⚠️ **SAME VOID**
Header `CARBON CREDIT LEDGER` amber full-width. 3 KPI cards (`CREDITS_ISSUED 32,850`, `_RETIRED 1,200`, `_AVAILABLE 31,650`) — spaced. `CREDIT_BATCHES` table 4 rows (batch_240701 8,212.5 etc) — colors: dates amber, status green/orange. Same void.

### T4 — `tui-04-health.png` ⚠️ **SAME VOID + SCROLLBAR**
Header `ASSET HEALTH SCORES` + `4 ACTIVE ALERTS` orange pill. `ASSET_HEALTH (3-SIGMA)` 11 rows (INV-01 98% → … STR-01 82% ↓ Power drop 18% orange). `ACTIVE_ALERTS` 4 lines (critical red dot, warning yellow dot). The health table's scrollbar is visible (blue thumb + black track) but overlaps the right border. Void below same as other screens.

**Global TUI notes:**
- Amber CRT palette faithfully matches web (`#ffb703` / `#ff5e00` / `#0a0500`) — strong brand consistency.
- Footer `1 Overview 2 Curtailment 3 Carbon 4 Health r Refresh q Quit | ^p palette` consistent.
- Mock fallback works — TUI renders even with API down (uses `_mock_*`).
- All 4 screens functional via key bindings (1/2/3/4).

---

## Issue Registry — Prioritized

| Severity | Where | Issue | Fix |
|----------|-------|-------|-----|
| **CRITICAL** | WEB /assets map | Carto tiles show `API KEY REQUIRED` watermark — map broken for fresh clones | Replace tile URL with `https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png` or free Stadia; document optional `NEXT_PUBLIC_MAPBOX_TOKEN` |
| **CRITICAL** | WEB / overview REVENUE KPI | Value `80,250 ₹/kWh` clipped to `₹/` — font too large for card | `text-3xl → text-2xl xl:text-3xl` + `truncate` or `flex-shrink`, test at 1280w |
| **MODERATE** | WEB /yield | Curtailed table + dispatch log show 3× identical rows (same time/asset/value) | Vary mock data: timestamp `now - delta`, rotate `asset` among `a-1..a-6`, jitter `curtailed/price` |
| **MODERATE** | WEB /health | Scrolling `main` slices KPI row mid-card (hard crop line) | Add `scroll-padding-top` / `pb-8` on main, test `main.scrollTop 300–700` |
| **MODERATE** | TUI all screens | ~35% vertical black void below content (tables/logs don't fill height) | `DataTable { height: 1fr; } RichLog { height: 10; }` in `theme.tcss`, or `Vertical` with `1fr` |
| **MINOR** | WEB /carbon | `REGISTRY TX VCS-2026-08-` truncated | `className="truncate"` + `title` or `break-all text-xs` |
| **MINOR** | WEB chart tooltip | `price : 1.75` vs `mw : 0` lower-case keys | Capitalize to `Price`/`MW` in `Tooltip` formatter |
| **MINOR** | TUI worker log | Extra space before colon `ingest  :` | Trim template `f\"[{now}] ingest: DNI...\"` |
| **MINOR** | Version | Sidebar shows `v1.0.4` everywhere — stale vs current sprint | Bump to `v1.0.5` / inject from `package.json` |

---

## Verdict

- **Sellability:** ✅ Pass — all 7 WEB routes render live data (mock-backed), auth guard + login error states work, pricing overlay fixed (dual axes + price line), tables populated. The two CRITICAL visual bugs (map watermark, REVENUE overflow) are polish blockers for Gumroad screenshots but do not break the demo flow.
- **TUI:** ✅ Functional from terminal with graceful mock fallback. The empty void is a cosmetic layout defect, not a crash.
- **Next actions before tagging `v1.0.0`:** Fix the two CRITICALs + the yield mock duplication + the TUI void, re-capture the 3 affected screenshots, then run `npm run build` + fresh-clone install check.

*Captured 2026-08-27 13:5x IST · Latitude 3460 — mock :8000 + next :3000 · Browser Chrome headless · Textual headless 132×36 · 17 images saved.*
