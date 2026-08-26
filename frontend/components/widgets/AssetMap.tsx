'use client'

import { MapContainer, TileLayer, CircleMarker, Tooltip } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import { cn } from '@/lib/utils'

interface MapAsset {
  id: string
  type: string
  lat: number
  lng: number
  health: number
  status: string
  capacity: number
}

function healthColor(health: number): string {
  if (health >= 80) return '#4ade80'
  if (health >= 50) return '#ffb703'
  return '#ef4444'
}

function getRadius(capacity: number): number {
  return Math.max(8, Math.min(40, capacity * 2))
}

interface AssetMapProps {
  assets?: MapAsset[]
  center?: [number, number]
  title?: string
}

export default function AssetMap({
  assets = [],
  center = [26.912, 70.825],
  title = 'SITE ASSET MAP',
}: AssetMapProps) {
  return (
    <div className="panel flex flex-col overflow-hidden">
      <div className="panel-header">
        <span>
          {title}
          {assets.length > 0 ? ` — ${assets.length} GEOLOCATED` : ''}
        </span>
      </div>
      <div className="panel-body relative !p-0">
        <MapContainer
          center={center}
          zoom={13}
          className="h-[400px] w-full"
          zoomControl={false}
          attributionControl={false}
        >
          <TileLayer url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png" />
          {assets.map((asset) => (
            <CircleMarker
              key={asset.id}
              center={[asset.lat, asset.lng]}
              radius={getRadius(asset.capacity)}
              pathOptions={{
                color: healthColor(asset.health),
                fillColor: healthColor(asset.health),
                fillOpacity: 0.35,
                weight: 2,
              }}
            >
              <Tooltip direction="top" offset={[0, -10]} className="urja-tooltip">
                <div className="font-ui text-xs leading-relaxed">
                  <div className="font-bold text-tactical-amber">{asset.id}</div>
                  <div className="mt-0.5 text-sand-muted">{asset.type}</div>
                  <div className="mt-1 flex items-center gap-2">
                    <span
                      className="inline-block h-2 w-2 rounded-full"
                      style={{ backgroundColor: healthColor(asset.health) }}
                    />
                    <span>{asset.health}% health</span>
                  </div>
                  <div
                    className={cn(
                      'font-bold',
                      asset.status === 'NOMINAL' && 'text-tactical-green',
                      asset.status === 'ALERT' && 'text-tactical-amber',
                      asset.status === 'OFFLINE' && 'text-tactical-red',
                    )}
                  >
                    {asset.status}
                  </div>
                  <div className="text-sand-muted">
                    {asset.capacity > 0 ? `${asset.capacity.toFixed(1)} MW` : '-- MW'}
                  </div>
                </div>
              </Tooltip>
            </CircleMarker>
          ))}
        </MapContainer>

        {/* Legend */}
        <div className="absolute right-3 top-3 z-[1000] rounded border border-border-hard bg-surface-dark/90 px-3 py-2 font-data text-[0.6rem] leading-relaxed">
          <div className="mb-1 text-[0.55rem] uppercase tracking-wider text-sand-muted">
            Health
          </div>
          <div className="flex items-center gap-2">
            <span className="inline-block h-2 w-2 rounded-full bg-tactical-green" />
            <span className="text-sand-bright">&ge;80%</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="inline-block h-2 w-2 rounded-full bg-tactical-amber" />
            <span className="text-sand-bright">50–79%</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="inline-block h-2 w-2 rounded-full bg-tactical-red" />
            <span className="text-sand-bright">&lt;50%</span>
          </div>
        </div>
      </div>

      <style>{`
        .urja-tooltip {
          background: #1c1a17 !important;
          border: 1px solid #3a332d !important;
          box-shadow: none !important;
          border-radius: 0 !important;
          padding: 8px 12px !important;
          font-family: 'Chakra Petch', sans-serif !important;
        }
        .urja-tooltip::before {
          border-top-color: #3a332d !important;
        }
        .leaflet-container {
          background: #090807 !important;
          font-family: 'Chakra Petch', sans-serif !important;
        }
      `}</style>
    </div>
  )
}
