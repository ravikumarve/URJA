'use client'

import { useCallback } from 'react'
import KpiCard from '@/components/widgets/KpiCard'
import { Card } from '@/components/ui/card'
import DuckCurveChart from '@/components/charts/DuckCurveChart'
import { EmptyState, ErrorPanel, SkeletonPanels, SkeletonRows } from '@/components/widgets/states'
import { api } from '@/lib/api'
import type { CurtailmentEvent, DispatchDecision, RevenueLost } from '@/lib/types'
import { useApiData } from '@/lib/use-api-data'
import { cn } from '@/lib/utils'

interface YieldData {
  events: CurtailmentEvent[]
  eventTotal: number
  decisions: DispatchDecision[]
  revenue: RevenueLost
}

function fmtTime(iso: string): string {
  const d = new Date(iso)
  return Number.isNaN(d.getTime()) ? '—' : d.toLocaleTimeString([], { hour12: false })
}

export default function Yield() {
  const fetcher = useCallback(async (): Promise<YieldData> => {
    const [eventsRes, decisionsRes, revenue] = await Promise.all([
      api.dispatch.curtailmentEvents({ per_page: 20 }),
      api.dispatch.decisions({ per_page: 10 }),
      api.dispatch.revenueLost(30),
    ])
    return {
      events: eventsRes.data,
      eventTotal: eventsRes.pagination.total,
      decisions: decisionsRes.data,
      revenue,
    }
  }, [])

  const { state, reload } = useApiData(fetcher)

  if (state.phase === 'loading') {
    return (
      <div className="flex flex-col gap-4">
        <SkeletonPanels />
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          <div className="panel h-[300px] animate-pulse opacity-40" />
          <div className="panel h-[300px] animate-pulse opacity-40" />
        </div>
      </div>
    )
  }

  if (state.phase === 'error') {
    return <ErrorPanel message={state.message} onRetry={reload} />
  }

  const { events, eventTotal, decisions, revenue } = state.data

  return (
    <div className="flex flex-col gap-4">
      <h1 className="font-ui text-lg font-bold uppercase tracking-wider text-sand-bright">
        YIELD DISPATCH
      </h1>

      <section className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <KpiCard
          title="REVENUE_LOST"
          label="LAST 30 DAYS"
          value={`₹${Math.round(revenue.total_revenue).toLocaleString()}`}
          trend="down"
          alert={revenue.total_revenue > 0}
        />
        <KpiCard
          title="CURTAILMENT"
          label={`EVENTS / ${revenue.event_count} IN 30D`}
          value={String(eventTotal)}
          trend="neutral"
        />
        <KpiCard
          title="CURTAILED"
          label="ENERGY CURTAILED 30D"
          value={(revenue.total_curtailed / 1000).toFixed(1)}
          unit="MWh"
          trend="neutral"
        />
        <KpiCard
          title="AVG_PRICE"
          label="AVG CURTAILMENT PRICE"
          value={`₹${revenue.avg_price.toFixed(2)}`}
          unit="/kWh"
          trend="neutral"
        />
      </section>

      <section className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card header={`CURTAILMENT EVENTS (${eventTotal})`}>
          {events.length === 0 ? (
            <EmptyState label="NO CURTAILMENT EVENTS RECORDED" />
          ) : (
            <div className="overflow-x-auto">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Time</th>
                    <th>Asset</th>
                    <th>Duration</th>
                    <th>Curtailed (kWh)</th>
                    <th>Price</th>
                    <th>Revenue Lost</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {events.map((evt) => (
                    <tr
                      key={evt.event_id}
                      className={cn(
                        'border-l-2',
                        !evt.is_resolved
                          ? 'border-l-tactical-red bg-tactical-red/10'
                          : 'border-l-transparent opacity-60',
                      )}
                    >
                      <td className="text-tactical-amber">{fmtTime(evt.ts)}</td>
                      <td className="text-sand-muted">{evt.asset_name}</td>
                      <td className="text-sand-bright">{evt.duration_minutes}m</td>
                      <td className="text-sand-bright">{evt.curtailed_kwh.toLocaleString()}</td>
                      <td className="text-sand-muted">₹{evt.price_per_kwh.toFixed(2)}</td>
                      <td className="text-tactical-red">
                        ₹{Math.round(evt.revenue_lost).toLocaleString()}
                      </td>
                      <td>
                        <span
                          className={cn(
                            'font-bold text-xs',
                            evt.is_resolved ? 'text-sand-muted' : 'text-tactical-red',
                          )}
                        >
                          {evt.is_resolved ? 'RESOLVED' : 'ACTIVE'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>

        <Card header="DISPATCH DECISIONS LOG">
          {decisions.length === 0 ? (
            <EmptyState label="NO DISPATCH DECISIONS EXECUTED" />
          ) : (
            <div className="flex flex-col gap-1.5">
              {decisions.map((d) => (
                <div
                  key={d.id}
                  className="border-b border-surface-light pb-1.5 last:border-0 last:pb-0"
                >
                  <div className="font-data flex items-baseline gap-2 text-[0.65rem] text-sand-muted">
                    <span className="text-tactical-amber">{fmtTime(d.created_at)}</span>
                    <span>{d.rule_name ?? 'MANUAL'}</span>
                    <span>· {d.asset_name ?? '—'}</span>
                  </div>
                  <div className="font-data mt-0.5 flex items-baseline gap-2 text-xs">
                    <span
                      className={cn(
                        'font-bold uppercase',
                        d.status === 'executed' && 'text-tactical-green',
                        d.status === 'failed' && 'text-tactical-red',
                        d.status !== 'executed' && d.status !== 'failed' && 'text-tactical-orange',
                      )}
                    >
                      [{d.action_taken}]
                    </span>
                    <span className="text-sand-bright">
                      {d.actual_outcome ?? d.expected_outcome ?? d.status}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>
      </section>

      <Card header="GENERATION — DUCK CURVE WITH PRICE OVERLAY (SAMPLE DATA)">
        <DuckCurveChart />
      </Card>
    </div>
  )
}
