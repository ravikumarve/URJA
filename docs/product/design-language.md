# URJA Design Language — "Arid Tactical" / Industrial SCADA

> **Design DNA**: Military-grade SCADA meets desert solar farm. Tactical-orange is the soul. JetBrains Mono carries every number. Borders are always 2px. Panels have hardware-like depth. Ambient particle animations communicate the harsh-environment narrative. The TUI strips away all non-terminal chrome and keeps only amber glow and keyboard-driven interaction.

**Source prototypes:**
- `urja_landing_page_arid_tactical.html` — Landing / Gumroad sales page
- `urja_tactical_dashboard.html` — Browser-based ops dashboard
- `urja_tui_simulator_amber.html` — Terminal TUI (Textual) mockup

---

## 1. Typography

### Font Stack

| Font | Role | Weight Used | Source |
|---|---|---|---|
| **Chakra Petch** | UI / headings / navigation | 400, 500, 600, 700 | Google Fonts |
| **JetBrains Mono** | All data / metrics / logs / tables / tags / badges | 400, 700, 800 | Google Fonts |
| System sans-serif | Body copy / paragraphs | 400 | Fallback |

### Size Ladder

| Level | Size | Weight | Context |
|---|---|---|---|
| Hero H1 | `clamp(3rem, 5vw, 4.5rem)` | 700 | Landing hero |
| Section H2 | `3rem` | 700 | Section titles |
| Card H3 | `1.8rem` | 700 | Bento card titles |
| Panel Header | `0.85rem` | 600 | Dashboard panel titles |
| KPI Value (dash) | `2.2rem` | 800 | Dashboard metrics |
| KPI Value (TUI) | `32px` | 800 | TUI panel metrics |
| Tags / Labels | `0.75rem` | 400/700 | Hero badges, card tags, status text |
| Table cells | `0.75rem` / `12px` | 400 | All data tables |
| Body copy | `1.1rem` | 400 | Paragraph text |

### Typography Rules
- All headings are `text-transform: uppercase`
- Body text uses system `sans-serif` (not Chakra Petch) for readability at small sizes
- JetBrains Mono = the *data voice* — any number, metric, log, or status
- Chakra Petch = the *system voice* — navigation chrome, headers, UI labels
- `letter-spacing: 2px` on brand wordmark
- `letter-spacing: 1px` on panel headers
- Font rendering: `-webkit-font-smoothing: antialiased`

---

## 2. Color Palette

### Base — "Arid Tactical" (Landing + Dashboard)

| Token | Hex | Usage |
|---|---|---|
| `--void` | `#090807` | Deepest background, page body, canvas layers |
| `--surface-dark` | `#12100e` | Card backgrounds, secondary surfaces |
| `--surface-mid` | `#1c1a17` | Panel body backgrounds |
| `--surface-light` | `#2c2723` | Panel headers, hover states, border accents |
| `--sand-muted` | `#8c7b6b` | Secondary text, muted labels, decorative borders |
| `--sand-bright` | `#d9cdbd` | Primary text color (off-white desert sand) |
| `--tactical-orange` | `#ff5e00` | **Primary action** — CTAs, warnings, interactive hover, crosshair |
| `--tactical-amber` | `#ffb703` | **Secondary accent** — brand mark, active states, OK status |
| `--tactical-green` | `#4ade80` | Success / nominal status |
| `--tactical-red` | `#ef4444` | Critical alarms, errors |
| `--border-hard` | `#3a332d` | All borders — **always 2px** |
| `--grid-line` | `rgba(217, 205, 189, 0.1)` | Dashboard grid background |

### Amber Terminal (TUI)

| Token | Hex | Usage |
|---|---|---|
| `--bg-term` | `#0a0500` | Terminal background (deeper than void) |
| `--amber-main` | `#ffb703` | Primary text, borders, glows |
| `--amber-dim` | `#8a6300` | Muted text, dashed borders |
| `--amber-alert` | `#ff5e00` | Critical alerts (same as tactical-orange) |

### Color Semantics (All Pages)
- **Orange** (`--tactical-orange`) = WARNING, ACTION, INTERACTIVE STATE
- **Amber** (`--tactical-amber`) = OK, NOMINAL, BRAND MARK
- **Green** (`--tactical-green`) = SUCCESS, HEALTHY
- **Red** (`--tactical-red`) = CRITICAL, ERROR
- Sand-bright on void/surface-dark = primary readability

---

## 3. Layout Systems

### Landing Page
- Constraint: `max-width: 1200px` centered container
- Section padding: `8rem` vertical with `2px solid --border-hard` bottom separators
- Hero: `85vh` min-height, `1fr 1fr` grid
- Bento grid: 12-column CSS Grid, cards span `col-8 / col-6 / col-4`
- Infra stack: `1fr 1fr` grid
- Breakpoint: `1024px` — all grids collapse to single column

### Dashboard
- Full viewport (`100vw x 100vh`), `overflow: hidden`
- Top bar: `50px` fixed, brand left, sys-status right
- Workspace: `[280px, 1fr, 350px]` columns × `1fr 1fr` rows
  - Left: Command navigation (full height)
  - Center: Radar/map (spans both rows)
  - Right top: Live metrics
  - Right bottom: Event log table
