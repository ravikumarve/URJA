'use client'

import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Line,
  ComposedChart,
} from 'recharts'

const data = [
  { hour: '00', actual: 0, expected: 0, gridPrice: 2.1 },
  { hour: '01', actual: 0, expected: 0, gridPrice: 1.8 },
  { hour: '02', actual: 0, expected: 0, gridPrice: 1.5 },
  { hour: '03', actual: 0, expected: 0, gridPrice: 1.4 },
  { hour: '04', actual: 0.2, expected: 0, gridPrice: 1.6 },
  { hour: '05', actual: 2.1, expected: 1.5, gridPrice: 2.0 },
  { hour: '06', actual: 5.8, expected: 5.2, gridPrice: 2.3 },
  { hour: '07', actual: 10.4, expected: 11.0, gridPrice: 2.4 },
  { hour: '08', actual: 15.2, expected: 16.1, gridPrice: 2.5 },
  { hour: '09', actual: 21.6, expected: 22.8, gridPrice: 2.6 },
  { hour: '10', actual: 26.3, expected: 28.5, gridPrice: 2.7 },
  { hour: '11', actual: 29.8, expected: 32.0, gridPrice: 2.8 },
  { hour: '12', actual: 31.2, expected: 33.4, gridPrice: 2.8 },
  { hour: '13', actual: 30.5, expected: 32.8, gridPrice: 2.9 },
  { hour: '14', actual: 28.1, expected: 31.2, gridPrice: 3.1 },
  { hour: '15', actual: 24.6, expected: 27.5, gridPrice: 3.4 },
  { hour: '16', actual: 19.3, expected: 22.0, gridPrice: 3.8 },
  { hour: '17', actual: 12.7, expected: 15.4, gridPrice: 4.2 },
  { hour: '18', actual: 6.4, expected: 8.2, gridPrice: 4.8 },
  { hour: '19', actual: 2.1, expected: 3.0, gridPrice: 5.2 },
  { hour: '20', actual: 0.5, expected: 1.0, gridPrice: 5.5 },
  { hour: '21', actual: 0, expected: 0, gridPrice: 5.0 },
  { hour: '22', actual: 0, expected: 0, gridPrice: 4.2 },
  { hour: '23', actual: 0, expected: 0, gridPrice: 3.0 },
]

export default function DuckCurveChart() {
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

        <YAxis
          yAxisId="right"
          orientation="right"
          tick={{ fill: '#ff5e00', fontFamily: 'JetBrains Mono', fontSize: 11 }}
          tickLine={false}
          axisLine={false}
          label={{
            value: '₹/kWh',
            angle: 90,
            position: 'insideRight',
            style: { fill: '#ff5e00', fontFamily: 'JetBrains Mono', fontSize: 11 },
          }}
        />

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
          dataKey="expected"
          stroke="#3a332d"
          strokeWidth={1.5}
          strokeDasharray="4 4"
          fill="none"
          dot={false}
        />

        <Area
          yAxisId="left"
          type="monotone"
          dataKey="actual"
          stroke="#ffb703"
          strokeWidth={2}
          fill="url(#actualFill)"
          dot={false}
        />

        <Line
          yAxisId="right"
          type="monotone"
          dataKey="gridPrice"
          stroke="#ff5e00"
          strokeWidth={1.5}
          dot={false}
        />
      </ComposedChart>
    </ResponsiveContainer>
  )
}
