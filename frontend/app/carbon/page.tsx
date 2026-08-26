'use client'

import { useCallback } from 'react'
import KpiCard from '@/components/widgets/KpiCard'
import { Card } from '@/components/ui/card'
import { EmptyState, ErrorPanel, SkeletonPanels, SkeletonRows } from '@/components/widgets/states'
import { api } from '@/lib/api'
import type { CarbonCredit, PortfolioSummary } from '@/lib/types'
import { useApiData } from '@/lib/use-api-data'
import { cn } from '@/lib/utils'

interface CarbonData {
  portfolio: PortfolioSummary
  credits: CarbonCredit[]
  creditTotal: number
}

function fmtDate(iso: string | null): string {
  if (!iso) return '—'
  const d = new Date(iso)
  return Number.isNaN(d.getTime()) ? '—' : d.toISOString().split('T')[0]
}

export default function Carbon() {
  const fetcher = useCallback(async (): Promise<CarbonData> => {
    const [portfolio, creditsRes] = await Promise.all([
      api.carbon.portfolio(),
      api.carbon.credits({ per_page: 50 }),
    ])
    return {
      portfolio,
      credits: creditsRes.data,
      creditTotal: creditsRes.pagination.total,
    }
  }, [])

  const { state, reload } = useApiData(fetcher)

  if (state.phase === 'loading') {
    return (
      <div className="flex flex-col gap-4">
        <SkeletonPanels />
        <div className="panel h-[320px] animate-pulse opacity-40" />
      </div>
    )
  }

  if (state.phase === 'error') {
    return <ErrorPanel message={state.message} onRetry={reload} />
  }

  const { portfolio, credits, creditTotal } = state.data

  return (
    <div className="flex flex-col gap-4">
      <h1 className="font-ui text-lg font-bold uppercase tracking-wider text-sand-bright">
        CARBON VAULT
      </h1>

      <section className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <KpiCard
          title="TOTAL_ISSUED"
          label={`${portfolio.total_issued} CREDITS ISSUED`}
          value={portfolio.total_co2e_issued.toLocaleString()}
          unit="tCO₂e"
          trend="up"
        />
        <KpiCard
          title="PENDING"
          label="AWAITING VERIFICATION"
          value={String(portfolio.by_status['pending'] ?? 0)}
          unit=""
          trend="neutral"
        />
        <KpiCard
          title="RETIRED"
          label={`${portfolio.total_retired} CREDITS RETIRED`}
          value={portfolio.total_co2e_retired.toLocaleString()}
          unit="tCO₂e"
          trend="neutral"
        />
        <KpiCard
          title="AVAILABLE"
          label="ACTIVE / TRANSFERABLE"
          value={String(portfolio.total_available)}
          unit=""
          trend="up"
        />
      </section>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <Card header={`CREDIT LEDGER (${creditTotal})`} className="lg:col-span-2">
          {credits.length === 0 ? (
            <EmptyState label="NO CREDITS ISSUED — RUN THE CARBON_MINT WORKER" />
          ) : (
            <div className="overflow-x-auto">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Credit</th>
                    <th>Batch</th>
                    <th>Asset</th>
                    <th>Quantity</th>
                    <th>Methodology</th>
                    <th>Issued</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {credits.map((c) => (
                    <tr key={c.credit_id}>
                      <td className="font-bold text-tactical-amber">
                        {c.credit_id.slice(0, 8)}…
                      </td>
                      <td className="text-sand-muted">{c.batch_id.slice(0, 8)}…</td>
                      <td className="text-sand-muted">{c.asset_name ?? '—'}</td>
                      <td className="text-sand-bright">
                        {c.quantity.toLocaleString()} {c.unit}
                      </td>
                      <td className="text-sand-muted">{c.methodology}</td>
                      <td className="text-sand-muted">{fmtDate(c.created_at)}</td>
                      <td>
                        <span
                          className={cn(
                            'font-bold text-xs uppercase',
                            c.status === 'active' && 'text-tactical-green',
                            c.status === 'pending' && 'text-tactical-amber',
                            c.status === 'retired' && 'text-sand-muted',
                            c.status === 'cancelled' && 'text-tactical-red',
                          )}
                        >
                          {c.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>

        <Card header="PORTFOLIO SUMMARY">
          <div className="flex flex-col gap-3 font-data text-xs">
            {Object.entries(portfolio.by_methodology).map(([method, count]) => (
              <div key={method} className="flex justify-between border-b border-surface-light pb-2">
                <span className="text-sand-muted">METHODOLOGY</span>
                <span className="text-sand-bright">
                  {method} × {count}
                </span>
              </div>
            ))}
            <div className="flex justify-between border-b border-surface-light pb-2">
              <span className="text-sand-muted">LAST ISSUANCE</span>
              <span className="text-sand-bright">{fmtDate(portfolio.last_issuance)}</span>
            </div>
            <div className="flex justify-between border-b border-surface-light pb-2">
              <span className="text-sand-muted">NEXT ELIGIBLE</span>
              <span className="text-sand-bright">{fmtDate(portfolio.next_eligible_date)}</span>
            </div>
            <div className="flex justify-between border-b border-surface-light pb-2">
              <span className="text-sand-muted">CANCELLED</span>
              <span className="text-sand-muted">{portfolio.total_cancelled}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sand-muted">REGISTRY TX</span>
              <span className="text-tactical-green">
                {credits.find((c) => c.registry_tx_id)?.registry_tx_id?.slice(0, 12) ?? '—'}
              </span>
            </div>
          </div>
        </Card>
      </div>
    </div>
  )
}
