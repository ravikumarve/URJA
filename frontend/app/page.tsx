'use client'

import KpiCard from '@/components/widgets/KpiCard'
import DuckCurveChart from '@/components/charts/DuckCurveChart'
import RadarCanvas from '@/components/widgets/RadarCanvas'
import { Card } from '@/components/ui/card'
import { AlertTriangle, Thermometer, CloudRain, WifiOff } from 'lucide-react'

const alerts = [
  {
    severity: 'critical' as const,
    icon: AlertTriangle,
    time: '14:02:11',
    source: 'weather_ingest',
    message: 'STORM_WARNING — Dust storm approaching. ETA 45 min.',
  },
  {
    severity: 'warning' as const,
    icon: Thermometer,
    time: '14:02:08',
    source: 'inv_array_04',
    message: 'TEMP_SPIKE_52°C — Inverter derating to 60%',
  },
  {
    severity: 'warning' as const,
    icon: CloudRain,
    time: '13:58:12',
    source: 'soiling_sensor',
    message: 'SOILING_RATIO 78% — Cleaning required within 24h',
  },
  {
    severity: 'info' as const,
    icon: WifiOff,
    time: '13:45:00',
    source: 'comms_link',
    message: 'SCADA_LINK_FLAP — Microwave link instability',
  },
]

const severityColors = {
  critical: 'text-tactical-red',
  warning: 'text-tactical-orange',
  info: 'text-tactical-amber',
}

const severityDots = {
  critical: 'bg-tactical-red',
  warning: 'bg-tactical-orange',
  info: 'bg-tactical-amber',
}

const bottomMetrics = [
  { title: 'DC POWER', label: 'INVERTER INPUT', value: '34.8', unit: 'MW', status: 'ok' },
  { title: 'AC POWER', label: 'GRID INJECTION', value: '32.4', unit: 'MW', status: 'ok' },
  { title: 'EFFICIENCY', label: 'PR', value: '87.2', unit: '%', status: 'warn' },
  { title: 'IRRADIANCE', label: 'POA', value: '612', unit: 'W/m²', status: 'ok' },
  { title: 'AMBIENT TEMP', label: 'SITE', value: '44.2', unit: '°C', status: 'warn' },
  { title: 'WIND SPEED', label: 'ANEMOMETER', value: '42.8', unit: 'km/h', status: 'crit' },
]

export default function Dashboard() {
  return (
    <div className="flex flex-col gap-4">
      <section className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
        <KpiCard
          title="GEN_MONITOR"
          label="ACTIVE GENERATION / CAPACITY"
          value="32.4"
          unit="MW"
          trend="down"
          alert
        />
        <KpiCard
          title="YIELD_MONITOR"
          label="TODAY'S YIELD"
          value="245"
          unit="MWh"
          trend="up"
        />
        <KpiCard
          title="REVENUE"
          label="REVENUE TODAY"
          value="₹14.2"
          unit="L"
          trend="up"
        />
        <KpiCard
          title="ALERTS"
          label="ACTIVE ALERTS"
          value="4"
          alert
          trend="neutral"
        />
        <KpiCard
          title="CARBON"
          label="CARBON CREDITS"
          value="3,450"
          unit="tCO₂e"
          trend="up"
        />
        <KpiCard
          title="MARKET"
          label="GRID PRICE"
          value="₹2.8"
          unit="/kWh"
          trend="up"
        />
      </section>

      <section className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <Card header="DUCK CURVE — GENERATION VS GRID PRICE" className="lg:col-span-2">
          <DuckCurveChart />
        </Card>

        <Card header="ACTIVE ALERTS">
          <div className="flex flex-col gap-2">
            {alerts.map((alert, i) => {
              const Icon = alert.icon
              return (
                <div
                  key={i}
                  className="flex items-start gap-3 border-b border-surface-light pb-2 last:border-0 last:pb-0"
                >
                  <span
                    className={`mt-0.5 inline-block h-2 w-2 shrink-0 rounded-full ${severityDots[alert.severity]} animate-blink`}
                  />
                  <Icon
                    size={14}
                    className={`mt-0.5 shrink-0 ${severityColors[alert.severity]}`}
                  />
                  <div className="min-w-0 flex-1">
                    <div className="font-data flex items-baseline gap-2 text-[0.65rem] text-sand-muted">
                      <span>{alert.time}</span>
                      <span className="text-tactical-amber">{alert.source}</span>
                    </div>
                    <p
                      className={`font-data mt-0.5 text-xs ${severityColors[alert.severity]}`}
                    >
                      {alert.message}
                    </p>
                  </div>
                </div>
              )
            })}
          </div>
        </Card>
      </section>

      <RadarCanvas />

      <section className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
        {bottomMetrics.map((m, i) => (
          <div
            key={i}
            className="panel flex flex-col justify-between p-3"
          >
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
