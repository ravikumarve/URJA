'use client'

import { Menu } from 'lucide-react'

interface TopBarProps {
  title: string
  onMenuToggle: () => void
}

export default function TopBar({ title, onMenuToggle }: TopBarProps) {
  return (
    <header className="flex h-[50px] shrink-0 items-center justify-between border-b-2 border-surface-light bg-surface-dark px-4">
      <div className="flex items-center gap-3">
        <button
          onClick={onMenuToggle}
          className="text-sand-muted hover:text-sand-bright md:hidden"
          aria-label="Toggle menu"
        >
          <Menu size={20} />
        </button>
        <h1 className="font-ui text-sm font-bold uppercase tracking-[2px] text-sand-bright">
          {title}
        </h1>
      </div>

      <div className="font-data flex items-center gap-5 text-xs text-sand-muted">
        <span>
          SITE: <strong className="text-sand-bright">ALPHA-DESERT-01</strong>
        </span>
        <span>
          OP_MODE: <strong className="text-tactical-amber">TACTICAL</strong>
        </span>
        <span className="flex items-center gap-1.5 text-tactical-orange">
          <span className="inline-block h-2 w-2 rounded-full bg-tactical-orange animate-blink" />
          [⚠] ANOMALY
        </span>
      </div>
    </header>
  )
}
