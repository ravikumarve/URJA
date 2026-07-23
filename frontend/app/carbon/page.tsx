'use client'

import KpiCard from '@/components/widgets/KpiCard'
import { Card } from '@/components/ui/card'
import { cn } from '@/lib/utils'

interface CreditBatch {
  id: string
  date: string
  co2e: number
  credits: number
  status: 'active' | 'pending'
}

const creditBatches: CreditBatch[] = [
  { id: 'VCS-2026-001', date: '2026-06-01', co2e: 1250, credits: 1250, status: 'active' },
  { id: 'VCS-2026-002', date: '2026-05-01', co2e: 1180, credits: 1180, status: 'active' },
  { id: 'VCS-2026-003', date: '2026-04-01', co2e: 1020, credits: 1020, status: 'active' },
  { id: 'VCS-2026-004', date: '2026-03-01', co2e: 980, credits: 980, status: 'active' },
  { id: 'VCS-2026-005', date: '2026-02-01', co2e: 870, credits: 870, status: 'active' },
  { id: 'VCS-2026-006', date: '2026-07-01', co2e: 1100, credits: 0, status: 'pending' },
]

export default function Carbon() {
  const totalIssued = creditBatches
    .filter((b) => b.status === 'active')
    .reduce((s, b) => s + b.co2e, 0)
  const totalPending = creditBatches
    .filter((b) => b.status === 'pending')
    .reduce((s, b) => s + b.co2e, 0)
  const totalRetired = 3200
  const totalAvailable = totalIssued - totalRetired

  return (
    <div className="flex flex-col gap-4">
      <h1 className="font-ui text-lg font-bold uppercase tracking-wider text-sand-bright">
        CARBON VAULT
      </h1>

      <section className="grid grid-cols-1 gap-3 sm:grid-cols-4">
        <KpiCard
          title="TOTAL_ISSUED"
          label="VERIFIED CREDITS (ACTIVE)"
          value={totalIssued.toLocaleString()}
          unit="tCO₂e"
          trend="up"
        />
        <KpiCard
          title="PENDING"
          label="UNVERIFIED (PENDING VERIFICATION)"
          value={totalPending.toLocaleString()}
          unit="tCO₂e"
          trend="neutral"
        />
        <KpiCard
          title="RETIRED"
          label="CREDITS RETIRED"
          value={totalRetired.toLocaleString()}
          unit="tCO₂e"
          trend="neutral"
        />
        <KpiCard
          title="AVAILABLE"
          label="CREDITS AVAILABLE"
          value={totalAvailable.toLocaleString()}
          unit="tCO₂e"
          trend="up"
        />
      </section>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <Card header="CREDIT BATCHES" className="lg:col-span-2">
          <table className="data-table">
            <thead>
              <tr>
                <th>Batch ID</th>
                <th>Date</th>
                <th>CO₂e (tonnes)</th>
                <th>Credits</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {creditBatches.map((batch) => (
                <tr key={batch.id}>
                  <td className="font-bold text-tactical-amber">{batch.id}</td>
                  <td className="text-sand-muted">{batch.date}</td>
                  <td className="text-sand-bright">{batch.co2e.toLocaleString()}</td>
                  <td className="text-sand-bright">{batch.credits.toLocaleString()}</td>
                  <td>
                    <span
                      className={cn(
                        'font-bold text-xs',
                        batch.status === 'active' && 'text-tactical-green',
                        batch.status === 'pending' && 'text-tactical-amber',
                      )}
                    >
                      {batch.status === 'active' ? 'ACTIVE' : 'PENDING'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>

        <Card header="PORTFOLIO SUMMARY">
          <div className="flex flex-col gap-3 font-data text-xs">
            <div className="flex justify-between border-b border-surface-light pb-2">
              <span className="text-sand-muted">METHODOLOGY</span>
              <span className="text-sand-bright">VM0004 v2.1</span>
            </div>
            <div className="flex justify-between border-b border-surface-light pb-2">
              <span className="text-sand-muted">REGISTRY</span>
              <span className="text-sand-bright">Verra VCS</span>
            </div>
            <div className="flex justify-between border-b border-surface-light pb-2">
              <span className="text-sand-muted">VINTAGE</span>
              <span className="text-sand-bright">2026</span>
            </div>
            <div className="flex justify-between border-b border-surface-light pb-2">
              <span className="text-sand-muted">PROJECT TYPE</span>
              <span className="text-sand-bright">Solar PV — Grid Connected</span>
            </div>
            <div className="flex justify-between border-b border-surface-light pb-2">
              <span className="text-sand-muted">VALIDATION BODY</span>
              <span className="text-sand-bright">SGS United Kingdom</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sand-muted">SDG CONTRIBUTION</span>
              <span className="text-tactical-green">SDG 7, 13</span>
            </div>
          </div>
        </Card>
      </div>
    </div>
  )
}
