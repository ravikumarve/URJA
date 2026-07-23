'use client'

import KpiCard from '@/components/widgets/KpiCard'
import { Card } from '@/components/ui/card'
import DuckCurveChart from '@/components/charts/DuckCurveChart'
import { cn } from '@/lib/utils'

interface CurtailmentEvent {
  time: string
  duration: string
  curtailed: number
  price: number
  revenueLost: number
  status: 'ACTIVE' | 'RESOLVED' | 'HISTORICAL'
}

interface DispatchLog {
  time: string
  action: string
  detail: string
}

const curtailmentEvents: CurtailmentEvent[] = [
  { time: '10:32', duration: '18m', curtailed: 4.2, price: 2.8, revenueLost: 11760, status: 'ACTIVE' },
  { time: '09:15', duration: '42m', curtailed: 9.8, price: 2.6, revenueLost: 25480, status: 'RESOLVED' },
  { time: '07:48', duration: '12m', curtailed: 2.1, price: 2.4, revenueLost: 5040, status: 'RESOLVED' },
  { time: '06:00', duration: '8m', curtailed: 1.3, price: 2.3, revenueLost: 2990, status: 'HISTORICAL' },
  { time: '04:22', duration: '15m', curtailed: 3.6, price: 1.6, revenueLost: 5760, status: 'HISTORICAL' },
]

const dispatchLogs: DispatchLog[] = [
  { time: '10:33:01', action: 'RECALL_BATTERY', detail: 'BAT-01 dispatched to curtailment gap — 4.2 MW' },
  { time: '10:32:44', action: 'CURTAILMENT', detail: 'Grid request: reduce injection by 4.2 MW' },
  { time: '09:57:12', action: 'RECALL_BATTERY', detail: 'BAT-01 returning to standby — SOC 84%' },
  { time: '09:15:23', action: 'CURTAILMENT', detail: 'Grid request: reduce injection by 9.8 MW' },
  { time: '09:15:00', action: 'DISPATCH_BATTERY', detail: 'BAT-01 dispatched — SOC 72% → absorbing 9.8 MW' },
  { time: '08:30:11', action: 'PRICE_SIGNAL', detail: 'Grid price dropped to ₹2.4/kWh — reducing injection' },
]

const statusRowColors: Record<string, string> = {
  ACTIVE: 'bg-tactical-red/10 border-l-tactical-red',
  RESOLVED: 'bg-tactical-amber/5 border-l-tactical-amber',
  HISTORICAL: 'opacity-50 border-l-transparent',
}

export default function Yield() {
  return (
    <div className="flex flex-col gap-4">
      <h1 className="font-ui text-lg font-bold uppercase tracking-wider text-sand-bright">
        YIELD DISPATCH
      </h1>

      <section className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <KpiCard
          title="REVENUE_LOST"
          label="REVENUE LOST TODAY"
          value="₹51,030"
          trend="down"
          alert
        />
        <KpiCard
          title="CURTAILMENT"
          label="CURTAILMENT EVENTS"
          value="5"
          trend="neutral"
        />
        <KpiCard
          title="BATTERY_SOC"
          label="BATTERY SOC"
          value="84"
          unit="%"
          trend="up"
        />
        <KpiCard
          title="GRID_PRICE"
          label="GRID PRICE"
          value="₹2.8"
          unit="/kWh"
          trend="up"
        />
      </section>

      <section className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card header="CURTAILMENT EVENTS">
          <table className="data-table">
            <thead>
              <tr>
                <th>Time</th>
                <th>Duration</th>
                <th>Curtailed (MWh)</th>
                <th>Price</th>
                <th>Revenue Lost</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {curtailmentEvents.map((evt, i) => (
                <tr key={i} className={cn('border-l-2', statusRowColors[evt.status])}>
                  <td className="text-tactical-amber">{evt.time}</td>
                  <td className="text-sand-bright">{evt.duration}</td>
                  <td className="text-sand-bright">{evt.curtailed.toFixed(1)}</td>
                  <td className="text-sand-muted">₹{evt.price.toFixed(1)}</td>
                  <td className="text-tactical-red">₹{evt.revenueLost.toLocaleString()}</td>
                  <td>
                    <span className={cn(
                      'font-bold text-xs',
                      evt.status === 'ACTIVE' && 'text-tactical-red',
                      evt.status === 'RESOLVED' && 'text-tactical-amber',
                      evt.status === 'HISTORICAL' && 'text-sand-muted',
                    )}>
                      {evt.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>

        <Card header="DISPATCH DECISIONS LOG">
          <div className="flex flex-col gap-1.5">
            {dispatchLogs.map((log, i) => (
              <div key={i} className="border-b border-surface-light pb-1.5 last:border-0 last:pb-0">
                <div className="font-data flex items-baseline gap-2 text-[0.65rem] text-sand-muted">
                  <span className="text-tactical-amber">{log.time}</span>
                </div>
                <div className="font-data mt-0.5 flex items-baseline gap-2 text-xs">
                  <span className={cn(
                    'font-bold',
                    log.action.includes('CURTAIL') && 'text-tactical-red',
                    log.action.includes('DISPATCH') && 'text-tactical-green',
                    log.action.includes('RECALL') && 'text-tactical-amber',
                    log.action.includes('PRICE') && 'text-tactical-orange',
                  )}>
                    [{log.action}]
                  </span>
                  <span className="text-sand-bright">{log.detail}</span>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </section>

      <Card header="GENERATION — DUCK CURVE WITH PRICE OVERLAY">
        <DuckCurveChart />
      </Card>
    </div>
  )
}
