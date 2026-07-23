'use client'

import KpiCard from '@/components/widgets/KpiCard'
import { Card } from '@/components/ui/card'
import { cn } from '@/lib/utils'

interface HealthScore {
  asset: string
  score: number
  trend: 'up' | 'stable' | 'down'
  anomalies: number
}

interface ActiveAlert {
  severity: 'critical' | 'warning'
  asset: string
  message: string
}

interface AlertLog {
  time: string
  asset: string
  event: string
  severity: 'critical' | 'warning' | 'info'
}

const healthScores: HealthScore[] = [
  { asset: 'INV-01', score: 94, trend: 'stable', anomalies: 0 },
  { asset: 'INV-02', score: 87, trend: 'up', anomalies: 1 },
  { asset: 'INV-03', score: 52, trend: 'down', anomalies: 7 },
  { asset: 'INV-04', score: 76, trend: 'stable', anomalies: 2 },
  { asset: 'INV-05', score: 33, trend: 'down', anomalies: 12 },
  { asset: 'INV-06', score: 91, trend: 'up', anomalies: 0 },
  { asset: 'INV-07', score: 45, trend: 'down', anomalies: 9 },
  { asset: 'INV-08', score: 68, trend: 'stable', anomalies: 3 },
  { asset: 'INV-09', score: 73, trend: 'up', anomalies: 1 },
  { asset: 'INV-10', score: 88, trend: 'stable', anomalies: 0 },
  { asset: 'BAT-01', score: 81, trend: 'down', anomalies: 2 },
  { asset: 'TRF-01', score: 92, trend: 'stable', anomalies: 0 },
]

const activeAlerts: ActiveAlert[] = [
  { severity: 'critical', asset: 'INV-05', message: 'Inverter offline — no communication for 47m' },
  { severity: 'critical', asset: 'INV-07', message: 'DC arc fault detected — maintenance required' },
  { severity: 'warning', asset: 'INV-03', message: 'Temperature exceeding threshold (52°C)' },
  { severity: 'warning', asset: 'BAT-01', message: 'Cell voltage imbalance — deviation 0.14V' },
  { severity: 'warning', asset: 'INV-08', message: 'Efficiency drop below 80% threshold' },
]

const alertLogs: AlertLog[] = [
  { time: '17:42:11', asset: 'INV-05', event: 'COMMS_LOST — SCADA heartbeat timeout', severity: 'critical' },
  { time: '17:22:08', asset: 'INV-07', event: 'ARC_FAULT — DC arc detected on string 4', severity: 'critical' },
  { time: '16:54:30', asset: 'INV-03', event: 'TEMP_HIGH — IGBT temp 52°C, derating to 80%', severity: 'warning' },
  { time: '16:12:44', asset: 'BAT-01', event: 'CELL_IMBALANCE — BMS reported 0.14V deviation', severity: 'warning' },
  { time: '15:38:22', asset: 'INV-08', event: 'EFFICIENCY_LOW — PR dropped to 78%', severity: 'warning' },
  { time: '14:55:01', asset: 'INV-02', event: 'SOILING_ALERT — Soiling ratio 78%', severity: 'warning' },
  { time: '14:02:11', asset: 'WEATHER', event: 'STORM_WARNING — Dust storm approaching', severity: 'critical' },
  { time: '13:45:00', asset: 'COMMS', event: 'SCADA_LINK_FLAP — Microwave instability', severity: 'info' },
]

const scoreColors = (score: number) =>
  score >= 80 ? 'text-tactical-green' : score >= 50 ? 'text-tactical-amber' : 'text-tactical-red'

const trendSymbols: Record<string, string> = { up: '↑', stable: '→', down: '↓' }
const trendColors: Record<string, string> = {
  up: 'text-tactical-green',
  stable: 'text-tactical-green',
  down: 'text-tactical-red',
}

const severityIcons: Record<string, string> = {
  critical: '🔴',
  warning: '🟡',
  info: '⚪',
}

const severityColors: Record<string, string> = {
  critical: 'text-tactical-red',
  warning: 'text-tactical-orange',
  info: 'text-sand-muted',
}

export default function Health() {
  return (
    <div className="flex flex-col gap-4">
      <h1 className="font-ui text-lg font-bold uppercase tracking-wider text-sand-bright">
        ASSET HEALTH
      </h1>

      <section className="grid grid-cols-1 gap-3 sm:grid-cols-4">
        <KpiCard
          title="ACTIVE_ALERTS"
          label="ACTIVE ALERTS"
          value={activeAlerts.length.toString()}
          alert
          trend="neutral"
        />
        <KpiCard
          title="AVG_HEALTH"
          label="AVERAGE HEALTH SCORE"
          value="73"
          unit="%"
          trend="neutral"
        />
        <KpiCard
          title="CRITICAL"
          label="CRITICAL ALERTS"
          value={activeAlerts.filter((a) => a.severity === 'critical').length.toString()}
          alert
          trend="neutral"
        />
        <KpiCard
          title="WARNINGS"
          label="WARNING ALERTS"
          value={activeAlerts.filter((a) => a.severity === 'warning').length.toString()}
          trend="neutral"
        />
      </section>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card header="HEALTH SCORES">
          <table className="data-table">
            <thead>
              <tr>
                <th>Asset</th>
                <th>Score</th>
                <th>Trend</th>
                <th>Anomalies</th>
              </tr>
            </thead>
            <tbody>
              {healthScores.map((h) => (
                <tr key={h.asset}>
                  <td className="font-bold text-tactical-amber">{h.asset}</td>
                  <td>
                    <span className={cn('font-bold', scoreColors(h.score))}>
                      {h.score}%
                    </span>
                  </td>
                  <td>
                    <span className={cn('text-lg', trendColors[h.trend])}>
                      {trendSymbols[h.trend]}
                    </span>
                  </td>
                  <td className={cn(h.anomalies > 5 && 'text-tactical-red', h.anomalies === 0 && 'text-tactical-green')}>
                    {h.anomalies}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>

        <Card header="ACTIVE ALERTS">
          <div className="flex flex-col gap-2">
            {activeAlerts.map((alert, i) => (
              <div
                key={i}
                className="flex items-start gap-3 border-b border-surface-light pb-2 last:border-0 last:pb-0"
              >
                <span className="text-xs">{severityIcons[alert.severity]}</span>
                <div className="min-w-0 flex-1">
                  <div className="font-data flex items-baseline gap-2 text-[0.65rem] text-sand-muted">
                    <span className={cn('font-bold', severityColors[alert.severity])}>
                      {alert.severity.toUpperCase()}
                    </span>
                    <span className="text-tactical-amber">{alert.asset}</span>
                  </div>
                  <p className="font-data mt-0.5 text-xs text-sand-bright">{alert.message}</p>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>

      <Card header="ALERTS LOG">
        <div className="flex flex-col gap-1.5">
          {alertLogs.map((log, i) => (
            <div
              key={i}
              className="flex items-start gap-3 border-b border-surface-light pb-1.5 last:border-0 last:pb-0"
            >
              <span className="mt-0.5 text-xs">{severityIcons[log.severity]}</span>
              <div className="font-data flex-1 text-xs">
                <span className="text-sand-muted">{log.time}</span>
                <span className="mx-2 text-sand-muted">|</span>
                <span className="text-tactical-amber">{log.asset}</span>
                <span className="mx-2 text-sand-muted">|</span>
                <span className={cn(severityColors[log.severity])}>{log.event}</span>
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  )
}
