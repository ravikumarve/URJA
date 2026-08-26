import { API_URL, TOKEN_STORAGE_KEYS } from './config'
import type {
  ApiKey,
  Asset,
  CarbonCredit,
  CurtailmentEvent,
  DispatchDecision,
  HealthAlert,
  HealthScore,
  HourlyTelemetry,
  LoginResponse,
  Paginated,
  PaginationMeta,
  PortfolioSummary,
  RevenueLost,
  Site,
  TelemetryLatest,
  TokenPair,
  User,
} from './types'

// ---------------------------------------------------------------------------
// Token storage (localStorage — pragmatic for self-hosted boilerplate)
// ---------------------------------------------------------------------------

export function getAccessToken(): string | null {
  if (typeof window === 'undefined') return null
  return localStorage.getItem(TOKEN_STORAGE_KEYS.access)
}

export function getRefreshToken(): string | null {
  if (typeof window === 'undefined') return null
  return localStorage.getItem(TOKEN_STORAGE_KEYS.refresh)
}

export function setTokens(access: string, refresh: string): void {
  localStorage.setItem(TOKEN_STORAGE_KEYS.access, access)
  localStorage.setItem(TOKEN_STORAGE_KEYS.refresh, refresh)
}

export function clearTokens(): void {
  localStorage.removeItem(TOKEN_STORAGE_KEYS.access)
  localStorage.removeItem(TOKEN_STORAGE_KEYS.refresh)
}

// ---------------------------------------------------------------------------
// Error type
// ---------------------------------------------------------------------------

export class ApiError extends Error {
  status: number
  detail: string

  constructor(status: number, detail: string) {
    super(detail)
    this.name = 'ApiError'
    this.status = status
    this.detail = detail
  }
}

// ---------------------------------------------------------------------------
// Single-flight refresh — parallel 401s share one refresh call
// ---------------------------------------------------------------------------

let refreshPromise: Promise<boolean> | null = null

