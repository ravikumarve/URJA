'use client'

import { useState, type FormEvent } from 'react'
import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { ApiError } from '@/lib/api'
import { useAuth } from '@/lib/auth-context'

export default function Login() {
  const router = useRouter()
  const { login } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      await login(email.trim(), password)
      router.replace('/')
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.detail
          : 'Sign-in failed. Check your connection and try again.',
      )
      setSubmitting(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center p-4">
      <div className="panel w-full max-w-sm p-8">
        <div className="mb-8 flex flex-col items-center gap-3">
          <div className="flex items-center gap-3">
            <svg
              width="32"
              height="32"
              viewBox="0 0 24 24"
              fill="none"
              stroke="#ff5e00"
              strokeWidth="3"
              strokeLinecap="square"
            >
              <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" />
            </svg>
            <span className="font-ui text-2xl font-bold uppercase tracking-[3px] text-tactical-amber">
              URJA
            </span>
          </div>
          <p className="font-data text-xs uppercase tracking-wider text-sand-muted">
            Deploy clean energy intelligence.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div>
            <label
              htmlFor="email"
              className="font-ui mb-1 block text-xs font-bold uppercase tracking-wider text-sand-muted"
            >
              Email
            </label>
            <input
              id="email"
              type="email"
              required
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="ops@example.com"
              className="font-data w-full rounded border border-border-hard bg-surface-mid px-3 py-2.5 text-sm text-sand-bright placeholder:text-sand-muted focus:border-tactical-amber focus:outline-none"
            />
          </div>
          <div>
            <label
              htmlFor="password"
              className="font-ui mb-1 block text-xs font-bold uppercase tracking-wider text-sand-muted"
            >
              Password
            </label>
            <input
              id="password"
              type="password"
              required
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="font-data w-full rounded border border-border-hard bg-surface-mid px-3 py-2.5 text-sm text-sand-bright placeholder:text-sand-muted focus:border-tactical-amber focus:outline-none"
            />
          </div>

          {error && (
            <p
              role="alert"
              className="font-data rounded border border-tactical-red/40 bg-tactical-red/10 px-3 py-2 text-xs text-tactical-red"
            >
              [!] {error}
            </p>
          )}

          <Button
            type="submit"
            variant="primary"
            size="lg"
            disabled={submitting}
            className="mt-2 w-full disabled:opacity-50"
          >
            {submitting ? 'AUTHENTICATING…' : 'SIGN IN'}
          </Button>
        </form>

        <div className="mt-6 text-center">
          <span className="font-data text-[0.6rem] uppercase tracking-widest text-sand-muted">
            <span className="text-tactical-orange">[</span> TACTICAL OPS{' '}
            <span className="text-tactical-orange">]</span>
          </span>
        </div>
      </div>
    </div>
  )
}
