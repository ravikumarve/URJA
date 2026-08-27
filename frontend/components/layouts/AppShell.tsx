'use client'

import { useEffect, useMemo, useState } from 'react'
import { usePathname, useRouter } from 'next/navigation'
import Sidebar from './Sidebar'
import TopBar from './TopBar'
import { useAuth } from '@/lib/auth-context'

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
  const router = useRouter()
  const { status } = useAuth()
  const [sidebarOpen, setSidebarOpen] = useState(false)

  const isLoginPage = pathname === '/login'

  // Auth guard — unauthenticated users never see app routes.
  useEffect(() => {
    if (!isLoginPage && status === 'unauthenticated') {
      router.replace('/login')
    }
  }, [isLoginPage, status, router])

  const pageTitle = useMemo(() => {
    if (pathname === '/') return routeTitles['/']
    const matched = Object.entries(routeTitles).find(([route]) =>
      pathname.startsWith(route),
    )
    return matched ? matched[1] : 'URJA'
  }, [pathname])

  // Login renders full-screen, outside the command-center chrome.
  if (isLoginPage) {
    return (
      <div className="h-screen overflow-y-auto bg-void">{children}</div>
    )
  }

  if (status !== 'authenticated') {
    return (
      <div className="flex h-screen items-center justify-center bg-void">
        <p className="font-data animate-pulse text-xs uppercase tracking-[3px] text-tactical-amber">
          {status === 'loading' ? '// AUTHENTICATING…' : '// REDIRECTING TO LOGIN…'}
        </p>
      </div>
    )
  }

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

        <main className="flex-1 overflow-y-auto bg-void p-4 pb-8 scroll-pt-4">
          {children}
        </main>
      </div>
    </div>
  )
}
