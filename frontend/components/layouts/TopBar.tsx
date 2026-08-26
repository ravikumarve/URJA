'use client'

import { Menu, LogOut } from 'lucide-react'
import { useAuth } from '@/lib/auth-context'

interface TopBarProps {
  title: string
  onMenuToggle: () => void
}

export default function TopBar({ title, onMenuToggle }: TopBarProps) {
  const { user, logout } = useAuth()

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
          OP_MODE: <strong className="text-tactical-amber">TACTICAL</strong>
        </span>
        <span className="hidden sm:inline">
          OPERATOR:{' '}
          <strong className="text-sand-bright">
            {user?.display_name ?? '—'}
          </strong>
        </span>
        <button
          onClick={() => void logout()}
          title={`Sign out ${user?.email ?? ''}`}
          aria-label="Sign out"
          className="flex items-center gap-1.5 text-tactical-orange transition-colors hover:text-tactical-red"
        >
          <LogOut size={13} />
          <span className="hidden sm:inline">LOGOUT</span>
        </button>
      </div>
    </header>
  )
}
