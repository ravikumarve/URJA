// Shared API types — mirrors backend/app/schemas/*

export interface User {
  id: string
  email: string
  display_name: string
  role: string
  is_active: boolean
  organization_id: string
  last_login_at: string | null
  created_at: string
}

export interface LoginResponse {
  user: User
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

export interface TokenPair {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface TelemetryLatest {
  asset_id: string
  asset_name: string
  asset_type: string
  site_name: string
  ts: string
  generation_kw: number
  energy_kwh: number
  temperature_c: number
  health_score: number
  status: string
}

export type AlertSeverity = 'critical' | 'warning' | 'info'

export interface HealthAlert {
  id: string
  asset_id: string
  asset_name: string
  site_name: string
  title: string
  description: string
  severity: AlertSeverity
  status: string
  acknowledged_by: string | null
  acknowledged_at: string | null
  resolved_at: string | null
  created_at: string
}

export interface PaginationMeta {
  has_more: boolean
  total: number
}

export interface PortfolioSummary {
  total_issued: number
  total_retired: number
  total_cancelled: number
  total_available: number
  total_co2e_issued: number
  total_co2e_retired: number
  by_status: Record<string, number>
  by_methodology: Record<string, number>
  last_issuance: string | null
  next_eligible_date: string
}
