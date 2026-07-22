# URJA — From Zero to 50MW Solar Farm in 10 Minutes

**Walk through a complete deployment scenario with GreenEnergy Corp's Rajasthan Solar Farm.**

---

This tutorial assumes you've completed the [Quick Start](QUICKSTART.md) — URJA is running on `http://localhost:3000`, seed data is loaded, and you're logged in as `admin@urja.local`.

---

## Scenario

GreenEnergy Corp has just commissioned a **50MW solar farm** in Rajasthan, India. You're the engineer tasked with setting up monitoring, curtailment detection, carbon credit issuance, and predictive maintenance. By the end of this tutorial, GreenEnergy's ops team will have a live control plane — dashboard, API, and terminal UI — running against their actual site data.

---

## Step 1: Deploy URJA *(1 minute)*

If you haven't already:

```bash
docker compose up -d
docker compose exec api alembic upgrade head
docker compose exec api python scripts/seed.py
```

The seed script populates the database with 12 months of realistic generation data for a 50MW solar farm — same scale as GreenEnergy's site. Open `http://localhost:3000` and log in:

```
Email:    admin@urja.local
Password: change-me-on-first-login
```

![Screenshot: URJA login page]

You're greeted by **six KPI cards** at the top — Current MW, Today's MWh, Revenue Today, Curtailment %, CO₂ Avoided, and Active Alerts. Below them, a duck curve chart and a Leaflet asset map.

---

## Step 2: Configure the Solar Farm *(3 minutes)*

The seed data includes a default site. You'll replace it with GreenEnergy's actual farm.

### Create the Site

1. Navigate to **Assets** in the sidebar.
2. Click **Add Site**.
3. Fill in:

| Field | Value |
|---|---|
| **Name** | Rajasthan Solar Farm |
| **Code** | RJ-SOL-01 |
| **Capacity (MW)** | 50 |
| **Latitude** | 27.0238 |
| **Longitude** | 74.2179 |
| **Timezone** | Asia/Kolkata |
| **Currency** | INR |

4. Click **Save**.

The site appears on the Leaflet map with a marker at the Rajasthan coordinates.

### Add Assets

URJA supports batch asset creation. Click **Add Assets → Batch Import** and paste:

```json
[
  {"name": "INV-01", "asset_type": "inverter", "capacity_kw": 5000, "status": "active"},
  {"name": "INV-02", "asset_type": "inverter", "capacity_kw": 5000, "status": "active"},
  {"name": "INV-03", "asset_type": "inverter", "capacity_kw": 5000, "status": "active"},
  {"name": "INV-04", "asset_type": "inverter", "capacity_kw": 5000, "status": "active"},
  {"name": "INV-05", "asset_type": "inverter", "capacity_kw": 5000, "status": "active"},
  {"name": "INV-06", "asset_type": "inverter", "capacity_kw": 5000, "status": "active"},
  {"name": "INV-07", "asset_type": "inverter", "capacity_kw": 5000, "status": "active"},
  {"name": "INV-08", "asset_type": "inverter", "capacity_kw": 5000, "status": "active"},
  {"name": "INV-09", "asset_type": "inverter", "capacity_kw": 5000, "status": "active"},
  {"name": "INV-10", "asset_type": "inverter", "capacity_kw": 5000, "status": "active"}
]
```

Click **Import** — all 10 inverters (5MW each = 50MW total) appear in the asset table. Each is linked to the Rajasthan site with a status of `active`.

For finer-grained monitoring, you can drill deeper — 100,000 solar panels grouped into strings under each inverter — but 10 inverters is enough to start.

---

## Step 3: View Live Generation *(1 minute)*

Navigate to **Dashboard**.

You'll see:

```
┌──────────────────────────────────────────────────────────────┐
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ 32.4 MW  │  │ 245 MWh  │  │ ₹14.2L   │  │ 12.3%    │   │
│  │ Current  │  │ Today    │  │ Revenue  │  │ Curtail  │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│  ┌──────────┐  ┌──────────┐                                │
│  │ 3,450    │  │ 4        │                                │
│  │ Credits  │  │ Alerts   │                                │
│  └──────────┘  └──────────┘                                │
└──────────────────────────────────────────────────────────────┘
```

The **generation curve** below shows a classic duck curve — power ramps up with the morning sun, peaks around noon at ~45MW, then drops toward sunset. The **grid price overlay** (orange line) shows Rajasthan's day-ahead market rates fluctuating between ₹2.5/kWh and ₹6.2/kWh.

![Screenshot: Dashboard with generation curve and duck curve overlay]

This is the view GreenEnergy's operations manager will have on their screen every morning.

---

## Step 4: Detect Curtailment *(2 minutes)*

Navigate to **Yield → Curtailment Events**.

URJA has already detected **3 curtailment events** today from the seed telemetry:

