import { api } from './api'

export interface DuckPoint {
  hour: string
  mw: number
  /** Grid price ₹/kWh for this hour — present when site pricing data exists. */
  price?: number
}

const MAX_ASSETS = 50 // protect CPU-bound host from unbounded request fan-out

/**
 * Fleet generation curve for today, local time — with optional grid-price
 * overlay for the primary site.
 *
 * GET /v1/telemetry is single-asset, so we fan out hourly queries across
 * assets and sum avg_kw per UTC-hour bucket. Prices come from
 * GET /v1/pricing (site-scoped). Both fail soft: individual failures are
 * skipped; a total pricing failure just omits the overlay.
 */
export async function fetchTodayDuckCurve(
  assetIds: string[],
  siteId?: string | null,
): Promise<DuckPoint[]> {
  if (assetIds.length === 0) return []

  const now = new Date()
  const start = new Date(now)
  start.setHours(0, 0, 0, 0)
  const startISO = start.toISOString()
  const endISO = now.toISOString()

  const [genResults, priceResult] = await Promise.all([
    Promise.allSettled(
      assetIds
        .slice(0, MAX_ASSETS)
        .map((id) => api.telemetry.hourly(id, startISO, endISO)),
    ),
    siteId
      ? api.pricing.hourly(siteId, startISO, endISO).catch(() => null)
      : Promise.resolve(null),
  ])

  const sumsByHour = new Map<number, number>()
  for (const result of genResults) {
    if (result.status !== 'fulfilled') continue
    for (const row of result.value.data) {
      const h = new Date(row.bucket).getHours()
      sumsByHour.set(h, (sumsByHour.get(h) ?? 0) + Number(row.avg_kw ?? 0))
    }
  }

  const priceByHour = new Map<number, number>()
  if (priceResult) {
    for (const row of priceResult.data) {
      const h = new Date(row.bucket).getHours()
      priceByHour.set(h, Number(row.avg_price ?? 0))
    }
  }

  const currentHour = now.getHours()
  const points: DuckPoint[] = []
  for (let h = 0; h <= currentHour; h++) {
    const kw = sumsByHour.get(h) ?? 0
    const point: DuckPoint = {
      hour: String(h).padStart(2, '0'),
      mw: Math.round((kw / 1000) * 10) / 10,
    }
    const price = priceByHour.get(h)
    if (price !== undefined) point.price = Math.round(price * 100) / 100
    points.push(point)
  }
  return points
}
