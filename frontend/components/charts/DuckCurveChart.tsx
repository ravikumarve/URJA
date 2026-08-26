'use client'

import {
  Area,
  CartesianGrid,
  ComposedChart,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { EmptyState } from '@/components/widgets/states'
import type { DuckPoint } from '@/lib/duck-curve'

interface DuckCurveChartProps {
  data: DuckPoint[]
}

/**
 * Live generation curve with optional grid-price overlay.
 *
 * NOTE: children must be DIRECT descendants of ComposedChart — Recharts 2.x
 * does not traverse JSX fragments when collecting axis/series children, and a
 * fragment-wrapped child list renders an empty surface. Conditionals stay
 * inline ({hasPrice && ...}) which Recharts handles natively.
 */
export default function DuckCurveChart({ data }: DuckCurveChartProps) {
  if (data.length === 0) {
    return <EmptyState label="No telemetry ingested today" />
  }

  const hasPrice = data.some((p) => p.price !== undefined)

  return (
    <ResponsiveContainer width="100%" height={300}>
      <ComposedChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
        <defs>
          <linearGradient id="actualFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#ffb703" stopOpacity={0.3} />
            <stop offset="100%" stopColor="#ffb703" stopOpacity={0.05} />
          </linearGradient>
        </defs>

        <CartesianGrid stroke="#2c2723" strokeWidth={1} />

        <XAxis
          dataKey="hour"
          tick={{ fill: '#8c7b6b', fontFamily: 'JetBrains Mono', fontSize: 11 }}
          tickLine={{ stroke: '#3a332d' }}
          axisLine={{ stroke: '#3a332d' }}
        />

        <YAxis
          yAxisId="left"
          tick={{ fill: '#8c7b6b', fontFamily: 'JetBrains Mono', fontSize: 11 }}
          tickLine={false}
          axisLine={{ stroke: '#3a332d' }}
          label={{
            value: 'MW',
            angle: -90,
            position: 'insideLeft',
            style: { fill: '#8c7b6b', fontFamily: 'JetBrains Mono', fontSize: 11 },
          }}
        />

        {hasPrice && (
          <YAxis
            yAxisId="right"
            orientation="right"
            tick={{ fill: '#ff5e00', fontFamily: 'JetBrains Mono', fontSize: 11 }}
            tickLine={false}
            axisLine={false}
            domain={[0, 'auto']}
            label={{
              value: '₹/kWh',
              angle: 90,
              position: 'insideRight',
              style: { fill: '#ff5e00', fontFamily: 'JetBrains Mono', fontSize: 11 },
            }}
          />
        )}

        <Tooltip
          contentStyle={{
            background: '#1c1a17',
            border: '2px solid #3a332d',
            borderRadius: 0,
            fontFamily: 'JetBrains Mono',
            fontSize: 12,
            color: '#d9cdbd',
          }}
          labelStyle={{ color: '#ffb703', fontWeight: 700 }}
        />

        <Area
          yAxisId="left"
          type="monotone"
          dataKey="mw"
          stroke="#ffb703"
          strokeWidth={2}
          fill="url(#actualFill)"
          dot={false}
          isAnimationActive={false}
        />

        {hasPrice && (
          <Line
            yAxisId="right"
            type="monotone"
            dataKey="price"
            stroke="#ff5e00"
            strokeWidth={1.5}
            dot={false}
            isAnimationActive={false}
          />
        )}
      </ComposedChart>
    </ResponsiveContainer>
  )
}
