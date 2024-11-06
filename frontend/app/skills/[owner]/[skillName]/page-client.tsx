"use client"

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { getSkillDetail, type SkillDetail as SkillDetailData } from "@/lib/skill"
import { FileText, GitFork, Info, Star } from "lucide-react"
import { Play } from "@phosphor-icons/react"
import Link from "next/link"
import { useEffect, useState } from "react"

function formatCount(count: number) {
  if (count >= 1000) {
    return `${(count / 1000).toFixed(count % 1000 === 0 ? 0 : 1)}k`
  }
  return count.toLocaleString()
}

export default function SkillDetailClient({
  owner,
  skillName,
}: {
  owner: string
  skillName: string
}) {
  const [skill, setSkill] = useState<SkillDetailData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)
    getSkillDetail(owner, skillName)
      .then((data) => {
        if (!cancelled) setSkill(data)
      })
      .catch(() => {
        if (!cancelled) setError("未找到该技能，可能已被删除或未公开")
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [owner, skillName])

  if (loading) {
    return (
      <div className="pt-app-header flex min-h-screen items-center justify-center">
        <div className="border-primary mx-auto mb-4 h-8 w-8 animate-spin rounded-full border-b-2" />
      </div>
    )
  }

  if (error || !skill) {
    return (
      <div className="pt-app-header flex min-h-screen flex-col items-center justify-center gap-3">
        <p className="text-muted-foreground">{error || "加载失败"}</p>
        <Link href="/skills" className="text-sm text-blue-600 hover:underline dark:text-blue-400">
          返回技能广场
        </Link>
      </div>
    )
  }

  return (
    <div className="pt-app-header relative flex min-h-screen flex-col">
      <div className="mx-auto w-full max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        {/* 页头 */}
        <div className="mb-8 flex items-start justify-between border-b border-border/50 pb-8">
          <div className="flex items-start gap-4">
            <Avatar className="h-12 w-12 flex-shrink-0 ring-1 ring-border/50">
              <AvatarImage
                src={
                  skill.avatar ||
                  `https://api.dicebear.com/7.x/bottts/svg?seed=${skill.owner}-${skill.name}`
                }
                alt={skill.title || skill.name}
              />
              <AvatarFallback className="text-sm font-medium">
                {skill.owner.substring(0, 2).toUpperCase()}
              </AvatarFallback>
            </Avatar>
            <div>
              <h1 className="text-2xl font-bold text-foreground">
                {skill.title || skill.name}
              </h1>
              <p className="text-sm text-muted-foreground">
                {skill.owner}/{skill.name}
              </p>
              <div className="mt-2 flex items-center gap-2">
                {skill.category && (
                  <Badge variant="secondary" className="text-xs">
                    {skill.category}
                  </Badge>
                )}
                <Badge variant="outline" className="gap-1 text-xs">
                  <Star className="h-3 w-3" />
                  {formatCount(skill.favorite_count)}
                </Badge>
              </div>
            </div>
          </div>
          <Link
            href={`/chat?type=skill&owner=${encodeURIComponent(owner)}&name=${encodeURIComponent(skillName)}`}
          >
            <Button className="gap-2 whitespace-nowrap">
              <Play className="h-4 w-4" weight="fill" />
              在线体验
            </Button>
          </Link>
        </div>

        {/* 主体内容 */}
        <div className="flex flex-col gap-8 lg:flex-row">
          {/* 左栏 */}
          <div className="min-w-0 flex-1">
            {/* 简介 */}
            <section className="mb-8">
              <h2 className="mb-3 flex items-center gap-2 text-lg font-semibold text-foreground">
                <Info className="h-5 w-5" />
                简介
              </h2>
              <p className="leading-relaxed text-muted-foreground">
                {skill.description || "暂无介绍"}
              </p>
            </section>
          </div>

          {/* 右栏 */}
          <div className="w-full lg:w-[340px]">
            {/* 仓库 */}
            {skill.repository && (
              <section className="mb-6">
                <h3 className="mb-2 text-sm font-medium text-foreground">代码仓库</h3>
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <GitFork className="h-4 w-4" />
                  <span className="break-all">{skill.repository}</span>
                </div>
              </section>
            )}

            {/* 安装路径 */}
            {skill.path && (
              <section>
                <h3 className="mb-2 flex items-center gap-2 text-sm font-medium text-foreground">
                  <FileText className="h-4 w-4" />
                  安装路径
                </h3>
                <div className="rounded-xl border border-border/50 bg-card px-4 py-2.5">
                  <code className="text-sm text-muted-foreground">{skill.path}</code>
                </div>
              </section>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
