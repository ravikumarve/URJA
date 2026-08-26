'use client'

import { AlertTriangle, RefreshCw } from 'lucide-react'

export function ErrorPanel({
  message,
  onRetry,
}: {
  message: string
  onRetry: () => void
}) {
  return (
    <div className="panel flex flex-col items-center gap-4 p-10 text-center">
      <AlertTriangle size={28} className="text-tactical-red" />
      <p className="font-data text-sm text-tactical-red">[!] {message}</p>
      <button
        onClick={onRetry}
        className="font-data flex items-center gap-2 rounded border border-border-hard px-4 py-2 text-xs uppercase tracking-wider text-sand-bright transition-colors hover:border-tactical-amber hover:text-tactical-amber"
      >
        <RefreshCw size={13} /> RETRY
      </button>
    </div>
  )
}

export function SkeletonRows({ rows = 6 }: { rows?: number }) {
  return (
    <div className="flex flex-col gap-2">
      {Array.from({ length: rows }).map((_, i) => (
        <div
          key={i}
          className="h-8 animate-pulse rounded bg-surface-light opacity-40"
        />
      ))}
    </div>
  )
}

export function SkeletonPanels({ count = 4 }: { count?: number }) {
  return (
    <section className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="panel h-[92px] animate-pulse opacity-40" />
      ))}
    </section>
  )
}

export function EmptyState({ label }: { label: string }) {
  return (
    <p className="font-data py-8 text-center text-xs uppercase tracking-wider text-sand-muted">
      {label}
    </p>
  )
}
