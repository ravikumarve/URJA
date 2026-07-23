'use client'

import { useState } from 'react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Copy, Check } from 'lucide-react'

const mockApiKeys = [
  { name: 'Production API', prefix: 'urja_prod_', key: 'a1b2c3d4e5f6...8a9b0c' },
  { name: 'Staging API', prefix: 'urja_stag_', key: 'f6e5d4c3b2a1...0c9b8a' },
]

export default function Settings() {
  const [copied, setCopied] = useState<string | null>(null)
  const [tempThreshold, setTempThreshold] = useState(60)
  const [powerDropThreshold, setPowerDropThreshold] = useState(20)
  const [siteName, setSiteName] = useState('Alpha Desert Solar Farm')
  const [location, setLocation] = useState('Rajasthan, India')
  const [timezone, setTimezone] = useState('Asia/Kolkata (UTC+5:30)')

  const handleCopy = (name: string) => {
    setCopied(name)
    setTimeout(() => setCopied(null), 2000)
  }

  return (
    <div className="flex flex-col gap-4">
      <h1 className="font-ui text-lg font-bold uppercase tracking-wider text-sand-bright">
        SETTINGS & CONFIG
      </h1>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card header="API KEYS">
          <div className="flex flex-col gap-3">
            {mockApiKeys.map((api) => (
              <div
                key={api.name}
                className="flex items-center justify-between rounded border border-border-hard bg-surface-mid p-3"
              >
                <div className="min-w-0 flex-1">
                  <div className="font-ui text-xs font-bold uppercase tracking-wider text-sand-muted">
                    {api.name}
                  </div>
                  <div className="font-data mt-1 text-sm text-sand-bright">
                    <span className="text-tactical-amber">{api.prefix}</span>
                    {api.key}
                  </div>
                </div>
                <button
                  onClick={() => handleCopy(api.name)}
                  className="ml-3 shrink-0 rounded border border-border-hard p-2 text-sand-muted hover:border-sand-muted hover:text-sand-bright"
                >
                  {copied === api.name ? <Check size={14} className="text-tactical-green" /> : <Copy size={14} />}
                </button>
              </div>
            ))}
          </div>
        </Card>

        <Card header="ALERT THRESHOLDS">
          <div className="flex flex-col gap-4">
            <div>
              <label className="font-ui mb-1 block text-xs font-bold uppercase tracking-wider text-sand-muted">
                Temperature Threshold
              </label>
              <div className="flex items-center gap-3">
                <input
                  type="range"
                  min={40}
                  max={80}
                  value={tempThreshold}
                  onChange={(e) => setTempThreshold(Number(e.target.value))}
                  className="flex-1 accent-tactical-orange"
                />
                <span className="font-data min-w-[3rem] text-right text-sm text-tactical-amber">
                  {tempThreshold}°C
                </span>
              </div>
            </div>
            <div>
              <label className="font-ui mb-1 block text-xs font-bold uppercase tracking-wider text-sand-muted">
                Power Drop Threshold
              </label>
              <div className="flex items-center gap-3">
                <input
                  type="range"
                  min={5}
                  max={50}
                  value={powerDropThreshold}
                  onChange={(e) => setPowerDropThreshold(Number(e.target.value))}
                  className="flex-1 accent-tactical-orange"
                />
                <span className="font-data min-w-[3rem] text-right text-sm text-tactical-amber">
                  {powerDropThreshold}%
                </span>
              </div>
            </div>
          </div>
        </Card>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card header="SITE INFO">
          <div className="flex flex-col gap-3">
            <div>
              <label className="font-ui mb-1 block text-xs font-bold uppercase tracking-wider text-sand-muted">
                Site Name
              </label>
              <input
                type="text"
                value={siteName}
                onChange={(e) => setSiteName(e.target.value)}
                className="font-data w-full rounded border border-border-hard bg-surface-mid px-3 py-2 text-sm text-sand-bright focus:border-tactical-amber focus:outline-none"
              />
            </div>
            <div>
              <label className="font-ui mb-1 block text-xs font-bold uppercase tracking-wider text-sand-muted">
                Location
              </label>
              <input
                type="text"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                className="font-data w-full rounded border border-border-hard bg-surface-mid px-3 py-2 text-sm text-sand-bright focus:border-tactical-amber focus:outline-none"
              />
            </div>
            <div>
              <label className="font-ui mb-1 block text-xs font-bold uppercase tracking-wider text-sand-muted">
                Timezone
              </label>
              <input
                type="text"
                value={timezone}
                onChange={(e) => setTimezone(e.target.value)}
                className="font-data w-full rounded border border-border-hard bg-surface-mid px-3 py-2 text-sm text-sand-bright focus:border-tactical-amber focus:outline-none"
              />
            </div>
          </div>
        </Card>

        <Card header="THEME">
          <div className="flex flex-col gap-3">
            <div className="panel flex items-center gap-3 border-tactical-amber bg-surface-mid p-4">
              <div className="flex h-10 w-10 items-center justify-center rounded border border-border-hard bg-void">
                <svg
                  width="18"
                  height="18"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="#ffb703"
                  strokeWidth="3"
                  strokeLinecap="square"
                >
                  <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" />
                </svg>
              </div>
              <div>
                <div className="font-ui text-xs font-bold uppercase tracking-wider text-tactical-amber">
                  Amber CRT Tactical
                </div>
                <div className="font-data mt-0.5 text-[0.65rem] text-sand-muted">
                  Theme locked — military spec
                </div>
              </div>
              <span className="ml-auto font-data text-[0.6rem] uppercase text-tactical-green">Active</span>
            </div>
            <div className="flex items-center gap-3 rounded border border-border-hard bg-surface-mid/50 p-4 opacity-50">
              <div className="flex h-10 w-10 items-center justify-center rounded border border-border-hard bg-surface-dark">
                <span className="font-ui text-xs font-bold text-sand-muted">Aa</span>
              </div>
              <div>
                <div className="font-ui text-xs font-bold uppercase tracking-wider text-sand-muted">
                  Light Mode
                </div>
                <div className="font-data mt-0.5 text-[0.65rem] text-sand-muted">
                  Coming soon — not available in tactical mode
                </div>
              </div>
              <span className="ml-auto font-data text-[0.6rem] uppercase text-sand-muted">Locked</span>
            </div>
            <div className="mt-2">
              <Button variant="primary" size="sm" disabled>
                SAVE CHANGES
              </Button>
            </div>
          </div>
        </Card>
      </div>
    </div>
  )
}
