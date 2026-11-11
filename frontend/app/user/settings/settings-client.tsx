"use client"
// 作者：langjunnan
// 开发时间：2025年7月23日

import { LlmCredentialPanel } from "@/components/user/llm-credential-panel"

export default function SettingsClient() {
  return (
    <div className="mx-auto w-full max-w-2xl px-4 py-8 sm:px-6">
      <div className="mb-6">
        <h1 className="text-2xl font-semibold">设置</h1>
        <p className="text-muted-foreground mt-1 text-sm">管理你的账号与模型配置</p>
      </div>
      <LlmCredentialPanel />
    </div>
  )
}
