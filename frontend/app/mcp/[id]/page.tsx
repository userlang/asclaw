// 作者：langjunnan
// 开发时间：2025年7月23日

import LayoutApp from "@/components/layout/layout-app"
import { notFound } from "next/navigation"
import ServerDetailClient from "./page-client"

export default async function ServerDetailPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = await params

  // 详情按 MCP id 寻址，非数字 id 直接 404
  if (!id || !/^\d+$/.test(id)) return notFound()

  return (
    <LayoutApp>
      <ServerDetailClient id={Number(id)} />
    </LayoutApp>
  )
}
