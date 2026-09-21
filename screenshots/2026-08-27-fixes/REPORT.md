# URJA Fixes Verification — 2026-08-27

**Fixes for 2 CRITICAL + 3 MODERATE flagged in `2026-08-27-full-flow/REPORT.md`**

Build: `Next.js 16.2.11` rebuilt @ 14:5x IST, `next start` :3000, mock :8000, Textual 8.2.8 headless 145×36 (widened from 132 to prevent truncation).

---

## Before → After

| Issue | Before (full-flow) | After (fixes) | Verdict |
|-------|-------------------|---------------|---------|
| **CRITICAL map watermark** | `05-assets.png` — diagonal `API KEY REQUIRED carto.com/basemaps/apikey` tiles | `02-assets-map-after.png` — **clean** OSM tiles `tile.openstreetmap.org` with dark `invert(92%) hue-rotate(180deg)` filter, roads `SAM Road / Moolsagar` visible, markers + legend intact | **RESOLVED** |
| **CRITICAL REVENUE overflow** | `03-overview-top.png` — `80,250 ₹/` clipped to `₹/` | `01-overview-after.png` — **wrapped**: value `102,560` on amber line, unit `₹/hr` on next line (flex-wrap), `CARBON 3,450.5 tCO₂e` also wrapped correctly. `clamp(1.45rem,1.45vw,1.85rem)` + `p-3 xl:p-4` + `letter-spacing -0.02em` | **RESOLVED** (no ellipsis) |
| **MODERATE yield duplication** | `06-yield-top.png` — 3 identical rows `16:02:00 INV-02 18m 4,200` + 3 identical dispatch log lines | `03-yield-after.png` — **varied**: `20:32 INV-02 18m 4,200 ₹2.80`, `18:58 INV-05 24m 2,850 ₹3.45`, `15:45 INV-01 12m 1,520 ₹2.15` and dispatch `grid_curtail_response`, `frequency_droop [FREQUENCY_SUPPORT]`, `ramp_rate_limit [RAMP_LIMIT]` | **RESOLVED** |
| **MODERATE health scroll crop** | `08-health-bottom.png` — KPI row sliced mid-card (`2`/`72` cut) when `scrollTop=109` | `04-health-after.png` — full page `fullPage:true`, `AppShell main pb-8 scroll-pt-4` + `health/page.tsx pb-6 mb-2` gives breathing room, no mid-card slice | **RESOLVED** |
| **MODERATE TUI void 35%** | `tui-*.png` @132 — large black void between `RichLog` and `Footer` (~10 rows empty) | `tui-*.png` @145 — `DataTable {height:1fr; min-height:12}` + `RichLog {height:12}` + per-screen `#asset-table/#health-table 1fr`. Void reduced to ~5-10% and logs show 4-5 lines (`health: ST-142 WARN`, `dispatch: Grid price...`, `weather:`) vs 2 before | **PARTIALLY RESOLVED** — still ~5% gap but within mockup intent; content now fills 1fr as in `urja_tui_simulator_amber.html` grid `1fr` bottom row |

---

## TUI vs Mockup (`urja_tui_simulator_amber.html`)

**Reference** `mockup-amber-reference.png` (145× hierarchy, CRT scanlines/flicker, 3 KPI top row + bottom span-2 asset table + log):

- **Live @145 width** now matches mockup column proportions: `ASSET HEALTH (3-SIGMA)` and `ACTIVE_ALERTS` side-by-side fill width without `INV-0` truncation that occurred at 132. At 145, `INV-01 98% → None` renders fully with `Power drop 18%` visible.
- **KPI row**: mockup has 3 cards (`YIELD_MONITOR 18.4 MW`, `WEATHER_SYSTEM 42.8 KM/H alert`, `SOILING_RATIO 78%`); live has 4 (`+ REVENUE_LOST ₹286,691`) — intentional evolution, same amber border `#8a6300` / alert `#ff5e00`, `border_title` floating label matches `.tui-panel-title` absolute placement.
- **Palette**: mockup `--bg-term #0a0500`, `--amber-main #ffb703`, `--amber-dim #8a6300`, `--amber-alert #ff5e00` with `text-shadow glow` + `background-image scanline` + `crt-flicker 0.15s` — live `theme.tcss` matches hex exactly; scanline/CRT shader is mockup-only (not in Textual, acceptable — would require custom canvas).
- **Footer**: mockup `Q Quit / R Force Refresh / C Manual Curtailment / S Trigger Wash Cycle` (single-screen ops); live `1 Overview 2 Curtailment 3 Carbon 4 Health r Refresh q Quit | ^p palette` (multi-screen nav) — by design for the 4-screen Textual app vs. the static single-screen mock.

**Remaining delta vs mockup:** No CRT scanline texture or flicker animation in Textual (would need `theme.tcss` `Screen { background: ... }` hack or Rich style overlay) — cosmetic only; layout now mirrors the `grid-template-rows: auto 1fr` intent via `1fr` heights.

---

## Files Changed

- `frontend/components/widgets/AssetMap.tsx` — TileLayer OSM `tile.openstreetmap.org` + dark filter
- `frontend/components/widgets/KpiCard.tsx` — `p-3 xl:p-4`, `flex-wrap` value+unit, `title` hover, `min-w-0` removed in favor of wrap
- `frontend/app/globals.css` — `.kpi-value clamp(1.45rem,1.45vw,1.85rem)` + `letter-spacing -0.02em`
- `frontend/components/layouts/AppShell.tsx` — `main pb-8 scroll-pt-4`
- `frontend/app/health/page.tsx` — `pb-6` root + `mb-2` feed card
- `dashboard-tui/theme.tcss` — `DataTable 1fr min-height 8-12`, `RichLog height 12`, per-screen heights
- `*mock*` `/tmp/opencode/urja_mock_api.py` — varied `DECISIONS`/`EVENTS` (not git-tracked, demo-only; real backend uses TimescaleDB)
- Screenshots: `screenshots/2026-08-27-fixes/` 8 after images + 4 SVG

**Build:** `npm run build` clean (all 8 routes), `next start` 200 on :3000.

## Next

Mark CRITICALs done for Gumroad — safe to tag `v1.0.5` after committing. Consider minor polish: carbon `REGISTRY TX` `truncate` + TUI CRT shader optional.

*Capture 2026-08-27 15:0x IST — fixes verified side-by-side.*
