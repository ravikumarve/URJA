'use client'

import { useCallback, useEffect, useState } from 'react'
import KpiCard from '@/components/widgets/KpiCard'
import DuckCurveChart from '@/components/charts/DuckCurveChart'
import RadarCanvas from '@/components/widgets/RadarCanvas'
import { Card } from '@/components/ui/card'
import { AlertTriangle, Thermometer, CloudRain, WifiOff, RefreshCw } from 'lucide-react'
import { api, ApiError } from '@/lib/api'
import { fetchTodayDuckCurve, type DuckPoint } from '@/lib/duck-curve'
import type { HealthAlert, PortfolioSummary, TelemetryLatest } from '@/lib/types'

// ---------------------------------------------------------------------------
// Live data orchestration — reference pattern for all module pages:
// parallel fetch → typed state machine (loading | error | ready)
// ---------------------------------------------------------------------------

interface OverviewData {
  telemetry: TelemetryLatest[]
  alerts: HealthAlert[]
  alertTotal: number
  portfolio: PortfolioSummary
  duckCurve: DuckPoint[]
}

type LoadState =
  | { phase: 'loading' }
  | { phase: 'error'; message: string }
  | { phase: 'ready'; data: OverviewData }

const severityColors = {
  critical: 'text-tactical-red',
  warning: 'text-tactical-orange',
  info: 'text-tactical-amber',
} as const

const severityDots = {
  critical: 'bg-tactical-red',
  warning: 'bg-tactical-orange',
  info: 'bg-tactical-amber',
} as const

const severityIcons = {
  critical: AlertTriangle,
  warning: Thermometer,
  info: CloudRain,
} as const

function fmtTime(iso: string): string {
  const d = new Date(iso)
  return Number.isNaN(d.getTime())
    ? '—'
    : d.toLocaleTimeString([], { hour12: false })
}

