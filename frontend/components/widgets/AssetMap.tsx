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

const mapAssets: MapAsset[] = [
  { id: 'INV-01', type: 'Inverter',    lat: 26.901, lng: 70.818, health: 94, status: 'NOMINAL', capacity: 5.0 },
  { id: 'INV-02', type: 'Inverter',    lat: 26.908, lng: 70.814, health: 87, status: 'NOMINAL', capacity: 5.0 },
  { id: 'INV-03', type: 'Inverter',    lat: 26.915, lng: 70.810, health: 52, status: 'ALERT',   capacity: 5.0 },
  { id: 'INV-04', type: 'Inverter',    lat: 26.902, lng: 70.830, health: 76, status: 'NOMINAL', capacity: 5.0 },
  { id: 'INV-05', type: 'Inverter',    lat: 26.920, lng: 70.822, health: 33, status: 'OFFLINE', capacity: 5.0 },
  { id: 'INV-06', type: 'Inverter',    lat: 26.895, lng: 70.813, health: 91, status: 'NOMINAL', capacity: 5.0 },
  { id: 'INV-07', type: 'Inverter',    lat: 26.925, lng: 70.835, health: 45, status: 'ALERT',   capacity: 5.0 },
  { id: 'INV-08', type: 'Inverter',    lat: 26.910, lng: 70.840, health: 68, status: 'NOMINAL', capacity: 5.0 },
  { id: 'INV-09', type: 'Inverter',    lat: 26.918, lng: 70.800, health: 73, status: 'NOMINAL', capacity: 5.0 },
  { id: 'INV-10', type: 'Inverter',    lat: 26.885, lng: 70.828, health: 88, status: 'NOMINAL', capacity: 5.0 },
  { id: 'MET-01', type: 'Meter',       lat: 26.908, lng: 70.845, health: 98, status: 'NOMINAL', capacity: 0.0 },
  { id: 'BAT-01', type: 'Battery',     lat: 26.930, lng: 70.815, health: 81, status: 'NOMINAL', capacity: 20.0 },
  { id: 'ARR-A1', type: 'Array',       lat: 26.898, lng: 70.805, health: 79, status: 'NOMINAL', capacity: 50.0 },
  { id: 'TRF-01', type: 'Transformer', lat: 26.905, lng: 70.850, health: 92, status: 'NOMINAL', capacity: 60.0 },
]

function healthColor(health: number): string {
  if (health >= 80) return '#4ade80'
  if (health >= 50) return '#ffb703'
  return '#ef4444'
}

function getRadius(capacity: number): number {
  return Math.max(8, Math.min(40, capacity * 2))
}

export default function AssetMap() {
  return (
    <div className="panel flex flex-col overflow-hidden">
      <div className="panel-header">
        <span>SITE ASSET MAP — ALPHA-DESERT-01</span>
      </div>
      <div className="panel-body relative !p-0">
        <MapContainer
          center={[26.912, 70.825]}
          zoom={13}
          className="h-[400px] w-full"
          zoomControl={false}
          attributionControl={false}
        >
          <TileLayer url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png" />
          {mapAssets.map((asset) => (
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
