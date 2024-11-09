"use client"
// 作者：langjunnan
// 开发时间：2025年7月23日


import { McpRecommendItem } from "@/lib/mcp"
import { cn } from "@/lib/utils"
import { ArrowUpRight, CaretLeft, CaretRight, Globe } from "@phosphor-icons/react"
import Link from "next/link"
import { useCallback, useEffect, useState } from "react"

// 专辑封面兜底配色：按名称哈希取色，同一服务永远得到同一张"专辑"
const PALETTES: [string, string, string][] = [
  ["#4338ca", "#a855f7", "#f0abfc"],
  ["#0e7490", "#22d3ee", "#a5f3fc"],
  ["#be123c", "#fb923c", "#fed7aa"],
  ["#047857", "#34d399", "#a7f3d0"],
  ["#7c3aed", "#f472b6", "#fbcfe8"],
  ["#b45309", "#fbbf24", "#fde68a"],
  ["#1d4ed8", "#60a5fa", "#bfdbfe"],
  ["#0f766e", "#2dd4bf", "#99f6e4"],
]

function hashName(name: string): number {
  let h = 0
  for (let i = 0; i < name.length; i++) {
    h = (h * 31 + name.charCodeAt(i)) >>> 0
  }
  return h
}

function formatCallCount(count: number): string {
  if (count >= 10000) {
    return (count / 1000).toFixed(1) + "k"
  }
  if (count >= 1000) {
    return (count / 1000).toFixed(2) + "k"
  }
  return count.toString()
}

