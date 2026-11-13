"use client"
// 作者：langjunnan
// 开发时间：2025年7月23日


import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { CredentialDialog } from "@/components/mcp/credential-dialog"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { useUser } from "@/components/providers/user-provider"
import { callMcpServerTool, getMcpCredentialStatus, getMcpServerDetail, McpServerItem, updateMcpAvatar, updateMcpCover } from "@/lib/mcp"
import { cn } from "@/lib/utils"
import { Play } from "@phosphor-icons/react"
import {
  Cloud,
  Globe,
  Info,
  KeyRound,
  Monitor,
  Pencil,
  Zap,
} from "lucide-react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { useEffect, useState } from "react"
import { toast } from "sonner"

export default function ServerDetailClient({
  id,
}: {
  id: number
}) {
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [serverDetail, setServerDetail] = useState<McpServerItem | null>(null)
  const [toolResults, setToolResults] = useState<
    Record<
      string,
      { isLoading: boolean; result: string | null; error: string | null }
    >
  >({})
  const [toolInputs, setToolInputs] = useState<
    Record<string, Record<string, any>>
  >({})
  const [envInputs, setEnvInputs] = useState<Record<string, string>>({})
  const [credentialOpen, setCredentialOpen] = useState(false)
  const { user } = useUser()
  const router = useRouter()
  const [avatarOpen, setAvatarOpen] = useState(false)
  const [avatarValue, setAvatarValue] = useState("")
  const [savingAvatar, setSavingAvatar] = useState(false)
  const [coverOpen, setCoverOpen] = useState(false)
  const [coverValue, setCoverValue] = useState("")
  const [savingCover, setSavingCover] = useState(false)

  useEffect(() => {
    const fetchServerDetail = async () => {
      try {
        setIsLoading(true)
        setError(null)
        const response = await getMcpServerDetail(id)
        setServerDetail(response)

        // Initialize tool inputs with default values
        if (response.tools) {
          const initialInputs: Record<string, Record<string, any>> = {}

          response.tools.forEach((tool) => {
            const toolName = tool.name
            const inputs: Record<string, any> = {}

            if (tool.inputSchema?.properties) {
              Object.entries(tool.inputSchema.properties).forEach(
                ([paramName, paramDetails]: [string, any]) => {
                  // Set default value if available, otherwise empty string
                  inputs[paramName] =
                    paramDetails.default !== undefined
                      ? paramDetails.default
                      : ""
                }
              )
            }

            initialInputs[toolName] = inputs
          })

          setToolInputs(initialInputs)
        }

        // Initialize environment variables if present
        if (response.envs && Object.keys(response.envs).length > 0) {
          const initialEnvs: Record<string, string> = {}
          Object.entries(response.envs).forEach(([key, value]) => {
            initialEnvs[key] = value as string
          })
          setEnvInputs(initialEnvs)
        }
      } catch (err) {
        console.error("Error fetching server details:", err)
        setError("Failed to load server details. Please try again.")
      } finally {
        setIsLoading(false)
      }
    }

    fetchServerDetail()
  }, [id])

  // 头像保存后局部刷新详情（不整页重载）
  const refreshDetail = async () => {
    try {
      setServerDetail(await getMcpServerDetail(id))
    } catch {
      // 静默失败，保留旧详情
    }
  }

  const handleSaveAvatar = async (avatar: string | null) => {
    if (!serverDetail?.id) return
    try {
      setSavingAvatar(true)
      await updateMcpAvatar(serverDetail.id, avatar)
      toast.success(avatar ? "头像已更新" : "已恢复默认头像")
      setAvatarOpen(false)
      await refreshDetail()
    } catch {
      toast.error("保存失败，请重试")
    } finally {
      setSavingAvatar(false)
    }
  }

  const handleSaveCover = async (cover: string | null) => {
    if (!serverDetail?.id) return
    try {
      setSavingCover(true)
      await updateMcpCover(serverDetail.id, cover)
      toast.success(cover ? "封面已更新" : "已清除封面")
      setCoverOpen(false)
      await refreshDetail()
    } catch {
      toast.error("保存失败，请重试")
    } finally {
      setSavingCover(false)
    }
  }

  const handleInputChange = (
    toolName: string,
    paramName: string,
    value: string
  ) => {
    setToolInputs((prev) => ({
      ...prev,
      [toolName]: {
        ...prev[toolName],
        [paramName]: value,
      },
    }))
  }

  const validateToolInputs = (
    toolName: string,
    tool: any
  ): { isValid: boolean; missingParams: string[] } => {
    const requiredParams = tool.inputSchema?.required || []
    const inputs = toolInputs[toolName] || {}

    const missingParams = requiredParams.filter(
      (param: string) =>
        !inputs[param] || inputs[param].toString().trim() === ""
    )

    return {
      isValid: missingParams.length === 0,
      missingParams,
    }
  }

  const handleRunTool = async (toolName: string, tool: any) => {
    if (!serverDetail) return

    // Validate required parameters
    const { isValid, missingParams } = validateToolInputs(toolName, tool)

    if (!isValid) {
      setToolResults((prev) => ({
        ...prev,
        [toolName]: {
          isLoading: false,
          result: null,
          error: `Missing required parameters: ${missingParams.join(", ")}`,
        },
      }))
      return
    }

    setToolResults((prev) => ({
      ...prev,
      [toolName]: { isLoading: true, result: null, error: null },
    }))

    try {
      const response = await callMcpServerTool(
        id,
        toolName,
        toolInputs[toolName] || {}
      )

      // Extract the text content from the response
      const resultText = response.content
        .filter((item) => item.type === "text")
        .map((item) => item.text)
        .join("\n")

      setToolResults((prev) => ({
        ...prev,
        [toolName]: { isLoading: false, result: resultText, error: null },
      }))
    } catch (err: any) {
      const errorMsg = err.code && err.code !== 200
        ? err.message
        : err.response?.data?.msg || err.message || "Failed to run tool"
      setToolResults((prev) => ({
        ...prev,
        [toolName]: {
          isLoading: false,
          result: null,
          error: errorMsg,
        },
      }))
    }
  }

  if (error) {
    return (
      <div className="flex h-full flex-col items-center justify-center p-8">
        <div className="mb-4 text-red-500">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="h-12 w-12"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
            />
          </svg>
        </div>
        <h2 className="mb-2 text-xl font-semibold">Error</h2>
        <p className="text-muted-foreground mb-4">{error}</p>
        <Link href="/mcp" className="text-primary hover:underline">
          Return to MCP Servers
        </Link>
      </div>
    )
  }

  if (isLoading || !serverDetail) {
    return (
      <div className="flex h-full items-center justify-center p-8">
        <div className="border-foreground h-12 w-12 animate-spin rounded-full border-b-2"></div>
      </div>
    )
  }

  const server = serverDetail

  // 未编译/编译失败时 server_metadata 可能为 null，统一兜底避免渲染崩溃
  const serverMeta = server.server_metadata ?? {}
  const serverInfo = serverMeta.serverInfo ?? {}
  const capabilities = serverMeta.capabilities ?? {}

  // Count the number of tools
  const toolsCount = server.tools?.length || 0

  // Generate a seed for the avatar based on the server title
  const avatarSeed = server.server_title.replace(/\s+/g, "-").toLowerCase()
  const isMine = !!user && user.username === server.owner

  // 在线体验前拦截：需鉴权且未配置自己的凭证（个人/企业共享）时，先弹出凭证配置
  const handleTryOnline = async () => {
    // 聊天链路仍按 owner/name 绑定，取详情响应里的字段
    const chatUrl = `/chat?type=mcp&owner=${encodeURIComponent(server.owner || "")}&name=${encodeURIComponent(server.server_name || "")}`
    if (server.needs_auth && !isMine && server.id) {
      try {
        const status = await getMcpCredentialStatus(server.id)
        if (!status.configured && !status.enterprise?.configured) {
          toast.info("该 MCP 需要配置你自己的 Token 后才能在线体验")
          setCredentialOpen(true)
          return
        }
      } catch {
        // 状态查询失败不拦截，放行交由后端兜底校验
      }
    }
    router.push(chatUrl)
  }

  return (
    <div
      className={cn(
        "pt-app-header relative flex min-h-screen flex-col"
      )}
    >
      <div className="mx-auto w-full max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        {/* Server Metadata */}
        <div className="mb-8 border-b border-border/50 pb-8">
          <div className="flex items-start justify-between gap-6">
            {/* Left: Info */}
            <div className="flex min-w-0 flex-1 items-start gap-4">
              <div className="relative flex-shrink-0">
                <Avatar className="h-14 w-14 rounded-xl ring-1 ring-border/50">
                  <AvatarImage
                    src={server.avatar || `https://api.dicebear.com/9.x/bottts/svg?seed=${avatarSeed}`}
                    alt={server.server_title}
                  />
                  <AvatarFallback className="rounded-xl text-sm font-medium">
                    {server.server_title.substring(0, 2).toUpperCase()}
                  </AvatarFallback>
                </Avatar>
                {isMine && (
                  <button
                    onClick={() => {
                      setAvatarValue(server.avatar || "")
                      setAvatarOpen(true)
                    }}
                    className="bg-primary text-primary-foreground absolute -bottom-1 -right-1 rounded-full p-1 shadow-sm transition-colors hover:bg-primary/90"
                    title="编辑头像"
                  >
                    <Pencil className="h-3 w-3" />
                  </button>
                )}
              </div>
              <div className="min-w-0 flex-1">
                <div className="mb-2 flex items-center gap-3">
                  <h1 className="truncate text-2xl font-bold text-foreground">
                    {server.server_title}
                  </h1>
                  {server.owner && (
                    <span className="text-sm text-muted-foreground">
                      by {server.owner}
                    </span>
                  )}
                </div>
                <p className="mb-3 line-clamp-2 text-sm leading-relaxed text-muted-foreground">
                  {server.description}
                </p>
                <div className="flex flex-wrap items-center gap-2">
                  <Badge variant="outline" className="gap-1 text-xs">
                    <Zap className="h-3 w-3" />
                    {toolsCount} tools
                  </Badge>
                  {serverInfo.version && (
                    <Badge variant="outline" className="gap-1 text-xs">
                      <Info className="h-3 w-3" />
                      v{serverInfo.version}
                    </Badge>
                  )}
                  {serverMeta.protocolVersion && (
                    <Badge variant="outline" className="gap-1 text-xs">
                      <Globe className="h-3 w-3" />
                      {serverMeta.protocolVersion}
                    </Badge>
                  )}
                  {server.server_type && (
                    <Badge
                      variant="secondary"
                      className="gap-1 text-xs"
                    >
                      {server.server_type === "hosted" ? (
                        <Cloud className="h-3 w-3" />
                      ) : server.server_type === "local" ? (
                        <Monitor className="h-3 w-3" />
                      ) : (
                        <Globe className="h-3 w-3" />
                      )}
                      {server.server_type === "hosted"
                        ? "Hosted"
                        : server.server_type === "local"
                          ? "Local"
                          : "Remote"}
                    </Badge>
                  )}
                  {server.needs_auth ? (
                    <Badge
                      variant="outline"
                      className="gap-1 border-amber-500/40 text-xs text-amber-600 dark:text-amber-400"
                    >
                      <KeyRound className="h-3 w-3" />
                      需配置 Token
                    </Badge>
                  ) : (
                    <Badge
                      variant="outline"
                      className="gap-1 border-emerald-500/40 text-xs text-emerald-600 dark:text-emerald-400"
                    >
                      <Zap className="h-3 w-3" />
                      无需 Token
                    </Badge>
                  )}
                </div>
              </div>
            </div>

            {/* Right: Playground Button */}
            <div className="flex items-center gap-2">
              {isMine && server.id && (
                <Button
                  variant="outline"
                  className="gap-2 whitespace-nowrap"
                  onClick={() => {
                    setCoverValue(server.cover || "")
                    setCoverOpen(true)
                  }}
                >
                  <Pencil className="h-4 w-4" />
                  编辑封面
                </Button>
              )}
              {server.needs_auth && server.id && (
                <Button
                  variant="outline"
                  className="gap-2 whitespace-nowrap"
                  onClick={() => setCredentialOpen(true)}
                >
                  <KeyRound className="h-4 w-4" />
                  配置使用
                </Button>
              )}
              <Button className="gap-2 whitespace-nowrap" onClick={handleTryOnline}>
                <Play className="h-4 w-4" weight="fill" />
                在线体验
              </Button>
            </div>
          </div>
        </div>

        {/* Main Content with 3/5 - 2/5 Layout */}
        <div className="flex flex-col gap-8 md:flex-row">
          {/* Tools Section (3/5 width) */}
          <div className="w-full md:w-3/5">
            <Tabs defaultValue="tools" className="w-full">
              <TabsList className="mb-6">
                <TabsTrigger value="tools">Tools ({toolsCount})</TabsTrigger>
                <TabsTrigger value="capabilities">Capabilities</TabsTrigger>
              </TabsList>

              {/* Tools Tab */}
              <TabsContent value="tools" className="space-y-6">
                {server.tools && server.tools.length > 0 ? (
                  server.tools.map((tool, index) => (
                    <div
                      key={index}
                      className="rounded-lg border p-4 transition-shadow hover:shadow-sm"
                    >
                      <div className="flex flex-col gap-4">
                        {/* Tool Info and Parameters */}
                        <div className="w-full">
                          <div className="mb-3 flex items-start justify-between">
                            <h3 className="text-lg font-semibold">
                              {tool.name}
                            </h3>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => handleRunTool(tool.name, tool)}
                              disabled={toolResults[tool.name]?.isLoading}
                            >
                              <Play className="mr-1 h-4 w-4" />
                              Run
                            </Button>
                          </div>
                          <p className="text-muted-foreground mb-3">
                            {tool.description}
                          </p>

                          {tool.inputSchema &&
                            tool.inputSchema.properties &&
                            Object.keys(tool.inputSchema.properties).length >
                              0 && (
                              <div className="mt-3">
                                <h4 className="text-foreground mb-2 text-sm font-medium">
                                  Input Parameters:
                                </h4>
                                <div className="bg-muted/50 rounded border p-3 text-sm">
                                  {tool.inputSchema.properties && (
                                    <div className="space-y-3">
                                      {Object.entries(
                                        tool.inputSchema.properties
                                      ).map(
                                        ([paramName, paramDetails]: [
                                          string,
                                          any,
                                        ]) => (
                                          <div
                                            key={paramName}
                                            className="flex flex-col"
                                          >
                                            <div className="mb-1 flex items-start">
                                              <span className="font-mono text-blue-600">
                                                {paramName}
                                              </span>
                                              {tool.inputSchema.required?.includes(
                                                paramName
                                              ) && (
                                                <span className="ml-1 text-red-500">
                                                  *
                                                </span>
                                              )}
                                              <span className="ml-2 text-gray-500">
                                                ({paramDetails.type})
                                              </span>
                                            </div>
                                            {paramDetails.description && (
                                              <span className="text-muted-foreground mb-1 text-xs">
                                                {paramDetails.description}
                                              </span>
                                            )}
                                            <Input
                                              value={
                                                toolInputs[tool.name]?.[
                                                  paramName
                                                ] || ""
                                              }
                                              onChange={(e) =>
                                                handleInputChange(
                                                  tool.name,
                                                  paramName,
                                                  e.target.value
                                                )
                                              }
                                              placeholder={`Enter ${paramName}`}
                                              className="mt-1"
                                            />
                                          </div>
                                        )
                                      )}
                                    </div>
                                  )}
                                </div>
                              </div>
                            )}
                        </div>

                        {/* Tool Results - Bottom */}
                        <div className="mt-2 w-full border-t pt-4">
                          <h4 className="text-foreground mb-2 text-sm font-medium">
                            Result:
                          </h4>

                          {toolResults[tool.name]?.isLoading && (
                            <div className="flex items-center justify-center py-4">
                              <div className="border-foreground h-6 w-6 animate-spin rounded-full border-b-2"></div>
                            </div>
                          )}

                          {toolResults[tool.name]?.error && (
                            <div className="bg-destructive/10 text-destructive border-destructive/20 rounded border p-3 text-sm">
                              <p className="font-medium">Error:</p>
                              <p>{toolResults[tool.name].error}</p>
                            </div>
                          )}

                          {toolResults[tool.name]?.result && (
                            <div className="bg-muted/50 rounded border p-3">
                              <pre className="bg-muted max-h-[400px] overflow-auto rounded p-2 text-xs">
                                {(() => {
                                  const raw = toolResults[tool.name].result!
                                  try {
                                    const parsed = JSON.parse(raw)
                                    return JSON.stringify(parsed, null, 2)
                                  } catch {
                                    return raw
                                  }
                                })()}
                              </pre>
                            </div>
                          )}

                          {!toolResults[tool.name] && (
                            <div className="bg-muted/30 text-muted-foreground rounded border p-3 text-sm italic">
                              Run the tool to see results here
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="text-muted-foreground py-8 text-center">
                    No tools available for this MCP server.
                  </div>
                )}
              </TabsContent>

              {/* Capabilities Tab */}
              <TabsContent value="capabilities">
                <div className="bg-card rounded-lg border p-4">
                  <h3 className="mb-4 text-lg font-semibold">
                    Server Capabilities
                  </h3>

                  {serverMeta.serverInfo ? (
                    <div className="space-y-4">
                      <div>
                        <h4 className="text-foreground font-medium">
                          Protocol Version
                        </h4>
                        <p className="text-muted-foreground">
                          {serverMeta.protocolVersion || "—"}
                        </p>
                      </div>

                      <div>
                        <h4 className="text-foreground font-medium">
                          Server Info
                        </h4>
                        <div className="border-border mt-2 border-l-2 pl-4">
                          <p>
                            <span className="text-muted-foreground">Name:</span>{" "}
                            {serverInfo.name || "—"}
                          </p>
                          <p>
                            <span className="text-muted-foreground">
                              Version:
                            </span>{" "}
                            {serverInfo.version || "—"}
                          </p>
                        </div>
                      </div>

                      <div>
                        <h4 className="text-foreground font-medium">
                          Supported Features
                        </h4>
                        <div className="border-border mt-2 space-y-2 border-l-2 pl-4">
                          <div className="flex items-center">
                            <div
                              className={`mr-2 h-3 w-3 rounded-full ${capabilities.tools ? "bg-green-500" : "bg-gray-300"}`}
                            ></div>
                            <span>Tools</span>
                          </div>
                          <div className="flex items-center">
                            <div
                              className={`mr-2 h-3 w-3 rounded-full ${capabilities.resources ? "bg-green-500" : "bg-gray-300"}`}
                            ></div>
                            <span>Resources</span>
                          </div>
                          <div className="flex items-center">
                            <div
                              className={`mr-2 h-3 w-3 rounded-full ${capabilities.prompts ? "bg-green-500" : "bg-gray-300"}`}
                            ></div>
                            <span>Prompts</span>
                          </div>
                          <div className="flex items-center">
                            <div
                              className={`mr-2 h-3 w-3 rounded-full ${capabilities.logging ? "bg-green-500" : "bg-gray-300"}`}
                            ></div>
                            <span>Logging</span>
                          </div>
                        </div>
                      </div>

                      {Object.keys(capabilities.experimental || {}).length >
                        0 && (
                        <div>
                          <h4 className="text-foreground font-medium">
                            Experimental Features
                          </h4>
                          <div className="border-border mt-2 border-l-2 pl-4">
                            <pre className="bg-muted/50 overflow-x-auto rounded border p-2 text-sm">
                              {JSON.stringify(
                                capabilities.experimental,
                                null,
                                2
                              )}
                            </pre>
                          </div>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="text-muted-foreground py-8 text-center">
                      该服务器尚未编译，暂无能力信息。
                    </div>
                  )}
                </div>
              </TabsContent>
            </Tabs>
          </div>

          {/* Environment Variables Section (2/5 width) */}
          {serverDetail &&
          serverDetail.envs &&
          Object.keys(serverDetail.envs).length > 0 ? (
            <div className="mt-18 w-full md:w-2/5">
              <Card>
                <CardHeader>
                  <CardTitle>Environment Variables</CardTitle>
                  <CardDescription>
                    此 MCP 服务器所需的环境变量
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {Object.entries(serverDetail.envs).map(([key, value]) => (
                      <div key={key} className="flex flex-col">
                        <label className="text-foreground mb-1 text-sm font-medium">
                          {key}
                        </label>
                        <Input
                          value={value as string}
                          readOnly
                          className="bg-muted/50 cursor-default"
                        />
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>
          ) : null}
        </div>
      </div>

      {serverDetail?.id && (
        <CredentialDialog
          mcpId={serverDetail.id}
          serverTitle={serverDetail.server_title || serverDetail.server_name}
          open={credentialOpen}
          onOpenChange={setCredentialOpen}
        />
      )}

      {/* 编辑头像弹窗（仅创建者可见入口） */}
      <Dialog open={avatarOpen} onOpenChange={setAvatarOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>编辑 MCP 头像</DialogTitle>
            <DialogDescription>
              填写图片 URL（如 https://example.com/logo.png）；
              点「恢复默认」或清空后保存，将回落到默认机器人头像。
            </DialogDescription>
          </DialogHeader>
          <Input
            placeholder="https://example.com/avatar.png"
            value={avatarValue}
            onChange={(e) => setAvatarValue(e.target.value)}
          />
          <DialogFooter className="gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleSaveAvatar(null)}
              disabled={savingAvatar}
            >
              恢复默认
            </Button>
            <Button
              size="sm"
              onClick={() => handleSaveAvatar(avatarValue.trim() || null)}
              disabled={savingAvatar}
            >
              保存
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 编辑封面弹窗（仅创建者可见入口，封面用于首页样式） */}
      <Dialog open={coverOpen} onOpenChange={setCoverOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>编辑 MCP 封面</DialogTitle>
            <DialogDescription>
              填写横幅图片 URL（建议 16:9，如 https://example.com/cover.jpg），
              将用于首页展示样式；点「清除封面」或清空后保存即恢复无封面。
            </DialogDescription>
          </DialogHeader>
          <Input
            placeholder="https://example.com/cover.jpg"
            value={coverValue}
            onChange={(e) => setCoverValue(e.target.value)}
          />
          <DialogFooter className="gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleSaveCover(null)}
              disabled={savingCover}
            >
              清除封面
            </Button>
            <Button
              size="sm"
              onClick={() => handleSaveCover(coverValue.trim() || null)}
              disabled={savingCover}
            >
              保存
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
