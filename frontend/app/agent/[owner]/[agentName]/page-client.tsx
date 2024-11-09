"use client"
// 作者：langjunnan
// 开发时间：2025年7月23日


import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { useUser } from "@/components/providers/user-provider"
import { deleteMyAgent, getAgentDetail, type AgentFullDetail } from "@/lib/agent"
import { Play } from "@phosphor-icons/react"
import { Bot, BrainCircuit, Loader2, MessageSquare, Pencil, Settings, Wrench, Zap } from "lucide-react"
import Link from "next/link"
import { useEffect, useState } from "react"
import { toast } from "sonner"

export default function AgentDetailClient({
  owner,
  agentName,
}: {
  owner: string
  agentName: string
}) {
  const { user } = useUser()
  const [agent, setAgent] = useState<AgentFullDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [deleting, setDeleting] = useState(false)

  const avatarSeed = `${owner}-${agentName}`
  const isMine = !!user && user.username === owner

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)
    getAgentDetail(owner, agentName)
      .then((data) => {
        if (!cancelled) setAgent(data)
      })
      .catch(() => {
        if (!cancelled) setError("未找到该 Agent，可能已被删除或未公开")
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [owner, agentName])

  const handleDelete = async () => {
    if (!agent || !confirm("确定删除该 Agent？删除后不可恢复。")) return
    setDeleting(true)
    try {
      await deleteMyAgent(agent.id)
      toast.success("Agent 已删除")
      window.location.href = "/agent"
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "删除失败")
      setDeleting(false)
    }
  }

  if (loading) {
    return (
      <div className="pt-app-header flex min-h-screen items-center justify-center">
        <div className="border-primary mx-auto mb-4 h-8 w-8 animate-spin rounded-full border-b-2" />
      </div>
    )
  }

  if (error || !agent) {
    return (
      <div className="pt-app-header flex min-h-screen flex-col items-center justify-center gap-3">
        <p className="text-muted-foreground">{error || "加载失败"}</p>
        <Link href="/agent" className="text-sm text-blue-600 hover:underline dark:text-blue-400">
          返回 Agent 广场
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
                src={agent.avatar || `https://api.dicebear.com/7.x/bottts/svg?seed=${avatarSeed}`}
                alt={agent.title}
              />
              <AvatarFallback className="text-sm font-medium">
                <Bot className="h-5 w-5" />
              </AvatarFallback>
            </Avatar>
            <div>
              <h1 className="text-2xl font-bold text-foreground">{agent.title}</h1>
              <p className="text-sm text-muted-foreground">
                {agent.owner}/{agent.name}
              </p>
              <div className="mt-2 flex items-center gap-2">
                {agent.category && (
                  <Badge variant="secondary" className="text-xs">
                    {agent.category}
                  </Badge>
                )}
                {agent.mcps.length > 0 && (
                  <Badge variant="outline" className="gap-1 text-xs">
                    <Wrench className="h-3 w-3" />
                    {agent.mcps.length} MCP
                  </Badge>
                )}
                {agent.skills.length > 0 && (
                  <Badge variant="outline" className="gap-1 text-xs">
                    <Zap className="h-3 w-3" />
                    {agent.skills.length} 技能
                  </Badge>
                )}
                {!agent.is_public && (
                  <Badge variant="secondary" className="text-xs">
                    私有
                  </Badge>
                )}
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {isMine && (
              <>
                <Button variant="outline" size="sm" className="gap-1.5" asChild>
                  <Link href={`/agent/${owner}/${agentName}/edit`}>
                    <Pencil className="h-3.5 w-3.5" />
                    编辑
                  </Link>
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  className="text-destructive hover:text-destructive gap-1.5"
                  onClick={handleDelete}
                  disabled={deleting}
                >
                  {deleting ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : null}
                  删除
                </Button>
              </>
            )}
            <Link
              href={`/chat?type=agent&owner=${encodeURIComponent(owner)}&name=${encodeURIComponent(agentName)}`}
            >
              <Button className="gap-2 whitespace-nowrap">
                <Play className="h-4 w-4" weight="fill" />
                开始对话
              </Button>
            </Link>
          </div>
        </div>

        {/* 主体 */}
        <div className="flex flex-col gap-8 lg:flex-row">
          <div className="min-w-0 flex-1">
            {/* 简介 */}
            <section className="mb-8">
              <h2 className="mb-3 flex items-center gap-2 text-lg font-semibold text-foreground">
                <MessageSquare className="h-5 w-5" />
                简介
              </h2>
              <p className="leading-relaxed text-muted-foreground">
                {agent.description || "暂无介绍"}
              </p>
            </section>

            {/* 开场白 */}
            {agent.prologue && (
              <section className="mb-8">
                <h2 className="mb-3 text-lg font-semibold text-foreground">开场白</h2>
                <div className="rounded-xl border border-border/50 bg-card p-5">
                  <p className="text-sm leading-relaxed text-muted-foreground">
                    {agent.prologue}
                  </p>
                </div>
              </section>
            )}

            {/* 系统提示词 */}
            {agent.system_prompt && (
              <section className="mb-8">
                <h2 className="mb-3 flex items-center gap-2 text-lg font-semibold text-foreground">
                  <Settings className="h-5 w-5" />
                  系统提示词
                </h2>
                <div className="rounded-xl border border-border/50 bg-card p-5">
                  <pre className="whitespace-pre-wrap text-sm leading-relaxed text-muted-foreground">
                    {agent.system_prompt}
                  </pre>
                </div>
              </section>
            )}
          </div>

          {/* 右栏：配置清单 */}
          <div className="w-full lg:w-[340px]">
            <section className="mb-6">
              <h3 className="mb-3 flex items-center gap-2 text-sm font-medium text-foreground">
                <Wrench className="h-4 w-4" />
                绑定的 MCP
              </h3>
              {agent.mcps.length === 0 ? (
                <p className="text-muted-foreground rounded-lg bg-muted/40 px-4 py-3 text-xs">
                  未绑定
                </p>
              ) : (
                <div className="space-y-2">
                  {agent.mcps.map((m) => (
                    <div
                      key={m}
                      className="rounded-lg border border-border/50 bg-card px-4 py-2.5"
                    >
                      <code className="text-xs text-muted-foreground">{m}</code>
                    </div>
                  ))}
                </div>
              )}
            </section>

            <section>
              <h3 className="mb-3 flex items-center gap-2 text-sm font-medium text-foreground">
                <Zap className="h-4 w-4" />
                绑定的 Skill
              </h3>
              {agent.skills.length === 0 ? (
                <p className="text-muted-foreground rounded-lg bg-muted/40 px-4 py-3 text-xs">
                  未绑定
                </p>
              ) : (
                <div className="space-y-2">
                  {agent.skills.map((s) => (
                    <div
                      key={s}
                      className="rounded-lg border border-border/50 bg-card px-4 py-2.5"
                    >
                      <code className="text-xs text-muted-foreground">{s}</code>
                    </div>
                  ))}
                </div>
              )}
            </section>

            {agent.enable_search && (
              <section className="mt-6">
                <h3 className="mb-3 flex items-center gap-2 text-sm font-medium text-foreground">
                  <BrainCircuit className="h-4 w-4" />
                  能力
                </h3>
                <div className="flex flex-wrap gap-2">
                  <Badge variant="outline" className="text-xs">
                    联网搜索
                  </Badge>
                  {agent.enable_suggest && (
                    <Badge variant="outline" className="text-xs">
                      问题建议
                    </Badge>
                  )}
                  {agent.enable_multimodal && (
                    <Badge variant="outline" className="text-xs">
                      多模态
                    </Badge>
                  )}
                </div>
              </section>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
