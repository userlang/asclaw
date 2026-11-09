"use client"
// 作者：langjunnan
// 开发时间：2025年7月23日


import McpGallery from "@/components/layout/mcp-gallery"
import { getMcpRecommendList, McpRecommendItem } from "@/lib/mcp"
import { ArrowUpRight, Robot } from "@phosphor-icons/react"
import Link from "next/link"
import { useEffect, useState } from "react"

export default function HomePage() {
  const [servers, setServers] = useState<McpRecommendItem[]>([])
  const [loading, setLoading] = useState(true)
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true)
        const data = await getMcpRecommendList()
        setServers(data)
      } catch (err) {
        console.error("Failed to fetch recommend data:", err)
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [])

  return (
    <div className="@container/main relative flex min-h-screen flex-col">
      {/* Hero Section — 水平垂直居中 */}
      <section className="relative flex min-h-dvh items-center justify-center overflow-hidden px-4 pt-24 pb-16 sm:px-6 lg:px-8">
        <div className="relative mx-auto max-w-4xl text-center">
          {/* Top badge */}
          <div className="animate-fade-in-up mb-6 inline-flex items-center gap-2 rounded-full border border-border/50 bg-muted/50 px-4 py-1.5 text-sm text-muted-foreground backdrop-blur-sm">
            <Robot className="h-4 w-4 text-yellow-500" weight="fill" />
            <span>下一代智能 Agent 构建平台</span>
          </div>

          {/* Title */}
          <p className="animate-fade-in-up mb-8 text-3xl font-medium tracking-wide text-muted-foreground/70 sm:text-4xl [animation-delay:100ms]">
            赋予 AsClaw 无限能力
          </p>

          {/* 企业入驻 CTA */}
          <div className="animate-fade-in-up flex flex-col items-center gap-4 [animation-delay:150ms]">
            <Link
              href="/enterprise/apply"
              className="group inline-flex items-center gap-3 rounded-full bg-gradient-to-r from-blue-600 via-purple-600 to-blue-600 bg-[length:200%_auto] px-8 py-4 text-xl font-bold text-white shadow-lg transition-all hover:bg-right hover:shadow-xl"
            >
              申请入驻平台
              <ArrowUpRight className="h-5 w-5 transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
            </Link>
            <p className="text-muted-foreground text-sm">
              提交企业资质，管理员审核通过后即可使用企业账号登录平台
            </p>
            <Link
              href="/enterprise/login"
              className="text-muted-foreground hover:text-primary text-sm underline-offset-4 hover:underline"
            >
              已有企业账号？前往登录
            </Link>
          </div>
        </div>
      </section>

      {/* 精选展映 — 专辑封面式 3D 轮播 */}
      <section id="hot" className="relative pb-24">
        <div className="mx-auto mb-10 max-w-7xl px-4 sm:px-6 lg:px-8">
          <h2 className="text-center text-2xl font-semibold text-foreground">
            热门推荐
          </h2>
          <p className="text-muted-foreground mt-2 text-center text-sm">
            精选 MCP 服务，如同唱片一样轮番上映
          </p>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-20">
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-muted-foreground/20 border-t-primary" />
          </div>
        ) : (
          <McpGallery servers={servers} />
        )}
      </section>
    </div>
  )
}
