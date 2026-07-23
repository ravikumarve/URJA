'use client'

import { useRef, useEffect, useState, useCallback } from 'react'
import { ChevronDown, ChevronRight, Maximize2, Minimize2 } from 'lucide-react'
import { cn } from '@/lib/utils'

interface Particle {
  x: number
  y: number
  size: number
  speedX: number
  speedY: number
  intensity: number
}

export default function RadarCanvas() {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const animRef = useRef<number>(0)
  const particlesRef = useRef<Particle[]>([])
  const angleRef = useRef(0)
  const isRunningRef = useRef(false)

  const [collapsed, setCollapsed] = useState(true)
  const [isVisible, setIsVisible] = useState(false)
  const [isFullscreen, setIsFullscreen] = useState(false)

  // ─── Canvas init ────────────────────────────────────────────────
  const initCanvas = useCallback(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const parent = canvas.parentElement
    if (!parent) return

    const w = parent.clientWidth
    const h = isFullscreen ? window.innerHeight - 120 : 380
    canvas.width = w
    canvas.height = h

    // Reset particles
    const p: Particle[] = []
    for (let i = 0; i < 150; i++) {
      p.push({
        x: Math.random() * w,
        y: Math.random() * h,
        size: Math.random() * 3 + 1,
        speedX: Math.random() * 2 + 1,
        speedY: (Math.random() - 0.5) * 0.5,
        intensity: Math.random(),
      })
    }
    particlesRef.current = p
  }, [isFullscreen])

  // ─── Draw frame ─────────────────────────────────────────────────
  const drawRadarGrid = useCallback((ctx: CanvasRenderingContext2D, w: number, h: number) => {
    const cx = w / 2
    const cy = h / 2
    const maxRadius = Math.min(w, h) / 2 - 20

    ctx.strokeStyle = 'rgba(217, 205, 189, 0.08)'
    ctx.lineWidth = 1

    for (let i = 1; i <= 4; i++) {
      ctx.beginPath()
      ctx.arc(cx, cy, maxRadius * (i / 4), 0, Math.PI * 2)
      ctx.stroke()
    }

    ctx.beginPath()
    ctx.moveTo(cx, 20)
    ctx.lineTo(cx, h - 20)
    ctx.moveTo(20, cy)
    ctx.lineTo(w - 20, cy)
    ctx.stroke()
  }, [])

  const animate = useCallback(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const w = canvas.width
    const h = canvas.height
    const cx = w / 2
    const cy = h / 2
    const radius = Math.min(w, h) / 2 - 20

    // Trail (semi-transparent fill instead of full clear)
    ctx.fillStyle = 'rgba(18, 16, 14, 0.25)'
    ctx.fillRect(0, 0, w, h)

    drawRadarGrid(ctx, w, h)

    // Dust storm particles
    const particles = particlesRef.current
    for (let i = 0; i < particles.length; i++) {
      const p = particles[i]
      p.x += p.speedX
      p.y += p.speedY

      if (p.x > w) p.x = 0
      if (p.y < 0) p.y = h
      if (p.y > h) p.y = 0

      ctx.beginPath()
      ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2)
      ctx.fillStyle =
        p.intensity > 0.8
          ? '#ef4444'
          : p.intensity > 0.4
            ? '#ff5e00'
            : '#ffb703'
      ctx.fill()
    }

    // Radar sweep line
    angleRef.current += 0.02
    const angle = angleRef.current
    ctx.beginPath()
    ctx.moveTo(cx, cy)
    ctx.lineTo(cx + Math.cos(angle) * radius, cy + Math.sin(angle) * radius)
    ctx.strokeStyle = '#ffb703'
    ctx.lineWidth = 2
    ctx.stroke()

    // Sweep gradient wedge
    ctx.beginPath()
    ctx.moveTo(cx, cy)
    ctx.arc(cx, cy, radius, angle, angle - 0.5, true)
    ctx.lineTo(cx, cy)
    const gradient = ctx.createRadialGradient(cx, cy, 0, cx, cy, radius)
    gradient.addColorStop(0, 'rgba(255, 183, 3, 0)')
    gradient.addColorStop(1, 'rgba(255, 183, 3, 0.15)')
    ctx.fillStyle = gradient
    ctx.fill()

    animRef.current = requestAnimationFrame(animate)
  }, [drawRadarGrid])

  // ─── Visibility observer ────────────────────────────────────────
  useEffect(() => {
    const el = containerRef.current
    if (!el) return

    const observer = new IntersectionObserver(
      ([entry]) => {
        setIsVisible(entry.isIntersecting)
      },
      { threshold: 0.1 },
    )

    observer.observe(el)
    return () => observer.disconnect()
  }, [])

  // ─── Animation lifecycle ────────────────────────────────────────
  useEffect(() => {
    if (!collapsed && isVisible) {
      isRunningRef.current = true
      initCanvas()
      animRef.current = requestAnimationFrame(animate)
    }

    return () => {
      isRunningRef.current = false
      cancelAnimationFrame(animRef.current)
    }
  }, [collapsed, isVisible, initCanvas, animate])

  // ─── Resize handler ─────────────────────────────────────────────
  useEffect(() => {
    if (!collapsed && isVisible) {
      const onResize = () => initCanvas()
      window.addEventListener('resize', onResize)
      return () => window.removeEventListener('resize', onResize)
    }
  }, [collapsed, isVisible, initCanvas])

  // ─── Fullscreen toggle ──────────────────────────────────────────
  const toggleFullscreen = () => {
    if (!isFullscreen && containerRef.current) {
      containerRef.current.requestFullscreen?.()
    } else {
      document.exitFullscreen?.()
    }
    setIsFullscreen(!isFullscreen)
  }

  useEffect(() => {
    const onFsChange = () => {
      if (!document.fullscreenElement) setIsFullscreen(false)
    }
    document.addEventListener('fullscreenchange', onFsChange)
    return () => document.removeEventListener('fullscreenchange', onFsChange)
  }, [])

  return (
    <div
      ref={containerRef}
      className={cn(
        'panel flex flex-col overflow-hidden transition-all duration-300',
        collapsed ? '' : isFullscreen ? 'fixed inset-0 z-50 rounded-none border-0' : '',
      )}
    >
      {/* ── Header (div, not button — contains a button for fullscreen) ── */}
      <div
        onClick={() => setCollapsed(!collapsed)}
        className="panel-header flex w-full cursor-pointer items-center justify-between hover:opacity-90"
        role="button"
        tabIndex={0}
        onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') setCollapsed(!collapsed) }}
      >
        <div className="flex items-center gap-2">
          {collapsed ? <ChevronRight size={14} /> : <ChevronDown size={14} />}
          <span>DNI &amp; ALBEDO TRACKING RADAR</span>
        </div>
        <div className="flex items-center gap-3">
          <span className="font-data text-[0.6rem] text-sand-muted">
            LAT: 26.91 | LON: 70.82
          </span>
          {!collapsed && (
            <button
              onClick={(e) => {
                e.stopPropagation()
                toggleFullscreen()
              }}
              className="text-sand-muted hover:text-sand-bright"
              title={isFullscreen ? 'Exit fullscreen' : 'Fullscreen'}
            >
              {isFullscreen ? <Minimize2 size={14} /> : <Maximize2 size={14} />}
            </button>
          )}
        </div>
      </div>

      {/* ── Canvas body ────────────────────────────────────────── */}
      <div
        className={cn(
          'transition-all duration-300',
          collapsed ? 'max-h-0 overflow-hidden' : 'max-h-[2000px]',
        )}
      >
        <div className="relative">
          <canvas
            ref={canvasRef}
            className="block w-full"
            style={{ height: isFullscreen ? 'calc(100vh - 120px)' : '380px' }}
          />

          {/* Storm warning overlay (shown when collapsed is toggled) */}
          {!collapsed && (
            <div className="pointer-events-none absolute bottom-3 left-3 flex items-center gap-2 rounded border border-tactical-red/30 bg-void/70 px-2 py-1 font-data text-[0.6rem] text-tactical-red">
              <span className="inline-block h-1.5 w-1.5 animate-blink rounded-full bg-tactical-red" />
              DUST STORM WARNING — ETA 45 MIN
            </div>
          )}
        </div>

        {/* ── Telemetry sidebar ────────────────────────────────── */}
        {!collapsed && (
          <div className="panel-body grid grid-cols-3 gap-4 border-t border-border-hard text-xs">
            <div className="flex flex-col gap-1">
              <span className="font-data text-[0.6rem] uppercase tracking-wider text-sand-muted">
                DNI (Direct Normal Irradiance)
              </span>
              <span className="font-data text-lg font-bold text-tactical-orange">312 W/m²</span>
              <span className="font-data text-[0.55rem] text-tactical-red">▼ -56.2% DUST OCCLUSION</span>
            </div>
            <div className="flex flex-col gap-1">
              <span className="font-data text-[0.6rem] uppercase tracking-wider text-sand-muted">
                Wind Speed (Anemometer)
              </span>
              <span className="font-data text-lg font-bold text-sand-bright">42.8 km/h</span>
            </div>
            <div className="flex flex-col gap-1">
              <span className="font-data text-[0.6rem] uppercase tracking-wider text-sand-muted">
                Soiling Ratio
              </span>
              <span className="font-data text-lg font-bold text-tactical-orange">78%</span>
              <span className="font-data text-[0.55rem] text-tactical-orange">CRITICAL: CLEANING REQUIRED</span>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
