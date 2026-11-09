"use client"
// 作者：langjunnan
// 开发时间：2025年7月23日


import { Header } from "@/components/layout/header"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { submitMcpServer } from "@/lib/mcp"
import { ArrowLeft, CircleNotch, Cube, Globe, Wrench } from "@phosphor-icons/react"
import Link from "next/link"
import { useMemo, useState } from "react"

type TransportKind = "stdio" | "remote"

const STIO_TEMPLATE = `{
  "mcpServers": {
    "my-server": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-xxx"],
      "env": {}
    }
  }
}`

const REMOTE_TEMPLATE = `{
  "mcpServers": {
    "my-server": {
      "url": "https://example.com/mcp",
      "headers": {}
    }
  }
}`

export default function McpSubmitPage() {
  const [serverTitle, setServerTitle] = useState("")
  const [description, setDescription] = useState("")
  const [transportKind, setTransportKind] = useState<TransportKind>("stdio")
  const [configJson, setConfigJson] = useState(STIO_TEMPLATE)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  const configTemplate = transportKind === "stdio" ? STIO_TEMPLATE : REMOTE_TEMPLATE

  const parsedConfig = useMemo(() => {
    try {
      const parsed = JSON.parse(configJson)
      if (!parsed?.mcpServers || typeof parsed.mcpServers !== "object") {
        return { ok: false as const, error: '缺少 "mcpServers" 字段' }
      }
      const entries = Object.entries(parsed.mcpServers)
      if (entries.length === 0) {
        return { ok: false as const, error: "mcpServers 不能为空" }
      }
      const [name, cfg] = entries[0] as [string, Record<string, unknown>]
      if (transportKind === "stdio") {
        if (!cfg.command) return { ok: false as const, error: "stdio 配置缺少 command 字段" }
      } else {
        if (!cfg.url) return { ok: false as const, error: "remote 配置缺少 url 字段" }
      }
      return { ok: true as const, name, cfg }
    } catch {
      return { ok: false as const, error: "JSON 格式错误" }
    }
  }, [configJson, transportKind])

  function switchTransport(kind: TransportKind) {
    setTransportKind(kind)
    setConfigJson(kind === "stdio" ? STIO_TEMPLATE : REMOTE_TEMPLATE)
    setError(null)
  }

  async function handleSubmit() {
    setError(null)
    setSuccess(null)

    if (!serverTitle.trim()) {
      setError("请填写服务名称")
      return
    }
    if (!parsedConfig.ok) {
      setError(parsedConfig.error)
      return
    }

    try {
      setIsSubmitting(true)
      const body = {
        server_title: serverTitle.trim(),
        description: description.trim() || undefined,
        mcpServers: { [parsedConfig.name]: parsedConfig.cfg },
      }
      await submitMcpServer(body)
      setSuccess(
        "提交成功！正在后台编译，通常需要几十秒。编译完成后可在「我的 MCP」中查看。"
      )
      setServerTitle("")
      setDescription("")
    } catch (err: any) {
      setError(err.message || "提交失败，请稍后重试")
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <>
      <Header />
      <div className="mx-auto w-full max-w-3xl px-4 pt-24 pb-8">
      <Link
        href="/mcp"
        className="text-muted-foreground hover:text-foreground mb-6 inline-flex items-center gap-1 text-sm transition-colors"
      >
        <ArrowLeft className="h-4 w-4" />
        返回 MCP 市场
      </Link>

      <div className="mb-6">
        <h1 className="text-2xl font-semibold">添加 MCP 服务器</h1>
        <p className="text-muted-foreground mt-1 text-sm">
          支持 stdio 本地命令与 HTTP/SSE 远程服务，提交后系统会自动连接并编译工具列表。
        </p>
      </div>

      {success && (
        <div className="mb-6 rounded-md border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-700 dark:border-green-800 dark:bg-green-950 dark:text-green-300">
          {success}
        </div>
      )}

      <div className="space-y-6">
        {/* 基本信息 */}
        <div className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="server-title">服务名称 *</Label>
            <Input
              id="server-title"
              placeholder="例如：brave-search"
              value={serverTitle}
              onChange={(e) => setServerTitle(e.target.value)}
              maxLength={60}
            />
            <p className="text-muted-foreground text-xs">
              仅允许中英文、数字、空格、连字符、下划线和点
            </p>
          </div>
          <div className="space-y-2">
            <Label htmlFor="description">描述</Label>
            <Input
              id="description"
              placeholder="一句话描述这个 MCP 的用途（可选）"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              maxLength={200}
            />
          </div>
        </div>

        {/* 传输方式选择 */}
        <div className="space-y-2">
          <Label>接入方式</Label>
          <div className="grid grid-cols-2 gap-3">
            <button
              type="button"
              onClick={() => switchTransport("stdio")}
              className={`flex items-start gap-3 rounded-lg border p-4 text-left transition-colors ${
                transportKind === "stdio"
                  ? "border-foreground bg-accent"
                  : "hover:bg-accent/50"
              }`}
            >
              <Wrench className="mt-0.5 h-5 w-5 shrink-0" />
              <span>
                <span className="block text-sm font-medium">本地命令 (stdio)</span>
                <span className="text-muted-foreground mt-0.5 block text-xs">
                  通过 npx / uvx 运行的本地包
                </span>
              </span>
            </button>
            <button
              type="button"
              onClick={() => switchTransport("remote")}
              className={`flex items-start gap-3 rounded-lg border p-4 text-left transition-colors ${
                transportKind === "remote"
                  ? "border-foreground bg-accent"
                  : "hover:bg-accent/50"
              }`}
            >
              <Globe className="mt-0.5 h-5 w-5 shrink-0" />
              <span>
                <span className="block text-sm font-medium">远程服务 (HTTP/SSE)</span>
                <span className="text-muted-foreground mt-0.5 block text-xs">
                  已部署的远程 MCP URL，直连不托管
                </span>
              </span>
            </button>
          </div>
        </div>

        {/* 配置 JSON */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <Label htmlFor="config">mcpServers 配置 *</Label>
            <button
              type="button"
              onClick={() => setConfigJson(configTemplate)}
              className="text-muted-foreground hover:text-foreground text-xs transition-colors"
            >
              恢复模板
            </button>
          </div>
          <Textarea
            id="config"
            value={configJson}
            onChange={(e) => setConfigJson(e.target.value)}
            className="h-64 font-mono text-sm"
            spellCheck={false}
          />
          <p className="text-muted-foreground flex items-center gap-1 text-xs">
            <Cube className="h-3.5 w-3.5" />
            {transportKind === "stdio"
              ? "支持 npx / uvx 命令，env 中可配置环境变量"
              : "支持 streamable-http 与 SSE，服务端会自动探测传输协议"}
          </p>
          {!parsedConfig.ok && configJson.trim() && (
            <p className="text-xs text-red-500">{parsedConfig.error}</p>
          )}
        </div>

        {error && <p className="text-sm text-red-500">{error}</p>}

        <Button
          size="lg"
          className="w-full"
          onClick={handleSubmit}
          disabled={isSubmitting || !parsedConfig.ok || !serverTitle.trim()}
        >
          {isSubmitting ? (
            <>
              <CircleNotch className="h-4 w-4 animate-spin" weight="bold" />
              提交中...
            </>
          ) : (
            "提交并编译"
          )}
        </Button>
      </div>
      </div>
    </>
  )
}
