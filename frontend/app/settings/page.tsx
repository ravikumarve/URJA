'use client'

import { useCallback, useState } from 'react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { EmptyState, ErrorPanel, SkeletonRows } from '@/components/widgets/states'
import { api, ApiError } from '@/lib/api'
import type { ApiKey, User } from '@/lib/types'
import { useApiData } from '@/lib/use-api-data'
import { cn } from '@/lib/utils'

interface SettingsData {
  keys: ApiKey[] | null // null = admin required
  users: User[] | null // null = admin required
}

function fmtDate(iso: string | null): string {
  if (!iso) return '—'
  const d = new Date(iso)
  return Number.isNaN(d.getTime()) ? '—' : d.toISOString().split('T')[0]
}

export default function Settings() {
  const [copied, setCopied] = useState<string | null>(null)

  const fetcher = useCallback(async (): Promise<SettingsData> => {
    const [keysRes, usersRes] = await Promise.allSettled([
      api.settings.apiKeys(),
      api.settings.users({ page_size: 50 }),
    ])
    return {
      keys:
        keysRes.status === 'fulfilled'
          ? keysRes.value
          : keysRes.reason instanceof ApiError && keysRes.reason.status === 403
            ? null
            : (() => {
                throw keysRes.reason
              })(),
      users:
        usersRes.status === 'fulfilled'
          ? usersRes.value.items
          : usersRes.reason instanceof ApiError && usersRes.reason.status === 403
            ? null
            : (() => {
                throw usersRes.reason
              })(),
    }
  }, [])

  const { state, reload } = useApiData(fetcher)

  const handleCopy = async (key: ApiKey) => {
    try {
      await navigator.clipboard.writeText(key.key_prefix)
      setCopied(key.id)
      setTimeout(() => setCopied(null), 2000)
    } catch {
      /* clipboard unavailable */
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <h1 className="font-ui text-lg font-bold uppercase tracking-wider text-sand-bright">
        SETTINGS & CONFIG
      </h1>

      {state.phase === 'loading' && (
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          <div className="panel p-4"><SkeletonRows rows={4} /></div>
          <div className="panel p-4"><SkeletonRows rows={4} /></div>
        </div>
      )}

      {state.phase === 'error' && (
        <ErrorPanel message={state.message} onRetry={reload} />
      )}

      {state.phase === 'ready' && (
        <>
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            {/* API KEYS — admin only */}
            <Card header="API KEYS">
              {state.data.keys === null ? (
                <EmptyState label="ADMIN ROLE REQUIRED TO VIEW API KEYS" />
              ) : state.data.keys.length === 0 ? (
                <EmptyState label="NO API KEYS — CREATE ONE VIA POST /V1/AUTH/API-KEYS" />
              ) : (
                <div className="flex flex-col gap-3">
                  {state.data.keys.map((key) => (
                    <div
                      key={key.id}
                      className="flex items-center justify-between rounded border border-border-hard bg-surface-mid p-3"
                    >
                      <div className="min-w-0 flex-1">
                        <div className="font-ui flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-sand-muted">
                          {key.name}
                          <span
                            className={cn(
                              'rounded px-1.5 py-0.5 text-[0.55rem]',
                              key.is_active
                                ? 'bg-tactical-green/10 text-tactical-green'
                                : 'bg-tactical-red/10 text-tactical-red',
                            )}
                          >
                            {key.is_active ? 'ACTIVE' : 'REVOKED'}
                          </span>
                        </div>
                        <div className="font-data mt-1 truncate text-sm text-sand-bright">
                          <span className="text-tactical-amber">{key.key_prefix}</span>
                          …
                        </div>
                        <div className="font-data mt-1 text-[0.6rem] uppercase text-sand-muted">
                          scope: {key.scope} · last used:{' '}
                          {key.last_used_at ? fmtDate(key.last_used_at) : 'never'} · expires:{' '}
                          {fmtDate(key.expires_at)}
                        </div>
                      </div>
                      <button
                        onClick={() => void handleCopy(key)}
                        aria-label={`Copy prefix of ${key.name}`}
                        className="ml-3 shrink-0 rounded border border-border-hard p-2 text-sand-muted hover:border-sand-muted hover:text-sand-bright"
                      >
                        {copied === key.id ? (
                          <span className="font-data text-[0.6rem] text-tactical-green">
                            COPIED
                          </span>
                        ) : (
                          <span className="font-data text-[0.6rem]">COPY</span>
                        )}
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </Card>

            {/* TEAM USERS — admin only */}
            <Card header="TEAM">
              {state.data.users === null ? (
                <EmptyState label="ADMIN ROLE REQUIRED TO VIEW USERS" />
              ) : state.data.users.length === 0 ? (
                <EmptyState label="NO USERS" />
              ) : (
                <div className="overflow-x-auto">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>User</th>
                        <th>Role</th>
                        <th>Status</th>
                        <th>Last Login</th>
                      </tr>
                    </thead>
                    <tbody>
                      {state.data.users.map((u) => (
                        <tr key={u.id}>
                          <td>
                            <div className="font-bold text-tactical-amber">
                              {u.display_name}
                            </div>
                            <div className="text-[0.65rem] text-sand-muted">{u.email}</div>
                          </td>
                          <td className="uppercase text-sand-muted">{u.role}</td>
                          <td>
                            <span
                              className={cn(
                                'font-bold',
                                u.is_active ? 'text-tactical-green' : 'text-tactical-red',
                              )}
                            >
                              {u.is_active ? 'ACTIVE' : 'DISABLED'}
                            </span>
                          </td>
                          <td className="text-sand-muted">
                            {u.last_login_at ? fmtDate(u.last_login_at) : 'never'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </Card>
          </div>

          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            <Card header="SITE INFO">
              <p className="font-data p-2 text-xs leading-relaxed text-sand-muted">
                Site metadata is managed via the backend —{' '}
                <span className="text-tactical-amber">PUT /v1/sites/{'{site_id}'}</span>.
                The current build reads sites live on the Assets page.
              </p>
            </Card>

            <Card header="THEME">
              <div className="flex flex-col gap-3">
                <div className="panel flex items-center gap-3 border-tactical-amber bg-surface-mid p-4">
                  <div className="flex h-10 w-10 items-center justify-center rounded border border-border-hard bg-void">
                    <svg
                      width="18"
                      height="18"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="#ffb703"
                      strokeWidth="3"
                      strokeLinecap="square"
                    >
                      <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" />
                    </svg>
                  </div>
                  <div>
                    <div className="font-ui text-xs font-bold uppercase tracking-wider text-tactical-amber">
                      Amber CRT Tactical
                    </div>
                    <div className="font-data mt-0.5 text-[0.65rem] text-sand-muted">
                      Theme locked — military spec
                    </div>
                  </div>
                  <span className="ml-auto font-data text-[0.6rem] uppercase text-tactical-green">
                    Active
                  </span>
                </div>
                <div className="mt-2">
                  <Button variant="primary" size="sm" disabled>
                    SAVE CHANGES
                  </Button>
                </div>
              </div>
            </Card>
          </div>
        </>
      )}
    </div>
  )
}
