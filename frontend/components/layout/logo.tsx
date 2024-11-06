"use client"

import Link from "next/link"

export function Logo({ className = "" }: { className?: string }) {
  return (
    <Link
      href="/"
      className={`flex shrink-0 items-center ${className}`}
      aria-label="asclaw 首页"
    >
      <span className="bg-gradient-to-r from-indigo-500 via-purple-500 to-fuchsia-500 bg-clip-text text-xl font-bold tracking-tight text-transparent">
        AsClaw
      </span>
    </Link>
  )
}
