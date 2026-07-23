'use client'

import { useState, useMemo } from 'react'
import { usePathname } from 'next/navigation'
import Sidebar from './Sidebar'
import TopBar from './TopBar'

const routeTitles: Record<string, string> = {
  '/': 'TACTICAL COMMAND CENTER',
  '/assets': 'ASSET COMMAND MODULE',
  '/yield': 'YIELD DISPATCH SYSTEM',
  '/carbon': 'CARBON VAULT',
  '/health': 'HEALTH MONITOR',
  '/settings': 'SYSTEM CONFIGURATION',
}

interface AppShellProps {
  children: React.ReactNode
}

export default function AppShell({ children }: AppShellProps) {
  const pathname = usePathname()
  const [sidebarOpen, setSidebarOpen] = useState(false)

  const pageTitle = useMemo(() => {
    if (pathname === '/') return routeTitles['/']
    const matched = Object.entries(routeTitles).find(([route]) =>
      pathname.startsWith(route),
    )
    return matched ? matched[1] : 'URJA'
  }, [pathname])

  return (
    <div className="flex h-screen overflow-hidden bg-void">
      <Sidebar
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />

      <div className="flex flex-1 flex-col md:ml-64">
        <TopBar
          title={pageTitle}
          onMenuToggle={() => setSidebarOpen((prev) => !prev)}
        />

        <main className="flex-1 overflow-y-auto bg-void p-4">
          {children}
        </main>
      </div>
    </div>
  )
}
