'use client'

import { useCallback, useEffect, useState } from 'react'
import { ApiError } from './api'

export type ApiState<T> =
  | { phase: 'loading' }
  | { phase: 'error'; message: string }
  | { phase: 'ready'; data: T }

/**
 * Shared fetch-state machine for module pages:
 * loading → ready | error, with manual reload.
 * The fetcher must be stable (useCallback / module fn).
 */
export function useApiData<T>(fetcher: () => Promise<T>) {
  const [state, setState] = useState<ApiState<T>>({ phase: 'loading' })
  const [tick, setTick] = useState(0)

  useEffect(() => {
    let cancelled = false
    setState({ phase: 'loading' })
    fetcher()
      .then((data) => {
        if (!cancelled) setState({ phase: 'ready', data })
      })
      .catch((err) => {
        if (!cancelled) {
          setState({
            phase: 'error',
            message:
              err instanceof ApiError
                ? err.detail
                : 'Failed to load data. Check your connection.',
          })
        }
      })
    return () => {
      cancelled = true
    }
  }, [fetcher, tick])

  const reload = useCallback(() => setTick((t) => t + 1), [])

  return { state, reload }
}