- No scrolling — everything fits viewport
- Background: repeating `30px × 30px` tactical grid at `--grid-line`

### TUI Simulator
- Full viewport terminal window
- Header: `12px` bold, amber-on-black
- Main grid: `1fr 1fr 1fr` × `auto 1fr`
  - Row 1: 3 KPI panels (Yield, Weather, Soiling)
  - Row 2: Asset diagnostics (span 2) + ARQ worker log
- Footer: Hotkey bar

---

## 4. Component Patterns

### Buttons
- Font: JetBrains Mono, `0.85rem`, 700 weight, uppercase
- Padding: `0.8rem 2rem`
- Border: `2px solid`
- Transition: `all 0.2s`

| Variant | Background | Border | Text | Hover |
|---|---|---|---|---|
| Primary | `--tactical-orange` | transparent | `--void` | transparent bg, orange border, orange text |
| Outline | `--surface-dark` | `--border-hard` | `--sand-bright` | `--surface-mid` bg, `--sand-muted` border |

### Panel / Card
- **Landing bento**: `--surface-dark` bg, `2px --border-hard`, 3rem padding, hover lifts border to orange
- **Dashboard panels**: `--surface-mid` bg, `1px --surface-light`, `inset 0 0 20px rgba(0,0,0,0.5)`, **hardware corner brackets** (::before/::after 8px L-shaped)
- **Dashboard panel header**: `--surface-light` bg, `0.85rem` uppercase, `letter-spacing: 1px`
- **TUI panels**: `1px --amber-dim`, **floating title badge** (absolute positioned -9px top), alert panels glow amber-alert

### Tables
- Font: JetBrains Mono throughout
- Headers: `--sand-muted` color, bottom border `1px dashed --amber-dim` (TUI)
- Status classes: `txt-err`/`fg-alert` (red), `txt-warn` (orange), `txt-ok` (green)
- Font size: `0.75rem` (dashboard), `12px` (TUI)

### Navigation
- Landing: Horizontal links, JetBrains Mono, `0.9rem`, uppercase, `--sand-muted` → orange on hover
- Dashboard sidebar: Vertical stacked, `0.8rem`, active state amber left-border

---

## 5. Visual Effects

| Effect | Technique | Used In |
|---|---|---|
| **Dust storm particles** | Canvas 400 particles, horizontal vel 2-8, sand-colored | Landing bg |
| **Sun glare** | `radial-gradient` 40vw circle, `--tactical-amber` 15%, `blur(60px)` | Landing fixed top-right |
| **Custom crosshair cursor** | `div::before/after` 24px cross in tactical-orange | Landing |
| **Tactical grid** | Repeating `30px` 1px lines at `--grid-line` | Dashboard bg |
| **Radar sweep** | Canvas rotating line + gradient wedge + concentric rings | Dashboard center |
| **CRT scanlines** | `repeating-linear-gradient` `100% 4px` | TUI |
| **CRT flicker** | `@keyframes` `0.15s` opacity cycling `0.95→1→0.98` | TUI |
| **Amber glow** | Multi-layer `text-shadow` + `box-shadow` | TUI |
| **Blinking alerts** | `@keyframes blink` 50% opacity 0 | Dashboard + TUI |
| **Hardware corners** | `::before/::after` 8px L-brackets | Dashboard panels |
| **Depth shadow** | `inset 0 0 20px rgba(0,0,0,0.5)` | Dashboard panels |

---

## 6. Tailwind v4 Theme Configuration

```css
@theme {
  --color-void: #090807;
  --color-surface-dark: #12100e;
  --color-surface-mid: #1c1a17;
  --color-surface-light: #2c2723;
  --color-sand-muted: #8c7b6b;
  --color-sand-bright: #d9cdbd;
  --color-tactical-orange: #ff5e00;
  --color-tactical-amber: #ffb703;
  --color-tactical-green: #4ade80;
  --color-tactical-red: #ef4444;
  --color-border-hard: #3a332d;
  --font-ui: 'Chakra Petch', sans-serif;
  --font-data: 'JetBrains Mono', monospace;
}
```

### CSS Rules That Must Be Replicated Everywhere
```css
/* Bold 2px borders as default separator */
border: 2px solid var(--border-hard);

/* Panel depth */
box-shadow: inset 0 0 20px rgba(0,0,0,0.5);

/* Subtle amber glow on light text */
text-shadow: 0 0 1px rgba(255, 183, 3, 0.2);

/* All headings uppercase + letter-spacing */
text-transform: uppercase;
letter-spacing: 1px;
```

---

## 7. Adaptation Map to URJA Stack

| Source HTML | Target URJA Component | Key Elements to Port |
|---|---|---|
| Landing page → | Gumroad sales page | Dust canvas, sun glare, crosshair cursor, terminal mockup, bento grid, stack list |
| Dashboard → | `app/frontend/dashboard/` | Color tokens, typography, KPI cards, radar canvas, panel layout, hardware corners, tactical grid bg |
| TUI Simulator → | `backend/dashboard-tui/` | Amber palette, CRT effects, panel title badges, hotkey footer, blinking alerts |
