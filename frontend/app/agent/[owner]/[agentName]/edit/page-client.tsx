"use client"
// 作者：langjunnan
// 开发时间：2025年7月23日


import { getAgentDetail, type AgentFullDetail } from "@/lib/agent"
import BuildAgentPage from "@/app/build/agent/page-client"
import { useEffect, useState } from "react"

export default function EditAgentClient({
  owner,
  agentName,
}: {
  owner: string
  agentName: string
}) {
  const [agent, setAgent] = useState<AgentFullDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    getAgentDetail(owner, agentName)
      .then(setAgent)
      .catch(() => setError("未找到该 Agent"))
      .finally(() => setLoading(false))
  }, [owner, agentName])

  if (loading) {
    return (
      <div className="pt-app-header flex min-h-screen items-center justify-center">
        <div className="border-primary mx-auto mb-4 h-8 w-8 animate-spin rounded-full border-b-2" />
      </div>
    )
  }

  if (error || !agent) {
    return (
      <div className="pt-app-header flex min-h-screen items-center justify-center">
        <p className="text-muted-foreground">{error || "加载失败"}</p>
      </div>
    )
  }

  return <BuildAgentPage editAgent={agent} />
}