/** 专辑封面：有 cover 用真图，没有就生成一张"唱片封面"（渐变 + 唱片纹 + 排版） */
function Cover({ server, className }: { server: McpRecommendItem; className?: string }) {
  if (server.cover) {
    return (
      <div className={cn("relative overflow-hidden bg-muted", className)}>
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={server.cover}
          alt={server.server_name}
          className="absolute inset-0 h-full w-full object-cover"
        />
        {/* 底部压暗，保证封面文字可读 */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/10 to-transparent" />
        {/* 专辑名排版 */}
        <div className="absolute inset-x-0 bottom-0 flex flex-col gap-0.5 p-[7%]">
          <span className="truncate text-sm font-bold uppercase tracking-widest text-white/95">
            {server.server_name}
          </span>
          <span className="text-[0.65rem] uppercase tracking-[0.25em] text-white/60">
            {server.owner}
          </span>
        </div>
      </div>
    )
  }

  const [from, to, accent] = PALETTES[hashName(server.server_name) % PALETTES.length]
  const initials = server.server_name.replace(/[^a-zA-Z0-9]/g, "").substring(0, 2).toUpperCase()

  return (
    <div
      className={cn("relative overflow-hidden", className)}
      style={{ background: `linear-gradient(135deg, ${from} 0%, ${to} 100%)` }}
    >
      {/* 唱片纹：同心圆环 + 盘心 */}
      <div className="absolute -right-[18%] -top-[18%] h-[85%] w-[85%] rounded-full border border-white/15">
        <div className="absolute inset-[12%] rounded-full border border-white/10" />
        <div className="absolute inset-[28%] rounded-full border border-white/10" />
        <div
          className="absolute inset-[44%] rounded-full"
          style={{ background: `radial-gradient(circle, ${accent}cc 0%, transparent 75%)` }}
        />
      </div>
      {/* 光泽 */}
      <div className="absolute inset-0 bg-gradient-to-tr from-black/25 via-transparent to-white/15" />
      {/* 排版：像专辑封面的艺术家名 */}
      <div className="absolute inset-0 flex flex-col justify-between p-[7%]">
        <span
          className="font-black leading-none tracking-tighter text-white/90"
          style={{ fontSize: "clamp(2.5rem, 22cqw, 5.5rem)" }}
        >
          {initials}
        </span>
        <span className="truncate text-[clamp(0.6rem,4.5cqw,0.9rem)] font-medium uppercase tracking-[0.2em] text-white/75">
          {server.server_name}
        </span>
      </div>
    </div>
  )
}

export default function McpGallery({ servers }: { servers: McpRecommendItem[] }) {
  const [index, setIndex] = useState(0)
  const [paused, setPaused] = useState(false)
  const count = servers.length

  const goTo = useCallback(
    (i: number) => {
      if (count > 0) setIndex(((i % count) + count) % count)
    },
    [count]
  )

  // 自动轮播：悬停暂停；用户系统要求减少动效时不开自动播放
  useEffect(() => {
    if (paused || count <= 1) return
    if (typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      return
    }
    const timer = setInterval(() => setIndex((i) => (i + 1) % count), 3600)
    return () => clearInterval(timer)
  }, [paused, count])

  if (count === 0) return null

  // 环形最近距离：负数在左、正数在右， wrap-around 保证首尾相接像胶片盘
  const offsetOf = (i: number) => {
    let d = i - index
    if (d > count / 2) d -= count
    if (d < -count / 2) d += count
    return d
  }

  const center = servers[index]

  return (
    <div className="select-none">
      {/* 放映舞台 */}
      <div
        className="relative mx-auto h-[300px] sm:h-[380px] lg:h-[440px] max-w-full [--cover-w:200px] sm:[--cover-w:260px] lg:[--cover-w:310px]"
        style={{ perspective: "1400px" }}
        onMouseEnter={() => setPaused(true)}
        onMouseLeave={() => setPaused(false)}
      >
        {/* 舞台底光，营造"放映厅"深度 */}
        <div className="bg-primary/10 absolute left-1/2 top-1/2 h-[60%] w-[70%] -translate-x-1/2 -translate-y-1/2 rounded-full blur-3xl" />

        {servers.map((server, i) => {
          const d = offsetOf(i)
          const abs = Math.abs(d)
          if (abs > Math.min(2, Math.floor(count / 2))) return null

          const isActive = d === 0

          return (
            <div
              key={`${server.owner}/${server.server_name}`}
              className="absolute left-1/2 top-1/2 transition-all duration-700 ease-[cubic-bezier(0.22,1,0.36,1)]"
              style={{
                width: "var(--cover-w)",
                aspectRatio: "1 / 1",
                zIndex: 10 - abs,
                transform: `translate(calc(-50% + ${d} * var(--cover-w) * 0.68), -50%) translateZ(${-abs * 110}px) rotateY(${d * -38}deg)`,
                filter: `brightness(${1 - Math.min(abs, 3) * 0.18})`,
                opacity: abs > 2 ? 0 : 1,
                pointerEvents: abs > 2 ? "none" : "auto",
              }}
            >
              {isActive ? (
                <Link
                  href={`/mcp/${server.owner}/${server.server_name}`}
                  className="group/cover block h-full w-full cursor-pointer"
                  draggable={false}
                >
                  <div className="h-full w-full overflow-hidden rounded-2xl shadow-2xl shadow-black/40 ring-1 ring-white/20 transition-transform duration-500 group-hover/cover:scale-[1.02]">
                    <Cover server={server} className="h-full w-full" />
                  </div>
                </Link>
              ) : (
                <button
                  type="button"
                  onClick={() => goTo(index + d)}
                  className="block h-full w-full cursor-pointer text-left"
                  aria-label={`切换到 ${server.server_name}`}
                >
                  <div className="h-full w-full overflow-hidden rounded-2xl shadow-xl shadow-black/30 ring-1 ring-white/10 transition-transform hover:scale-[1.03]">
                    <Cover server={server} className="h-full w-full" />
                  </div>
                </button>
              )}
            </div>
          )
        })}

        {/* 左右箭头 */}
        <button
          type="button"
          onClick={() => goTo(index - 1)}
          aria-label="上一张"
          className="bg-background/60 text-foreground/70 hover:bg-background hover:text-foreground absolute left-2 top-1/2 z-20 -translate-y-1/2 rounded-full p-2 backdrop-blur transition-colors sm:left-6"
        >
          <CaretLeft className="h-5 w-5" />
        </button>
        <button
          type="button"
          onClick={() => goTo(index + 1)}
          aria-label="下一张"
          className="bg-background/60 text-foreground/70 hover:bg-background hover:text-foreground absolute right-2 top-1/2 z-20 -translate-y-1/2 rounded-full p-2 backdrop-blur transition-colors sm:right-6"
        >
          <CaretRight className="h-5 w-5" />
        </button>
      </div>

      {/* 中央唱片信息条 */}
      <div className="mx-auto mt-6 max-w-2xl px-4 text-center">
        <div key={center.server_name} className="animate-fade-in-up">
          <div className="mb-2 flex items-center justify-center gap-2 text-xs text-muted-foreground">
            <span className="truncate">@{center.owner}</span>
            <span className="text-border">·</span>
            <span className="flex items-center gap-1">
              <Globe className="h-3 w-3" />
              {center.server_type === "hosted" ? "Remote" : "Local"}
            </span>
            <span className="text-border">·</span>
            <span className="flex items-center gap-1">
              <ArrowUpRight className="h-3 w-3" />
              {formatCallCount(center.call_count)}
            </span>
          </div>
          <Link
            href={`/mcp/${center.owner}/${center.server_name}`}
            className="group/center block"
          >
            <h3 className="group-hover/center:text-primary text-xl font-semibold transition-colors">
              {center.server_name}
            </h3>
            <p className="text-muted-foreground mt-1 line-clamp-2 text-sm leading-relaxed">
              {center.description}
            </p>
          </Link>
        </div>

        {/* 胶片盘指示点 */}
        <div className="mt-5 flex items-center justify-center gap-2">
          {servers.map((s, i) => (
            <button
              key={`dot-${s.owner}/${s.server_name}`}
              type="button"
              onClick={() => goTo(i)}
              aria-label={`第 ${i + 1} 张`}
              className={cn(
                "h-1.5 rounded-full transition-all duration-300",
                i === index ? "bg-primary w-6" : "bg-muted-foreground/30 hover:bg-muted-foreground/50 w-1.5"
              )}
            />
          ))}
        </div>
      </div>
    </div>
  )
}