| Time | Duration | Curtailed (MWh) | Grid Price | Revenue Lost |
|---|---|---|---|---|
| 10:15–11:45 | 90 min | 42.5 | ₹2.8/kWh | **₹1,19,000** |
| 13:00–14:30 | 90 min | 38.2 | ₹2.5/kWh | **₹95,500** |
| 16:00–16:45 | 45 min | 15.8 | ₹3.1/kWh | **₹48,980** |

### Revenue Lost Breakdown

Click on the first event. A detail panel opens:

```
Curtailment Event — INV-01 to INV-05
─────────────────────────────────────
Expected generation:    67.5 MWh
Actual generation:      25.0 MWh
Curtailed:              42.5 MWh
Grid price:             ₹2.8/kWh
Revenue lost:           ₹1,19,000

Breakdown:
  INV-01:  ₹23,800 (20.0%)
  INV-02:  ₹23,800 (20.0%)
  INV-03:  ₹23,800 (20.0%)
  INV-04:  ₹23,800 (20.0%)
  INV-05:  ₹23,800 (20.0%)
```

**Total revenue lost today: ₹2,63,480.**

> Notice how the revenue lost calculator uses the actual grid price at the time of curtailment? GreenEnergy can take this number straight to their board meeting to justify battery storage investment.

### Configure a Dispatch Rule

GreenEnergy has a 10MWh battery on site. Let's route excess power there instead of letting it go to waste.

1. Go to **Yield → Dispatch Rules**.
2. Click **Add Rule**.
3. Configure:

| Field | Value |
|---|---|
| **Name** | Route excess to battery when price < ₹2/kWh |
| **Condition** | Grid price below ₹2.0/kWh |
| **Action** | Charge battery at max rate |
| **Priority** | 100 |
| **Cooldown** | 15 minutes |

4. Click **Save**.

URJA will now automatically generate dispatch decisions: when the grid price drops below ₹2/kWh and curtailment is detected, excess generation flows to the battery. Each decision is logged in the dispatch history with expected vs. actual outcome.

---

## Step 5: Issue Carbon Credits *(2 minutes)*

Navigate to **Carbon → Portfolio**.

URJA's carbon module has already calculated the environmental impact from the generation data:

```
Carbon Portfolio — Rajasthan Solar Farm
─────────────────────────────────────────
Total generation this month:  45,000 MWh
Grid emission factor:         0.73 tCO₂e/MWh (India 2026 grid mix)
CO₂ avoided:                  32,850 tCO₂e
Potential credits:            32,850 (at 1 tCO₂e/credit)
Estimated value @ ₹500/credit: ₹1,64,25,000
```

### Issue Credits

1. Click **Issue Credits**.
2. Set the range to cover this month's generation.
3. Select methodology: **IPMVP v2.1** (International Performance Measurement and Verification Protocol).
4. Click **Confirm**.

URJA processes the batch in the background via its ARQ worker. Within seconds:

```json
{
  "batch_id": "batch_rj_202607",
  "total_kwh": 45000000,
  "emission_factor": 0.73,
  "total_co2e": 32850.0,
  "credit_count": 32850,
  "methodology": "IPMVP_v2.1",
  "registry_tx_id": "VCS-2026-07-RJ-001",
  "status": "active"
}
```

Each of the 32,850 credits has a unique ID, a cryptographic audit trail linking it to the specific generation data, and a Verra-compatible registry transaction ID.

> "Notice how the carbon credits are cryptographically linked to generation data? That's the MRV pipeline. Each credit traces back to a specific 15-minute telemetry window — so an auditor at Verra can verify every single credit against the hardware that generated it."

### Export ESG Report

Click **Export Report** → Choose **PDF** → Date range: **This month**.

A professionally formatted report is generated with:

- Executive summary (generation, CO₂ avoided, credits issued)
- Revenue from credit portfolio (at current market price)
- Generation breakdown by asset
- Methodology documentation (IPMVP v2.1)
- Full MRV audit trail with registry transaction IDs

GreenEnergy can send this directly to investors or compliance bodies.

---

## Step 6: Health Monitoring *(1 minute)*

Navigate to **Health → Dashboard**.

URJA's anomaly detection engine (running as a background ARQ task every 15 minutes) has flagged two issues:

```
┌─────────────────────────────────────────────────────────┐
│  Alert                                Severity   Status │
├─────────────────────────────────────────────────────────┤
│  INV-07: Temperature anomaly (78°C)   Critical   Active │
│    Expected: 45°C | z-score: 4.2                         │
│    Recommended: Check inverter cooling fans,             │
│    clean air intake vents.                               │
├─────────────────────────────────────────────────────────┤
│  ST-142: Power drop — 18% below expected  Warning   Active │
│    Expected: 4.8kW | Actual: 3.9kW                       │
│    Recommended: Inspect panels for soiling/shading.      │
└─────────────────────────────────────────────────────────┘
```

### Acknowledge and Create Work Order

1. Click on the **INV-07 temperature anomaly** alert.
2. Click **Acknowledge**.
3. URJA prompts: "Create work order?"
4. Click **Yes**.

A work order is automatically created:

