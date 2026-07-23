'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')

  return (
    <div className="flex min-h-[calc(100vh-120px)] items-center justify-center">
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

        <div className="flex flex-col gap-4">
          <div>
            <label className="font-ui mb-1 block text-xs font-bold uppercase tracking-wider text-sand-muted">
              Email
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="ops@example.com"
              className="font-data w-full rounded border border-border-hard bg-surface-mid px-3 py-2.5 text-sm text-sand-bright placeholder:text-sand-muted focus:border-tactical-amber focus:outline-none"
            />
          </div>
          <div>
            <label className="font-ui mb-1 block text-xs font-bold uppercase tracking-wider text-sand-muted">
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="font-data w-full rounded border border-border-hard bg-surface-mid px-3 py-2.5 text-sm text-sand-bright placeholder:text-sand-muted focus:border-tactical-amber focus:outline-none"
            />
          </div>
          <Button
            variant="primary"
            size="lg"
            className="mt-2 w-full"
            onClick={() => console.log('sign in', { email, password })}
          >
            SIGN IN
          </Button>
        </div>

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