export default function Dashboard() {
  const [state, setState] = useState<LoadState>({ phase: 'loading' })
  const [reloadTick, setReloadTick] = useState(0)

  const load = useCallback(async () => {
    setState({ phase: 'loading' })
    try {
      const [telemetryRes, alertsRes, portfolio] = await Promise.all([
        api.telemetry.latest(),
        api.health.alerts({ status: 'open', per_page: 20 }),
        api.carbon.portfolio(),
      ])
      const telemetry = telemetryRes.data
      // Duck curve fails soft — chart shows empty state, never kills the page.
      const duckCurve = await fetchTodayDuckCurve(
        telemetry.map((t) => t.asset_id),
      ).catch(() => [])
      setState({
        phase: 'ready',
        data: {
          telemetry,
          alerts: alertsRes.data,
          alertTotal: alertsRes.pagination.total,
          portfolio,
          duckCurve,
        },
      })
    } catch (err) {
      setState({
        phase: 'error',
        message:
          err instanceof ApiError
            ? err.detail
            : 'Failed to load dashboard data.',
      })
    }
  }, [])

  useEffect(() => {
    void load()
  }, [load, reloadTick])

  // ---------------------------------------------------------------------------

  if (state.phase === 'loading') {
    return (
      <div className="flex flex-col gap-4">
        <section className="grid grid-cols-2 gap-3 sm:grid-cols-3 xl:grid-cols-6">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="panel h-[92px] animate-pulse opacity-40" />
          ))}
        </section>
        <section className="grid grid-cols-1 gap-4 lg:grid-cols-3">
          <div className="panel h-[320px] animate-pulse opacity-40 lg:col-span-2" />
          <div className="panel h-[320px] animate-pulse opacity-40" />
        </section>
      </div>
    )
  }

  if (state.phase === 'error') {
    return (
      <div className="panel flex flex-col items-center gap-4 p-10 text-center">
        <AlertTriangle size={28} className="text-tactical-red" />
        <p className="font-data text-sm text-tactical-red">[!] {state.message}</p>
        <button
          onClick={() => setReloadTick((t) => t + 1)}
          className="font-data flex items-center gap-2 rounded border border-border-hard px-4 py-2 text-xs uppercase tracking-wider text-sand-bright transition-colors hover:border-tactical-amber hover:text-tactical-amber"
        >
          <RefreshCw size={13} /> RETRY
        </button>
      </div>
    )
  }

  const { telemetry, alerts, alertTotal, portfolio } = state.data

  // Derived KPIs from live telemetry.
  const totalGenKw = telemetry.reduce((sum, t) => sum + (t.generation_kw ?? 0), 0)
  const totalEnergyKwh = telemetry.reduce((sum, t) => sum + (t.energy_kwh ?? 0), 0)
  const genMw = totalGenKw / 1000
  const yieldMwh = totalEnergyKwh / 1000
  const siteCount = new Set(telemetry.map((t) => t.site_name)).size
  const avgHealth =
    telemetry.length > 0
      ? telemetry.reduce((s, t) => s + (t.health_score ?? 0), 0) / telemetry.length
      : 0
  const lastTs = telemetry.reduce<string | null>(
    (latest, t) => (!latest || t.ts > latest ? t.ts : latest),
    null,
  )

  const kpis = [
    {
      title: 'GEN_MONITOR',
      label: `LIVE GENERATION / ${telemetry.length} ASSETS`,
      value: genMw.toFixed(1),
      unit: 'MW',
      trend: 'neutral' as const,
      alert: genMw <= 0 && telemetry.length > 0,
    },
    {
      title: 'YIELD_MONITOR',
      label: 'LATEST INTERVAL ENERGY',
      value: yieldMwh.toFixed(0),
      unit: 'MWh',
      trend: 'neutral' as const,
    },
    {
      title: 'ALERTS',
      label: 'OPEN ALERTS',
      value: String(alertTotal),
      trend: 'neutral' as const,
      alert: alertTotal > 0,
    },
    {
      title: 'CARBON',
      label: `${portfolio.total_available} AVAILABLE CREDITS`,
      value: portfolio.total_co2e_issued.toLocaleString(),
      unit: 'tCO₂e',
      trend: 'up' as const,
    },
    {
      title: 'SITES',
      label: 'ACTIVE SITES',
      value: String(siteCount),
      unit: '',
      trend: 'neutral' as const,
    },
    {
      title: 'FLEET HEALTH',
      label: 'MEAN HEALTH SCORE',
      value: avgHealth.toFixed(1),
      unit: '/100',
      trend: 'neutral' as const,
      alert: avgHealth > 0 && avgHealth < 60,
    },
  ]

  return (
    <div className="flex flex-col gap-4">
      {/* KPI row — live */}
      <section className="grid grid-cols-2 gap-3 sm:grid-cols-3 xl:grid-cols-6">
        {kpis.map((k) => (
          <KpiCard key={k.title} {...k} />
        ))}
      </section>

      <section className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <Card header="GENERATION CURVE — TODAY (LIVE)" className="lg:col-span-2">
          <DuckCurveChart data={state.data.duckCurve} />
        </Card>

        {/* Active alerts — live */}
        <Card header={`ACTIVE ALERTS${alertTotal > 0 ? ` (${alertTotal})` : ''}`}>
          {alerts.length === 0 ? (
            <p className="font-data py-8 text-center text-xs uppercase tracking-wider text-sand-muted">
              NO OPEN ALERTS — FLEET NOMINAL
            </p>
          ) : (
            <div className="flex flex-col gap-2">
              {alerts.slice(0, 5).map((alert) => {
                const Icon =
                  severityIcons[alert.severity as keyof typeof severityIcons] ??
                  WifiOff
                const color =
                  severityColors[alert.severity as keyof typeof severityColors] ??
                  'text-sand-muted'
                const dot =
                  severityDots[alert.severity as keyof typeof severityDots] ??
                  'bg-sand-muted'
                return (
                  <div
                    key={alert.id}
                    className="flex items-start gap-3 border-b border-surface-light pb-2 last:border-0 last:pb-0"
                  >
                    <span
                      className={`mt-0.5 inline-block h-2 w-2 shrink-0 rounded-full ${dot} animate-blink`}
                    />
                    <Icon size={14} className={`mt-0.5 shrink-0 ${color}`} />
                    <div className="min-w-0 flex-1">
                      <div className="font-data flex items-baseline gap-2 text-[0.65rem] text-sand-muted">
                        <span>{fmtTime(alert.created_at)}</span>
                        <span className="truncate text-tactical-amber">
                          {alert.asset_name ?? 'SYSTEM'}
                        </span>
                      </div>
                      <p className={`font-data mt-0.5 text-xs ${color}`}>
                        {alert.title}
                      </p>
                      {alert.description && (
                        <p className="font-data mt-0.5 truncate text-[0.65rem] text-sand-muted">
                          {alert.description}
                        </p>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </Card>
      </section>

      <RadarCanvas />

      {/* Fleet strip — derived from live telemetry */}
      <section className="grid grid-cols-2 gap-3 sm:grid-cols-3 xl:grid-cols-6">
        {[
          { title: 'ASSETS REPORTING', label: 'LIVE TELEMETRY', value: String(telemetry.length), unit: '' },
          { title: 'TOTAL GENERATION', label: 'SUM OF LATEST READINGS', value: genMw.toFixed(1), unit: 'MW' },
          { title: 'AVG TEMP', label: 'ACROSS FLEET', value: telemetry.length ? (telemetry.reduce((s, t) => s + (t.temperature_c ?? 0), 0) / telemetry.length).toFixed(1) : '—', unit: '°C' },
          { title: 'MIN HEALTH', label: 'WEAKEST ASSET', value: telemetry.length ? String(Math.min(...telemetry.map((t) => t.health_score ?? 0))) : '—', unit: '/100' },
          { title: 'CREDITS RETIRED', label: 'CARBON VAULT', value: String(portfolio.total_retired), unit: '' },
          { title: 'LAST INGEST', label: 'NEWEST READING', value: lastTs ? fmtTime(lastTs) : '—', unit: '' },
        ].map((m) => (
          <div key={m.title} className="panel flex flex-col justify-between p-3">
            <span className="font-data text-[0.6rem] font-bold uppercase tracking-widest text-sand-muted">
              {m.title}
            </span>
            <div className="mt-1 flex items-baseline gap-1">
              <span className="font-data text-xl font-bold text-sand-bright">
                {m.value}
              </span>
              <span className="font-data text-xs text-tactical-amber">{m.unit}</span>
            </div>
            <span className="font-data mt-0.5 text-[0.6rem] uppercase text-sand-muted">
              {m.label}
            </span>
          </div>
        ))}
      </section>
    </div>
  )
}
