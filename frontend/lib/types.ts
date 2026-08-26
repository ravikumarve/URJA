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

export interface HourlyTelemetry {
  bucket: string
  asset_id: string
  avg_kw: number
  peak_kw: number
  min_kw: number
  energy_kwh: number
  reading_count: number
}

export interface HourlyPrice {
  bucket: string
  site_id: string
  avg_price: number
  min_price: number
  max_price: number
  currency: string
  reading_count: number
}

export interface LatestPrice {
  ts: string
  site_id: string
  price_per_kwh: number
  currency: string
  source: string
  is_forecast: boolean
  market_region: string | null
}



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

// --- Assets / Sites ---------------------------------------------------------

export interface Asset {
  id: string
  site_id: string
  parent_asset_id: string | null
  asset_type: string
  name: string
  code: string
  serial_number: string | null
  manufacturer: string | null
  model: string | null
  capacity_kw: number | null
  latitude: number | null
  longitude: number | null
  commissioning_date: string | null
  status: string
  health_score: number | null
  created_at: string
  updated_at: string
}

export interface Site {
  id: string
  name: string
  code: string
  description: string | null
  address: string | null
  latitude: number | null
  longitude: number | null
  capacity_mw: number
  timezone: string
  status: string
  asset_count: number
  created_at: string
  updated_at: string
}

export interface Paginated<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

// --- Dispatch / Curtailment -------------------------------------------------

export interface DispatchDecision {
  id: string
  rule_name: string | null
  asset_name: string | null
  status: string
  action_taken: string
  action_params: Record<string, unknown>
  triggered_value: number | null
  expected_outcome: string | null
  actual_outcome: string | null
  duration_seconds: number | null
  executed_at: string | null
  created_at: string
}

export interface CurtailmentEvent {
  event_id: string
  asset_id: string
  asset_name: string
  site_name: string
  ts: string
  duration_minutes: number
  expected_kwh: number
  actual_kwh: number
  curtailed_kwh: number
  price_per_kwh: number
  revenue_lost: number
  grid_price_source: string
  is_resolved: boolean
  resolved_at: string | null
}

export interface RevenueLost {
  total_curtailed: number
  total_revenue: number
  event_count: number
  avg_price: number
}

// --- Carbon -----------------------------------------------------------------

export interface CarbonCredit {
  credit_id: string
  batch_id: string
  asset_id: string
  asset_name: string | null
  status: string
  quantity: number
  unit: string
  methodology: string
  generation_start: string
  generation_end: string
  total_kwh: number
  emission_factor: number
  registry_tx_id: string | null
  registry_url: string | null
  issued_by: string | null
  retired_at: string | null
  notes: string | null
  created_at: string
}

// --- Health -----------------------------------------------------------------

export interface HealthScore {
  asset_id: string
  asset_name: string
  asset_type: string
  site_name: string
  health_score: number
  anomaly_score: number
  trend: string
  metric_scores: Record<string, number>
  anomaly_flags: string[]
  last_checked_at: string
}

// --- Settings ---------------------------------------------------------------

export interface ApiKey {
  id: string
  key_prefix: string
  name: string
  scope: string
  expires_at: string | null
  last_used_at: string | null
  is_active: boolean
  created_at: string
}
