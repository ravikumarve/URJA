# URJA — Terminal UI Guide

**Real-time terminal dashboard for renewable energy ops teams.**

Built with [Textual](https://textual.textualize.io). Runs in any terminal — or in a browser. Same data as the web dashboard, zero GUI overhead, built for keyboard-only operation under pressure.

---

## What Is the TUI?

The URJA TUI is a live ops dashboard that polls the URJA API every 5 seconds and displays:

- Live MW generation across all assets
- Curtailment events with revenue lost in real currency
- Carbon credit ledger with issuance history
- Asset health scores with active alerts

No mouse required. No browser tabs. Just a terminal and your keys.

---

## Installation

The TUI runs in the `tui` Docker container — no separate install needed:

```bash
docker compose up -d
```

If running locally without Docker:

```bash
pip install textual rich httpx
```

---

## Launching

### Via Docker (recommended)

```bash
docker compose exec tui python dashboard-tui/app.py
```

### Direct (local Python)

```bash
python dashboard-tui/app.py
```

### Web Mode

Textual can serve the TUI over HTTP — useful when you can't SSH but have a browser:

```bash
docker compose exec tui textual run --dev dashboard-tui/app.py
```

Then open **http://localhost:8080** in any browser. Same UI, same keyboard shortcuts.

> **Note:** Web mode uses Textual's dev server. Data is still live-polled from the API — no configuration needed.

---

## Screens

### 1. Overview Screen (Default)

```
┌──────────────────────────────────────────────────────────────────┐
│  URJA ▸ 50MW Solar Farm                 MW: 32.4  Alerts: 4     │
├──────────────────────────────────────────────────────────────────┤
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │  32.4 MW │ │ 245 MWh  │ │ ₹14.2L   │ │   4      │           │
│  │  Current │ │ Today    │ │ Revenue  │ │  Alerts  │           │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘           │
│  ┌──────────┐ ┌──────────┐                                      │
│  │  3,450   │ │ ₹2.8/kWh│                                      │
│  │  Credits │ │ Grid Pr.│                                      │
│  └──────────┘ └──────────┘                                      │
├──────────────────────────────────────────────────────────────────┤
│  Asset      │ MW    │ Curtail │ Temp   │ Health                 │
│  INV-01     │ 3.2   │   0.0%  │  44°C  │  98% ████████░░       │
│  INV-02     │ 3.1   │   0.0%  │  43°C  │  97% ████████░░       │
│  INV-03     │ 4.8   │   0.0%  │  41°C  │  99% █████████░       │
│  INV-04     │ 3.3   │   0.0%  │  45°C  │  95% █████████░       │
│  INV-05     │ 3.0   │   0.0%  │  44°C  │  96% █████████░       │
│  INV-06     │ 3.2   │   0.0%  │  46°C  │  94% █████████░       │
│  INV-07     │ 2.8   │  18.0%  │  78°C  │  62% ██████░░░░░  ⚠   │
│  INV-08     │ 3.4   │   0.0%  │  43°C  │  97% ████████░░       │
│  INV-09     │ 3.1   │   0.0%  │  42°C  │  98% ████████░░       │
│  INV-10     │ 3.5   │   0.0%  │  44°C  │  96% █████████░       │
└──────────────────────────────────────────────────────────────────┘
```

What you see at a glance:
- **Header bar** — site name, total MW, active alert count
- **KPI row** — Current MW, MWh today, revenue today, alerts, carbon credits, grid price
- **Asset table** — every inverter/turbine with live MW, curtailment %, temperature, health score bar
- **Auto-refresh** — every 5 seconds

![Screenshot: Overview screen with KPI cards and asset table]

### 2. Curtailment Screen

```
┌──────────────────────────────────────────────────────────────────┐
│  Curtailment Events — Last 24 Hours                  Total Lost │
│                                                      ₹2,63,480  │
├──────────────────────────────────────────────────────────────────┤
│  Time          │ Duration  │ Curtailed │ Price │ Revenue Lost   │
│  10:15–11:45   │   90 min  │  42.5 MWh │ ₹2.8  │ ₹1,19,000  🔴  │
│  13:00–14:30   │   90 min  │  38.2 MWh │ ₹2.5  │ ₹95,500   🔴  │
│  16:00–16:45   │   45 min  │  15.8 MWh │ ₹3.1  │ ₹48,980   🟡  │
├──────────────────────────────────────────────────────────────────┤
│  Recent Dispatch Decisions                                       │
│  14:30  Charged battery (12.4 MW → 78% SOC)                     │
│  14:32  Curtailment resolved — grid price recovered              │
└──────────────────────────────────────────────────────────────────┘
```

Color coding:
- **🔴 Red** — Active curtailment (ongoing revenue loss)
- **🟡 Yellow** — Resolved within last hour
- **Faded** — Historical (past hour or older)

The bottom panel shows the dispatch decision log — every time a rule fired (battery charging, compute load routing, etc.).

### 3. Carbon Screen

```
┌──────────────────────────────────────────────────────────────────┐
│  Carbon Credit Ledger                                           │
│  Total Issued: 32,850  │  Retired: 1,200  │  Available: 31,650 │
├──────────────────────────────────────────────────────────────────┤
│  Batch ID      │ Date       │ CO₂e    │ Credits │ Status        │
│  batch_240701  │ 2026-07-01 │ 8,212.5 │  8,212  │ active        │
│  batch_240702  │ 2026-07-08 │ 8,150.0 │  8,150  │ active        │
│  batch_240703  │ 2026-07-15 │ 8,300.0 │  8,300  │ active        │
│  batch_240704  │ 2026-07-22 │ 8,188.0 │  8,188  │ pending       │
└──────────────────────────────────────────────────────────────────┘
```

Shows the last N credit issuances with methodology version, CO₂ equivalent, and registry transaction ID. Each batch links back to the generation data window that produced it.

### 4. Health Screen

```
┌──────────────────────────────────────────────────────────────────┐
│  Asset Health Scores                             4 Active Alerts │
├──────────────────────────────────────────────────────────────────┤
│  Asset      │ Score   │ Trend │ Anomalies                       │
│  INV-01     │  98%    │  →    │ None                            │
│  INV-02     │  97%    │  →    │ None                            │
│  INV-03     │  99%    │  →    │ None                            │
│  INV-04     │  95%    │  →    │ None                            │
│  INV-05     │  96%    │  →    │ None                            │
│  INV-06     │  94%    │  →    │ None                            │
│  INV-07     │  62%    │  ↓    │ Temp 78°C (z=4.2) ⚠            │
│  INV-08     │  97%    │  →    │ None                            │
│  INV-09     │  98%    │  →    │ None                            │
│  INV-10     │  96%    │  →    │ None                            │
├──────────────────────────────────────────────────────────────────┤
│  Active Alerts                                                  │
│  🔴 INV-07: Temperature anomaly (78°C) — Check fans            │
│  🟡 ST-142: Power drop 18% below expected — Check panels       │
└──────────────────────────────────────────────────────────────────┘
```

Health score thresholds:
- **🟢 80–100%** — Healthy (green)
- **🟡 50–79%** — Warning (yellow)
- **🔴 0–49%** — Critical (red)

---

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `1` | Overview screen |
| `2` | Curtailment screen |
| `3` | Carbon screen |
| `4` | Health screen |
| `Tab` / `→` | Next screen |
| `↑` `↓` | Navigate rows |
| `Enter` | View detail panel |
| `r` | Refresh now |
| `?` | Show help overlay |
| `q` | Quit |
| `Ctrl+C` | Quit |

---

## Theming

The TUI automatically detects your terminal's light/dark color scheme and adjusts accordingly.

- **Dark terminal** → Dark theme (default for most ops terminals)
- **Light terminal** → Light theme
- No manual theme switch required.

To force a specific scheme, set your terminal theme before launching:

```bash
# Most terminals: set profile to light/dark
# The TUI reads the COLORFGBG environment variable
```

---

## Tips for Ops Teams

### 24/7 Monitoring in tmux

Keep the TUI running in a persistent tmux session:

```bash
tmux new -s urja-tui
docker compose exec tui python dashboard-tui/app.py
# Detach: Ctrl+B, D
# Reattach: tmux attach -t urja-tui
```

Same for `screen`:

```bash
screen -S urja-tui
docker compose exec tui python dashboard-tui/app.py
# Detach: Ctrl+A, D
# Reattach: screen -r urja-tui
```

### Desktop Notifications on Alerts

Pipe alert counts to a notification daemon:

```bash
# Every 60 seconds, check alert count via API
watch -n 60 'curl -s http://localhost:8000/api/v1/health/alerts?status=active | \
  python -c "import sys,json; d=json.load(sys.stdin); print(f\"{len(d)} active alerts\")" \
  | xargs -I{} notify-send "URJA" "{}"'
```

### Combine with `watch` for Custom Views

Need a specific data slice not shown in the TUI? Pipe the API directly:

```bash
watch -n 10 'curl -s http://localhost:8000/api/v1/dispatch/revenue-lost | \
  python -m json.tool | grep -E "total_lost|currency"'
```

### TUI in Web Mode as a Status Screen

Set up a dedicated monitor displaying the TUI in web mode at `http://localhost:8080` — full-screen in a kiosk browser. No SSH needed for walk-up viewing.

### Docker Restart Policy

The `tui` container restarts automatically with `docker compose restart`. If the TUI process crashes, Docker brings it back.

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| TUI shows "Connection refused" | Ensure `docker compose up -d` completed and API is healthy |
| TUI shows empty tables | Seed data missing — run `docker compose exec api python scripts/seed.py` |
| Web mode blank page | Port 8080 not exposed — check `docker compose ps` |
| TUI crashes on startup | Run `pip install textual rich httpx` in the container |
| Data not refreshing | Check `URJA_API_URL` and `URJA_POLL_INTERVAL` in `docker/tui.env` |

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `URJA_API_URL` | `http://api:8000/api/v1` | API base URL |
| `URJA_POLL_INTERVAL` | `5` | Refresh interval in seconds |
| `URJA_THEME` | `auto` | `auto`, `dark`, or `light` |

---

## Architecture

```
┌─────────────────┐     GET /api/v1/telemetry/latest
│   TUI (Textual) │────► GET /api/v1/dispatch/curtailment
│                 │────► GET /api/v1/carbon/credits?limit=10
│  :8080 / tty    │────► GET /api/v1/health/scores
└────────┬────────┘     GET /api/v1/health/alerts?status=active
         │
         │ polls every N seconds (default: 5)
         ▼
┌─────────────────┐
│   API (FastAPI) │───► PostgreSQL + TimescaleDB
└─────────────────┘
```

The TUI has no direct database access. It polls the same REST API the web dashboard uses. This means:
- No extra DB connections from the TUI
- The API cache layer (Redis) reduces load on repeated polls
- TLS and auth apply the same way as the web dashboard

---

*URJA — Deploy clean energy intelligence. Own your infrastructure.*