async function tryRefresh(): Promise<boolean> {
  const refresh = getRefreshToken()
  if (!refresh) return false

  const res = await fetch(`${API_URL}/v1/auth/refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: refresh }),
  })

  if (!res.ok) {
    clearTokens()
    return false
  }

  const pair = (await res.json()) as TokenPair
  setTokens(pair.access_token, pair.refresh_token)
  return true
}

function refreshSingleFlight(): Promise<boolean> {
  if (!refreshPromise) {
    refreshPromise = tryRefresh().finally(() => {
      refreshPromise = null
    })
  }
  return refreshPromise
}

// ---------------------------------------------------------------------------
// Core fetch wrapper
// ---------------------------------------------------------------------------

async function apiFetch<T>(
  path: string,
  options: RequestInit & { retry?: boolean } = {},
): Promise<T> {
  const { retry = true, ...init } = options

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(init.headers as Record<string, string>),
  }
  const token = getAccessToken()
  if (token) headers['Authorization'] = `Bearer ${token}`

  let res: Response
  try {
    res = await fetch(`${API_URL}${path}`, { ...init, headers })
  } catch {
    throw new ApiError(0, 'Cannot reach the API. Is the backend running?')
  }

  // Access token expired → refresh once, retry the original request.
  if (res.status === 401 && retry && getRefreshToken()) {
    const refreshed = await refreshSingleFlight()
    if (refreshed) return apiFetch<T>(path, { ...options, retry: false })
    if (typeof window !== 'undefined' && window.location.pathname !== '/login') {
      window.location.href = '/login'
    }
    throw new ApiError(401, 'Session expired')
  }

  if (!res.ok) {
    let detail = `Request failed (${res.status})`
    try {
      const body = await res.json()
      if (body?.detail) {
        detail =
          typeof body.detail === 'string'
            ? body.detail
            : JSON.stringify(body.detail)
      }
    } catch {
      /* non-JSON error body */
    }
    throw new ApiError(res.status, detail)
  }

  return (await res.json()) as T
}

// ---------------------------------------------------------------------------
// Endpoint helpers
// ---------------------------------------------------------------------------

export const api = {
  auth: {
    async login(email: string, password: string): Promise<LoginResponse> {
      const data = await apiFetch<LoginResponse>('/v1/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
        retry: false,
      })
      setTokens(data.access_token, data.refresh_token)
      return data
    },

    me(): Promise<User> {
      return apiFetch<User>('/v1/auth/me')
    },

    async logout(): Promise<void> {
      const refresh = getRefreshToken()
      try {
        if (refresh) {
          await apiFetch('/v1/auth/logout', {
            method: 'POST',
            body: JSON.stringify({ refresh_token: refresh }),
            retry: false,
          })
        }
      } finally {
        clearTokens()
      }
    },
  },

  telemetry: {
    latest(): Promise<{ data: TelemetryLatest[] }> {
      return apiFetch('/v1/telemetry/latest')
    },
    hourly(
      assetId: string,
      startISO: string,
      endISO?: string,
    ): Promise<{ data: HourlyTelemetry[]; pagination: PaginationMeta }> {
      const qs = new URLSearchParams({
        asset_id: assetId,
        start_date: startISO,
        aggregation: 'hourly',
      })
      if (endISO) qs.set('end_date', endISO)
      return apiFetch(`/v1/telemetry?${qs.toString()}`)
    },
  },

  health: {
    scores(): Promise<{ data: HealthScore[] }> {
      return apiFetch('/v1/health/scores')
    },
    alerts(params: { status?: string; per_page?: number } = {}): Promise<{
      data: HealthAlert[]
      pagination: PaginationMeta
    }> {
      const qs = new URLSearchParams()
      if (params.status) qs.set('status', params.status)
      if (params.per_page) qs.set('per_page', String(params.per_page))
      const suffix = qs.toString() ? `?${qs.toString()}` : ''
      return apiFetch(`/v1/health/alerts${suffix}`)
    },
  },

  carbon: {
    portfolio(): Promise<PortfolioSummary> {
      return apiFetch('/v1/carbon/portfolio')
    },
    credits(
      params: { status?: string; per_page?: number } = {},
    ): Promise<{ data: CarbonCredit[]; pagination: PaginationMeta }> {
      const qs = new URLSearchParams()
      if (params.status) qs.set('status', params.status)
      if (params.per_page) qs.set('per_page', String(params.per_page))
      const suffix = qs.toString() ? `?${qs.toString()}` : ''
      return apiFetch(`/v1/carbon/credits${suffix}`)
    },
  },

  assets: {
    list(params: { page?: number; page_size?: number } = {}): Promise<Paginated<Asset>> {
      const qs = new URLSearchParams()
      if (params.page) qs.set('page', String(params.page))
      if (params.page_size) qs.set('page_size', String(params.page_size))
      const suffix = qs.toString() ? `?${qs.toString()}` : ''
      return apiFetch(`/v1/assets${suffix}`)
    },
    sites(params: { page_size?: number } = {}): Promise<Paginated<Site>> {
      const qs = new URLSearchParams()
      if (params.page_size) qs.set('page_size', String(params.page_size))
      const suffix = qs.toString() ? `?${qs.toString()}` : ''
      return apiFetch(`/v1/sites${suffix}`)
    },
  },

  dispatch: {
    decisions(
      params: { per_page?: number } = {},
    ): Promise<{ data: DispatchDecision[]; pagination: PaginationMeta }> {
      const qs = new URLSearchParams()
      if (params.per_page) qs.set('per_page', String(params.per_page))
      const suffix = qs.toString() ? `?${qs.toString()}` : ''
      return apiFetch(`/v1/dispatch/decisions${suffix}`)
    },
    curtailmentEvents(
      params: { per_page?: number } = {},
    ): Promise<{ data: CurtailmentEvent[]; pagination: PaginationMeta }> {
      const qs = new URLSearchParams()
      if (params.per_page) qs.set('per_page', String(params.per_page))
      const suffix = qs.toString() ? `?${qs.toString()}` : ''
      return apiFetch(`/v1/curtailment/events${suffix}`)
    },
    revenueLost(days = 30): Promise<RevenueLost> {
      const start = new Date(Date.now() - days * 86_400_000)
        .toISOString()
        .split('T')[0]
      return apiFetch(`/v1/curtailment/revenue-lost?start_date=${start}`)
    },
  },

  settings: {
    apiKeys(): Promise<ApiKey[]> {
      return apiFetch('/v1/auth/api-keys')
    },
    users(params: { page?: number; page_size?: number } = {}): Promise<
      Paginated<User>
    > {
      const qs = new URLSearchParams()
      if (params.page) qs.set('page', String(params.page))
      if (params.page_size) qs.set('page_size', String(params.page_size))
      const suffix = qs.toString() ? `?${qs.toString()}` : ''
      return apiFetch(`/v1/auth/users${suffix}`)
    },
  },
}