```
Work Order #WO-2026-07-034
────────────────────────────
Asset:      INV-07 (Inverter #7)
Priority:   Critical
Assigned:   Carlos (field technician)
Scheduled:  Today, 14:00–16:00
Description: Temperature at 78°C (z-score 4.2).
             Check cooling fans, clean air intake vents.
Created:    Automatically from alert acknowledge
```

> "See the revenue lost calculator? That's data your operator can act on immediately. The health alerts come with recommended actions — so a field technician who's never seen URJA before knows exactly what to check."

The Health dashboard also shows a **health score grid** — all 10 inverters ranked by score (0–100%). INV-07 is at 62% and dropping (trend: ⬇ declining). INV-03 is at 98% and stable. GreenEnergy's manager can sort, filter, and export this view for weekly reports.

---

## Step 7: Try the TUI *(1 minute)*

URJA ships with a full **terminal UI** powered by Textual. Open a terminal:

```bash
docker compose exec tui python dashboard-tui/app.py
```

Or open `http://localhost:8080` in your browser.

![Screenshot: Textual TUI Overview screen]

You'll see four tabbed screens:

### Overview (default)

```
┌─────────────────────────────────────────────────────────────┐
│  URJA ▸ Rajasthan Solar Farm             Ctrl+C  Ctrl+H  Q │
├─────────────────────────────────────────────────────────────┤
│  MW: 32.4 MW | Today: 245 MWh | Alerts: 4 | Credits: 3,450 │
├─────────────────────────────────────────────────────────────┤
│  Inverter    │ MW     │ Status    │ Curtailment │ Temp      │
│  INV-01      │ 3.2    │ ● Active  │     0.0%    │ 44°C ✓    │
│  INV-02      │ 3.1    │ ● Active  │     0.0%    │ 43°C ✓    │
│  INV-03      │ 4.8    │ ● Active  │     0.0%    │ 41°C ✓    │
│  INV-04      │ 3.3    │ ● Active  │     0.0%    │ 45°C ✓    │
│  INV-05      │ 3.0    │ ● Active  │     0.0%    │ 44°C ✓    │
│  INV-06      │ 3.2    │ ● Active  │     0.0%    │ 46°C ✓    │
│  INV-07      │ 2.8    │ ○ Warning │    18.0%    │ 78°C ⚠    │
│  INV-08      │ 3.4    │ ● Active  │     0.0%    │ 43°C ✓    │
│  INV-09      │ 3.1    │ ● Active  │     0.0%    │ 42°C ✓    │
│  INV-10      │ 3.5    │ ● Active  │     0.0%    │ 44°C ✓    │
└─────────────────────────────────────────────────────────────┘
```

### Keyboard shortcuts

| Key | Screen |
|---|---|
| `Tab` / `→` | Next screen |
| `Ctrl+C` | Carbon credits ledger |
| `Ctrl+H` | Health scores |
| `↑` / `↓` | Navigate rows |
| `Enter` | View detail |
| `Q` | Quit |

### Carbon screen (`Ctrl+C`)

Shows the last 10 credit issuances with registry transaction IDs, CO₂ eq, and status — all live from the API.

### Health screen (`Ctrl+H`)

Lists all assets with health scores, anomaly flags, and a strip of active alerts at the bottom.

> "The TUI gives your ops team the same data without a browser. GreenEnergy's field technician Carlos can pull it up on a laptop in the inverter shed — no internet, just a terminal."

---

## What You've Built

In **10 minutes**, GreenEnergy Corp has:

| Capability | Status |
|---|---|
| 50MW solar farm configured with 10 inverters | ✅ |
| Live generation monitoring with duck curve | ✅ |
| Curtailment detection with ₹2,63,480/day in identified losses | ✅ |
| Dispatch rule routing excess power to battery | ✅ |
| 32,850 carbon credits issued with Verra-compatible audit trail | ✅ |
| Predictive health monitoring with auto-generated work orders | ✅ |
| Terminal UI for on-site ops teams | ✅ |

## The Difference This Makes

Without URJA, GreenEnergy would need:
- A SCADA integration consultant (₹15–25L for 6 months)
- A separate carbon MRV provider (₹5–10L/year)
- A custom dashboard built by a dev agency (₹20–40L)
- A reactive maintenance regime (lost generation from undetected faults)

With URJA, they have it all — deployed in 10 minutes, owned outright, ready to customize.

---

## Next Steps

- **[QUICKSTART.md](QUICKSTART.md)** — Revisit for setup and navigation basics
- **[API-SPEC.md](../technical/API-SPEC.md)** — Integrate SCADA feeds via the telemetry ingestion endpoint
- **[ARCHITECTURE.md](../technical/ARCHITECTURE.md)** — Understand the modular design for customization
- **Tailor it**: Edit `.env` → change the logo, currency, and emission factor under Settings → Branding
- **Scale it**: Add more sites, configure SCADA integration scripts in `/examples/scada-integrations/`

---

<p align="center">
  <sub>URJA — Deploy clean energy intelligence. Own your infrastructure.</sub>
</p>
