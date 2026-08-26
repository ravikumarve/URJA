'use client'

import { useCallback, useState } from 'react'
import dynamic from 'next/dynamic'
import { Card } from '@/components/ui/card'
import KpiCard from '@/components/widgets/KpiCard'
import { EmptyState, ErrorPanel, SkeletonPanels, SkeletonRows } from '@/components/widgets/states'
import { api } from '@/lib/api'
import type { Asset, Site } from '@/lib/types'
import { useApiData } from '@/lib/use-api-data'
import { cn } from '@/lib/utils'

const AssetMap = dynamic(() => import('@/components/widgets/AssetMap'), { ssr: false })

interface AssetsData {
  assets: Asset[]
  total: number
  sites: Site[]
}

function statusColor(status: string): string {
  const s = status.toLowerCase()
  if (s === 'online' || s === 'nominal' || s === 'active') return 'text-tactical-green'
  if (s === 'maintenance' || s === 'alert' || s === 'degraded') return 'text-tactical-orange'
  if (s === 'offline' || s === 'fault') return 'text-tactical-red'
  return 'text-sand-muted'
}

export default function Assets() {
  const [selected, setSelected] = useState<string | null>(null)

  const fetcher = useCallback(async (): Promise<AssetsData> => {
    const [assetsRes, sitesRes] = await Promise.all([
      api.assets.list({ page_size: 100 }),
      api.assets.sites({ page_size: 50 }),
    ])
    return {
      assets: assetsRes.items,
      total: assetsRes.total,
      sites: sitesRes.items,
    }
  }, [])

  const { state, reload } = useApiData(fetcher)

  if (state.phase === 'loading') {
    return (
      <div className="flex flex-col gap-4">
        <SkeletonPanels />
        <div className="panel h-[400px] animate-pulse opacity-40" />
        <div className="panel p-4"><SkeletonRows rows={8} /></div>
      </div>
    )
  }

  if (state.phase === 'error') {
    return <ErrorPanel message={state.message} onRetry={reload} />
  }

  const { assets, total, sites } = state.data

  const totalCapacityKw = assets.reduce((s, a) => s + (a.capacity_kw ?? 0), 0)
  const healthScores = assets
    .map((a) => a.health_score)
    .filter((h): h is number => h !== null)
  const avgHealth =
    healthScores.length > 0
      ? healthScores.reduce((s, h) => s + h, 0) / healthScores.length
      : 0
  const geolocated = assets.filter(
    (a) => a.latitude !== null && a.longitude !== null,
  )
  const mapCenter: [number, number] =
    geolocated.length > 0
      ? [geolocated[0].latitude!, geolocated[0].longitude!]
      : [26.912, 70.825]

  const mapAssets = geolocated.map((a) => ({
    id: a.name,
    type: a.asset_type,
    lat: a.latitude!,
    lng: a.longitude!,
    health: a.health_score ?? 0,
    status: a.status.toUpperCase(),
    capacity: (a.capacity_kw ?? 0) / 1000,
  }))

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h1 className="font-ui text-lg font-bold uppercase tracking-wider text-sand-bright">
          ASSET INVENTORY
        </h1>
        <span className="font-data rounded border border-border-hard bg-surface-mid px-3 py-1 text-xs text-tactical-amber">
          {total} ASSETS / {sites.length} SITES
        </span>
      </div>

      <section className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <KpiCard title="ASSETS" label="REGISTERED ASSETS" value={String(total)} trend="neutral" />
        <KpiCard
          title="CAPACITY"
          label="TOTAL INSTALLED"
          value={(totalCapacityKw / 1000).toFixed(1)}
          unit="MW"
          trend="neutral"
        />
        <KpiCard title="SITES" label="ACTIVE SITES" value={String(sites.length)} trend="neutral" />
        <KpiCard
          title="FLEET HEALTH"
          label="MEAN SCORE"
          value={avgHealth.toFixed(1)}
          unit="/100"
          trend="neutral"
          alert={avgHealth > 0 && avgHealth < 60}
        />
      </section>

      <AssetMap assets={mapAssets} center={mapCenter} />

      <Card header={`SITES (${sites.length})`}>
        {sites.length === 0 ? (
          <EmptyState label="NO SITES REGISTERED" />
        ) : (
          <div className="overflow-x-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Site</th>
                  <th>Code</th>
                  <th>Capacity (MW)</th>
                  <th>Timezone</th>
                  <th>Assets</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {sites.map((site) => (
                  <tr key={site.id}>
                    <td className="font-bold text-tactical-amber">{site.name}</td>
                    <td className="text-sand-muted">{site.code}</td>
                    <td className="text-sand-bright">{site.capacity_mw.toFixed(1)}</td>
                    <td className="text-sand-muted">{site.timezone}</td>
                    <td className="text-sand-bright">{site.asset_count}</td>
                    <td>
                      <span className={cn('font-bold', statusColor(site.status))}>
                        {site.status.toUpperCase()}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      <Card header={`ASSETS (${assets.length} SHOWN)`}>
        {assets.length === 0 ? (
          <EmptyState label="NO ASSETS REGISTERED — ADD ASSETS VIA API OR SEED DATA" />
        ) : (
          <div className="overflow-x-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Asset</th>
                  <th>Type</th>
                  <th>Code</th>
                  <th>Capacity (kW)</th>
                  <th>Health %</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {assets.map((asset) => (
                  <tr
                    key={asset.id}
                    onClick={() => setSelected(asset.id)}
                    className={cn(
                      'cursor-pointer transition-colors hover:bg-surface-mid',
                      (asset.health_score ?? 100) < 60 && 'border-l-2 border-l-tactical-orange',
                      selected === asset.id && 'bg-surface-light',
                    )}
                  >
                    <td className="font-bold text-tactical-amber">{asset.name}</td>
                    <td className="text-sand-muted">{asset.asset_type}</td>
                    <td className="text-sand-muted">{asset.code}</td>
                    <td className="text-sand-bright">
                      {asset.capacity_kw !== null ? asset.capacity_kw.toLocaleString() : '—'}
                    </td>
                    <td>
                      {asset.health_score === null ? (
                        <span className="text-sand-muted">—</span>
                      ) : (
                        <span
                          className={cn(
                            asset.health_score >= 80 && 'text-tactical-green',
                            asset.health_score >= 50 &&
                              asset.health_score < 80 &&
                              'text-tactical-amber',
                            asset.health_score < 50 && 'text-tactical-red',
                          )}
                        >
                          {asset.health_score.toFixed(0)}%
                        </span>
                      )}
                    </td>
                    <td>
                      <span className={cn('font-bold', statusColor(asset.status))}>
                        {asset.status.toUpperCase()}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  )
}
