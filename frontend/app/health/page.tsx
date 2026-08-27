'use client'

import { useCallback } from 'react'
import KpiCard from '@/components/widgets/KpiCard'
import { Card } from '@/components/ui/card'
import { EmptyState, ErrorPanel, SkeletonPanels, SkeletonRows } from '@/components/widgets/states'
import { api } from '@/lib/api'
import type { HealthAlert, HealthScore } from '@/lib/types'
import { useApiData } from '@/lib/use-api-data'
import { cn } from '@/lib/utils'

interface HealthData {
  scores: HealthScore[]
  alerts: HealthAlert[]
  alertTotal: number
}

const severityColors = {
  critical: 'text-tactical-red',
  warning: 'text-tactical-orange',
  info: 'text-sand-muted',
} as const

const severityDots = {
  critical: 'bg-tactical-red',
  warning: 'bg-tactical-amber',
  info: 'bg-sand-muted',
} as const

function fmtTime(iso: string): string {
  const d = new Date(iso)
  return Number.isNaN(d.getTime()) ? '—' : d.toLocaleTimeString([], { hour12: false })
}

export default function Health() {
  const fetcher = useCallback(async (): Promise<HealthData> => {
    const [scoresRes, alertsRes] = await Promise.all([
      api.health.scores(),
      api.health.alerts({ status: 'open', per_page: 20 }),
    ])
    return {
      scores: scoresRes.data,
      alerts: alertsRes.data,
      alertTotal: alertsRes.pagination.total,
    }
  }, [])

  const { state, reload } = useApiData(fetcher)

  if (state.phase === 'loading') {
    return (
      <div className="flex flex-col gap-4">
        <SkeletonPanels />
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          <div className="panel h-[320px] animate-pulse opacity-40" />
          <div className="panel h-[320px] animate-pulse opacity-40" />
        </div>
      </div>
    )
  }

  if (state.phase === 'error') {
    return <ErrorPanel message={state.message} onRetry={reload} />
  }

  const { scores, alerts, alertTotal } = state.data

  const criticalCount = alerts.filter((a) => a.severity === 'critical').length
  const warningCount = alerts.filter((a) => a.severity === 'warning').length
  const avgHealth =
    scores.length > 0
      ? scores.reduce((s, h) => s + h.health_score, 0) / scores.length
      : 0

  return (
    <div className="flex flex-col gap-4 pb-6">
      <h1 className="font-ui text-lg font-bold uppercase tracking-wider text-sand-bright">
        ASSET HEALTH
      </h1>

      <section className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <KpiCard
          title="ACTIVE_ALERTS"
          label="OPEN ALERTS"
          value={String(alertTotal)}
          alert={alertTotal > 0}
          trend="neutral"
        />
        <KpiCard
          title="AVG_HEALTH"
          label={`ACROSS ${scores.length} ASSETS`}
          value={avgHealth.toFixed(0)}
          unit="/100"
          trend="neutral"
        />
        <KpiCard
          title="CRITICAL"
          label="CRITICAL ALERTS"
          value={String(criticalCount)}
          alert={criticalCount > 0}
          trend="neutral"
        />
        <KpiCard
          title="WARNINGS"
          label="WARNING ALERTS"
          value={String(warningCount)}
          trend="neutral"
        />
      </section>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card header={`HEALTH SCORES (${scores.length})`}>
          {scores.length === 0 ? (
            <EmptyState label="NO HEALTH METRICS — RUN THE HEALTH_SCAN WORKER" />
          ) : (
            <div className="max-h-[420px] overflow-y-auto">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Asset</th>
                    <th>Score</th>
                    <th>Anomaly</th>
                    <th>Flags</th>
                  </tr>
                </thead>
                <tbody>
                  {scores.map((h) => (
                    <tr key={h.asset_id}>
                      <td className="font-bold text-tactical-amber">{h.asset_name}</td>
                      <td>
                        <span
                          className={cn(
                            'font-bold',
                            h.health_score >= 80 && 'text-tactical-green',
                            h.health_score >= 50 &&
                              h.health_score < 80 &&
                              'text-tactical-amber',
                            h.health_score < 50 && 'text-tactical-red',
                          )}
                        >
                          {h.health_score.toFixed(0)}%
                        </span>
                      </td>
                      <td
                        className={cn(
                          h.anomaly_score > 0.5 && 'text-tactical-red',
                          h.anomaly_score <= 0.5 && 'text-sand-muted',
                        )}
                      >
                        {(h.anomaly_score * 100).toFixed(0)}%
                      </td>
                      <td
                        className={cn(
                          h.anomaly_flags.length > 5 && 'text-tactical-red',
                          h.anomaly_flags.length === 0 && 'text-tactical-green',
                        )}
                      >
                        {h.anomaly_flags.length}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>

        <Card header={`ACTIVE ALERTS (${alertTotal})`}>
          {alerts.length === 0 ? (
            <EmptyState label="NO OPEN ALERTS — FLEET NOMINAL" />
          ) : (
            <div className="flex max-h-[420px] flex-col gap-2 overflow-y-auto">
              {alerts.map((alert) => (
                <div
                  key={alert.id}
                  className="flex items-start gap-3 border-b border-surface-light pb-2 last:border-0 last:pb-0"
                >
                  <span
                    className={cn(
                      'mt-1.5 inline-block h-2 w-2 shrink-0 rounded-full animate-blink',
                      severityDots[alert.severity as keyof typeof severityDots] ??
                        'bg-sand-muted',
                    )}
                  />
                  <div className="min-w-0 flex-1">
                    <div className="font-data flex items-baseline gap-2 text-[0.65rem] text-sand-muted">
                      <span
                        className={cn(
                          'font-bold uppercase',
                          severityColors[alert.severity as keyof typeof severityColors] ??
                            'text-sand-muted',
                        )}
                      >
                        {alert.severity.toUpperCase()}
                      </span>
                      <span>{fmtTime(alert.created_at)}</span>
                      <span className="truncate text-tactical-amber">
                        {alert.asset_name ?? 'SYSTEM'}
                      </span>
                    </div>
                    <p className="font-data mt-0.5 text-xs text-sand-bright">
                      {alert.title}
                    </p>
                    {alert.description && (
                      <p className="font-data mt-0.5 text-[0.65rem] text-sand-muted">
                        {alert.description}
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>

      <Card header="ALERT FEED — MOST RECENT FIRST" className="mb-2">
        {alerts.length === 0 ? (
          <EmptyState label="FEED EMPTY" />
        ) : (
          <div className="flex max-h-[300px] flex-col gap-1.5 overflow-y-auto">
            {alerts.map((alert) => (
              <div
                key={`feed-${alert.id}`}
                className="flex items-start gap-3 border-b border-surface-light pb-1.5 last:border-0 last:pb-0"
              >
                <span
                  className={cn(
                    'mt-1 inline-block h-2 w-2 shrink-0 rounded-full',
                    severityDots[alert.severity as keyof typeof severityDots] ??
                      'bg-sand-muted',
                  )}
                />
                <div className="font-data flex-1 text-xs">
                  <span className="text-sand-muted">{fmtTime(alert.created_at)}</span>
                  <span className="mx-2 text-sand-muted">|</span>
                  <span className="text-tactical-amber">{alert.asset_name ?? 'SYSTEM'}</span>
                  <span className="mx-2 text-sand-muted">|</span>
                  <span
                    className={
                      severityColors[alert.severity as keyof typeof severityColors] ??
                      'text-sand-muted'
                    }
                  >
                    {alert.title}
                    {alert.site_name ? ` — ${alert.site_name}` : ''}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  )
}
