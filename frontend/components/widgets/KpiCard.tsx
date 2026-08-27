'use client'

import { cn } from '@/lib/utils'
import { TrendingUp, TrendingDown, Minus } from 'lucide-react'

interface KpiCardProps {
  title: string
  label: string
  value: string
  unit?: string
  trend?: 'up' | 'down' | 'neutral'
  alert?: boolean
  className?: string
}

const trendIcons = {
  up: TrendingUp,
  down: TrendingDown,
  neutral: Minus,
}

const trendColors = {
  up: 'text-tactical-green',
  down: 'text-tactical-red',
  neutral: 'text-sand-muted',
}

export default function KpiCard({
  title,
  label,
  value,
  unit,
  trend,
  alert,
  className,
}: KpiCardProps) {
  const TrendIcon = trend ? trendIcons[trend] : null

  return (
      <div
        className={cn(
          'panel relative flex min-w-0 flex-col justify-between p-3 xl:p-4',
          alert && 'animate-pulse-glow border-tactical-orange',
          className,
        )}
      >
      <span
        className={cn(
          'font-data absolute -top-2.5 left-3 z-10 bg-surface-dark px-2 text-[0.65rem] font-bold uppercase tracking-widest',
          alert ? 'text-tactical-orange' : 'text-sand-muted',
        )}
      >
        {title}
      </span>

      <div className="mt-2">
        <span className="font-data text-[0.7rem] uppercase tracking-wider text-sand-muted">
          {label}
        </span>
      </div>

      <div className="mt-1 flex flex-wrap items-baseline gap-x-1 gap-y-0">
        <span className="kpi-value text-tactical-amber" title={`${value} ${unit ?? ''}`.trim()}>
          {value}
        </span>
        {unit && (
          <span className="font-data text-[0.7rem] font-bold leading-none text-tactical-amber">
            {unit}
          </span>
        )}
      </div>

      {trend && TrendIcon && (
        <div className={cn('mt-1 flex items-center gap-1', trendColors[trend])}>
          <TrendIcon size={14} />
          <span className="font-data text-[0.65rem] uppercase">
            {trend === 'up' ? 'INCREASING' : trend === 'down' ? 'DECREASING' : 'STABLE'}
          </span>
        </div>
      )}
    </div>
  )
}
