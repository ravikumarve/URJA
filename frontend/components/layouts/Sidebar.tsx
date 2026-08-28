'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import {
  LayoutDashboard,
  Sun,
  Zap,
  Leaf,
  HeartPulse,
  Settings,
  type LucideIcon,
} from 'lucide-react'
import { cn } from '@/lib/utils'

interface NavItem {
  href: string
  label: string
  icon: LucideIcon
}

const navItems: NavItem[] = [
  { href: '/', label: 'Overview', icon: LayoutDashboard },
  { href: '/assets', label: 'Assets', icon: Sun },
  { href: '/yield', label: 'Yield Dispatch', icon: Zap },
  { href: '/carbon', label: 'Carbon Vault', icon: Leaf },
  { href: '/health', label: 'Health', icon: HeartPulse },
  { href: '/settings', label: 'Settings', icon: Settings },
]

interface SidebarProps {
  isOpen: boolean
  onClose: () => void
}

export default function Sidebar({ isOpen, onClose }: SidebarProps) {
  const pathname = usePathname()

  return (
    <>
      {isOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/60 md:hidden"
          onClick={onClose}
        />
      )}

      <aside
        className={cn(
          'fixed left-0 top-0 z-40 flex h-full w-64 flex-col border-r-2 border-border-hard bg-surface-dark transition-transform duration-200 md:translate-x-0',
          isOpen ? 'translate-x-0' : '-translate-x-full',
        )}
      >
        <div className="flex items-center gap-3 border-b-2 border-border-hard px-5 py-4">
          <svg
            width="22"
            height="22"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="3"
            strokeLinecap="square"
            className="text-tactical-amber"
          >
            <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" />
          </svg>
          <span
            className="font-ui text-lg font-bold uppercase tracking-[2px] text-tactical-amber"
          >
            URJA
          </span>
        </div>

        <nav className="flex flex-1 flex-col gap-1 px-3 py-4">
          {navItems.map((item) => {
            const isActive =
              item.href === '/' ? pathname === '/' : pathname.startsWith(item.href)
            const Icon = item.icon

            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={onClose}
                className={cn(
                  'font-data flex items-center gap-3 rounded-sm px-3 py-2.5 text-xs uppercase tracking-wider transition-all',
                  isActive
                    ? 'border-l-2 border-tactical-amber bg-tactical-amber/10 pl-[10px] font-bold text-tactical-amber'
                    : 'border-l-2 border-transparent text-sand-muted hover:bg-surface-light hover:text-sand-bright',
                )}
              >
                <Icon size={16} />
                <span>{item.label}</span>
              </Link>
            )
          })}
        </nav>

        <div className="border-t-2 border-border-hard px-5 py-3 font-data text-xs text-sand-muted">
          v1.0.0
        </div>
      </aside>
    </>
  )
}
