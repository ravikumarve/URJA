import { api } from './api'

export interface DuckPoint {
  hour: string
  mw: number
}

const MAX_ASSETS = 50 // protect CPU-bound host from unbounded request fan-out

/**
 * Fleet generation curve for today, local time.
 * GET /v1/telemetry is single-asset, so we fan out hourly queries across
 * assets and sum avg_kw per UTC-hour bucket. Fails soft: individual asset
 * failures are skipped; total failure yields an empty curve (caller renders
 * an empty state rather than an error panel).
 */
export async function fetchTodayDuckCurve(assetIds: string[]): Promise<DuckPoint[]> {
  if (assetIds.length === 0) return []

  const now = new Date()
  const start = new Date(now)
  start.setHours(0, 0, 0, 0)

  const results = await Promise.allSettled(
    assetIds
      .slice(0, MAX_ASSETS)
      .map((id) => api.telemetry.hourly(id, start.toISOString(), now.toISOString())),
  )

  const sumsByHour = new Map<number, number>()
  for (const result of results) {
    if (result.status !== 'fulfilled') continue
    for (const row of result.value.data) {
      const h = new Date(row.bucket).getHours()
      sumsByHour.set(h, (sumsByHour.get(h) ?? 0) + Number(row.avg_kw ?? 0))
    }
  }

  const currentHour = now.getHours()
  const points: DuckPoint[] = []
  for (let h = 0; h <= currentHour; h++) {
    const kw = sumsByHour.get(h) ?? 0
    points.push({
      hour: String(h).padStart(2, '0'),
      mw: Math.round((kw / 1000) * 10) / 10,
    })
  }
  return points
}
