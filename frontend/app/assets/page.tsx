'use client'

import { Card } from '@/components/ui/card'
import { cn } from '@/lib/utils'
import { useState } from 'react'
import dynamic from 'next/dynamic'

const AssetMap = dynamic(() => import('@/components/widgets/AssetMap'), { ssr: false })

interface Asset {
  id: string
  type: 'Inverter' | 'Panel' | 'Battery' | 'Meter' | 'Array' | 'Transformer'
  site: string
  capacity: number
  health: number
  status: 'NOMINAL' | 'ALERT' | 'OFFLINE'
}

const assets: Asset[] = [
  { id: 'INV-01', type: 'Inverter', site: 'ALPHA-DESERT-01', capacity: 5.0, health: 94, status: 'NOMINAL' },
  { id: 'INV-02', type: 'Inverter', site: 'ALPHA-DESERT-01', capacity: 5.0, health: 87, status: 'NOMINAL' },
  { id: 'INV-03', type: 'Inverter', site: 'ALPHA-DESERT-01', capacity: 5.0, health: 52, status: 'ALERT' },
  { id: 'INV-04', type: 'Inverter', site: 'ALPHA-DESERT-01', capacity: 5.0, health: 76, status: 'NOMINAL' },
  { id: 'INV-05', type: 'Inverter', site: 'ALPHA-DESERT-01', capacity: 5.0, health: 33, status: 'OFFLINE' },
  { id: 'MET-01', type: 'Meter', site: 'ALPHA-DESERT-01', capacity: 0, health: 98, status: 'NOMINAL' },
  { id: 'BAT-01', type: 'Battery', site: 'ALPHA-DESERT-01', capacity: 20.0, health: 81, status: 'NOMINAL' },
  { id: 'INV-06', type: 'Inverter', site: 'ALPHA-DESERT-01', capacity: 5.0, health: 91, status: 'NOMINAL' },
  { id: 'INV-07', type: 'Inverter', site: 'ALPHA-DESERT-01', capacity: 5.0, health: 45, status: 'ALERT' },
  { id: 'INV-08', type: 'Inverter', site: 'ALPHA-DESERT-01', capacity: 5.0, health: 68, status: 'NOMINAL' },
  { id: 'INV-09', type: 'Inverter', site: 'ALPHA-DESERT-01', capacity: 5.0, health: 73, status: 'NOMINAL' },
  { id: 'INV-10', type: 'Inverter', site: 'ALPHA-DESERT-01', capacity: 5.0, health: 88, status: 'NOMINAL' },
  { id: 'ARR-A1', type: 'Array', site: 'ALPHA-DESERT-01', capacity: 50.0, health: 79, status: 'NOMINAL' },
  { id: 'TRF-01', type: 'Transformer', site: 'ALPHA-DESERT-01', capacity: 60.0, health: 92, status: 'NOMINAL' },
]

const statusColors: Record<string, string> = {
  NOMINAL: 'text-tactical-green',
  ALERT: 'text-tactical-orange',
  OFFLINE: 'text-tactical-red',
}

export default function Assets() {
  const [selected, setSelected] = useState<string | null>(null)

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h1 className="font-ui text-lg font-bold uppercase tracking-wider text-sand-bright">
          ASSET INVENTORY
        </h1>
        <span className="font-data rounded border border-border-hard bg-surface-mid px-3 py-1 text-xs text-tactical-amber">
          {assets.length} ASSETS
        </span>
      </div>

      <AssetMap />

      <Card>
        <div className="overflow-x-auto">
          <table className="data-table">
            <thead>
              <tr>
                <th>Asset ID</th>
                <th>Type</th>
                <th>Site</th>
                <th>Capacity (MW)</th>
                <th>Health %</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {assets.map((asset) => (
                <tr
                  key={asset.id}
                  onClick={() => {
                    setSelected(asset.id)
                    console.log('Asset selected:', asset.id)
                  }}
                  className={cn(
                    'cursor-pointer transition-colors hover:bg-surface-mid',
                    asset.health < 60 && 'border-l-2 border-l-tactical-orange',
                    selected === asset.id && 'bg-surface-light',
                  )}
                >
                  <td className="font-bold text-tactical-amber">{asset.id}</td>
                  <td className="text-sand-muted">{asset.type}</td>
                  <td className="text-sand-muted">{asset.site}</td>
                  <td className="text-sand-bright">{asset.capacity.toFixed(1)}</td>
                  <td>
                    <span
                      className={cn(
                        asset.health >= 80 && 'text-tactical-green',
                        asset.health >= 50 && asset.health < 80 && 'text-tactical-amber',
                        asset.health < 50 && 'text-tactical-red',
                      )}
                    >
                      {asset.health}%
                    </span>
                  </td>
                  <td>
                    <span className={cn('font-bold', statusColors[asset.status])}>
                      {asset.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  )
}
