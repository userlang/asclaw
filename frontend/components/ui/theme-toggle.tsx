"use client"
// 作者：langjunnan
// 开发时间：2025年7月23日


import { Moon, Sun } from "lucide-react"
import { useTheme } from "next-themes"
import { useEffect, useState } from "react"

export function ThemeToggle() {
  const { setTheme, resolvedTheme } = useTheme()
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  if (!mounted) return null

  const isDark = resolvedTheme === "dark"

  return (
    <button
      onClick={() => setTheme(isDark ? "light" : "dark")}
      className="rounded-md p-2 hover:bg-accent hover:text-accent-foreground transition-colors"
      aria-label={isDark ? "切换到浅色" : "切换到深色"}
      title={isDark ? "切换到浅色" : "切换到深色"}
    >
      {isDark ? (
        <Sun className="icon-gradient h-5 w-5" />
      ) : (
        <Moon className="icon-gradient h-5 w-5" />
      )}
    </button>
  )
}
