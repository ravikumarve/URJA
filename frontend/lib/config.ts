export const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

export const TOKEN_STORAGE_KEYS = {
  access: 'urja_access_token',
  refresh: 'urja_refresh_token',
} as const
