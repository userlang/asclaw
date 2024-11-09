// 作者：langjunnan
// 开发时间：2025年7月23日

import EditAgentClient from "./page-client"
import LayoutApp from "@/components/layout/layout-app"

export default async function EditAgentPage({
  params,
}: {
  params: Promise<{ owner: string; agentName: string }>
}) {
  const { owner, agentName } = await params

  if (!owner || !agentName) return notFoundPage()

  return (
    <LayoutApp>
      <EditAgentClient owner={owner} agentName={agentName} />
    </LayoutApp>
  )
}

function notFoundPage() {
  return (
    <div className="flex min-h-screen items-center justify-center">
      <p className="text-muted-foreground">404</p>
    </div>
  )
}
