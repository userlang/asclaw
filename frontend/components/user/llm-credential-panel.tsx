"use client"
// 作者：langjunnan
// 开发时间：2025年7月23日

import {
  getLlmCredential,
  isLlmUnconfigured,
  type LlmCredentialScope,
  type LlmCredentialStatus,
  saveLlmCredential,
  deleteLlmCredential,
  testLlmCredential,
} from "@/lib/llm"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { cn } from "@/lib/utils"
import { CheckCircle, Eye, EyeSlash, Info, Key, Plug, Trash } from "@phosphor-icons/react"
import { toast } from "sonner"
import { useCallback, useEffect, useState } from "react"

/** 每个作用域一份表单；api_key 留空表示沿用已保存的密钥 */
type ScopeForm = {
  apiKey: string
  baseUrl: string
  chatModel: string
  titleModel: string
}

const emptyForm: ScopeForm = { apiKey: "", baseUrl: "", chatModel: "", titleModel: "" }

function toForm(detail: { baseUrl: string | null; chatModel: string | null; titleModel: string | null }): ScopeForm {
  return {
    apiKey: "",
    baseUrl: detail.baseUrl ?? "",
    chatModel: detail.chatModel ?? "",
    titleModel: detail.titleModel ?? "",
  }
}

/**
 * 模型密钥配置面板（BYOK）：设置页 /user/settings 与个人中心弹窗共用。
 * 自包含数据加载与保存/测试/清除逻辑，外层只负责页面框架。
 */
export function LlmCredentialPanel() {
  const [status, setStatus] = useState<LlmCredentialStatus | null>(null)
  const [scope, setScope] = useState<LlmCredentialScope>("personal")
  const [forms, setForms] = useState<Record<"personal" | "enterprise", ScopeForm>>({
    personal: { ...emptyForm },
    enterprise: { ...emptyForm },
  })
  const [showKey, setShowKey] = useState(false)
  const [saving, setSaving] = useState(false)
  const [testing, setTesting] = useState(false)
  const [loading, setLoading] = useState(true)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const data = await getLlmCredential()
      setStatus(data)
      setForms({
        personal: data.personal.configured ? toForm(data.personal) : { ...emptyForm },
        enterprise: data.enterprise?.configured ? toForm(data.enterprise) : { ...emptyForm },
      })
      if (data.personal.configured) setScope("personal")
      else if (data.enterprise?.configured) setScope("enterprise")
    } catch {
      // http 层已 toast 业务错误
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  const current = forms[scope]
  const currentDetail = scope === "personal" ? status?.personal : status?.enterprise
  const defaults = status?.defaults

  const setField = (field: keyof ScopeForm, value: string) => {
    setForms((prev) => ({ ...prev, [scope]: { ...prev[scope], [field]: value } }))
  }

  const handleSave = async () => {
    if (!current.apiKey.trim() && !currentDetail?.configured) {
      toast.error("请先填写 API Key")
      return
    }
    setSaving(true)
    try {
      await saveLlmCredential(
        {
          api_key: current.apiKey.trim(),
          base_url: current.baseUrl.trim() || undefined,
          chat_model: current.chatModel.trim() || undefined,
          title_model: current.titleModel.trim() || undefined,
        },
        scope
      )
      toast.success(scope === "enterprise" ? "企业共享密钥已保存" : "模型密钥已保存")
      await load()
    } catch {
      // http 层已 toast 业务错误
    } finally {
      setSaving(false)
    }
  }

  const handleTest = async () => {
    if (!current.apiKey.trim()) {
      toast.error(currentDetail?.configured ? "测试需要输入明文 API Key（保存过的仅回显掩码）" : "请先填写 API Key")
      return
    }
    setTesting(true)
    try {
      const result = await testLlmCredential({
        api_key: current.apiKey.trim(),
        base_url: current.baseUrl.trim() || undefined,
        chat_model: current.chatModel.trim() || undefined,
      })
      if (result.ok) {
        toast.success(`连接成功，模型 ${result.model ?? ""} 可用`)
      } else {
        toast.error(`连接失败：${result.error ?? "未知错误"}`)
      }
    } catch {
      // http 层已 toast 业务错误
    } finally {
      setTesting(false)
    }
  }

  const handleDelete = async () => {
    try {
      await deleteLlmCredential(scope)
      toast.success("已清除")
      await load()
    } catch {
      // http 层已 toast 业务错误
    }
  }

  if (loading) {
    return (
      <div className="flex h-40 items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-muted-foreground/20 border-t-primary" />
      </div>
    )
  }

  const unconfigured = status ? isLlmUnconfigured(status) : false

  return (
    <div>
      {unconfigured && (
        <Alert className="mb-6">
          <Info className="h-4 w-4" />
          <AlertDescription>
            聊天与 Agent 调用使用你自己的模型密钥（BYOK）。还没有可用密钥，配置后即可开始对话。
          </AlertDescription>
        </Alert>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Key className="h-5 w-5 text-primary" weight="fill" />
            模型密钥
          </CardTitle>
          <CardDescription>
            支持任意 OpenAI 兼容网关（阿里云百炼 / DeepSeek / Kimi 等）。密钥加密存储，仅本人（或企业全体成员）可用；
            网关地址与模型留空时使用平台默认值。
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-5">
          {/* 作用域切换：个人 always；企业共享仅有关联企业时出现 */}
          {status?.enterprise && (
            <div className="flex items-center gap-2">
              {(
                [
                  { key: "personal", label: "个人密钥" },
                  { key: "enterprise", label: `企业共享（${status.enterprise.name}）` },
                ] as const
              ).map((tab) => (
                <button
                  key={tab.key}
                  type="button"
                  onClick={() => {
                    setScope(tab.key)
                    setShowKey(false)
                  }}
                  className={cn(
                    "rounded-full border px-4 py-1.5 text-sm transition-colors",
                    scope === tab.key
                      ? "border-primary/60 bg-primary/10 text-primary"
                      : "text-muted-foreground hover:text-foreground border-border"
                  )}
                >
                  {tab.label}
                </button>
              ))}
              {currentDetail?.configured && (
                <Badge variant="secondary" className="ml-1">
                  已配置
                </Badge>
              )}
            </div>
          )}

          <div className="space-y-2">
            <Label htmlFor="api-key">API Key</Label>
            <div className="relative">
              <Input
                id="api-key"
                type={showKey ? "text" : "password"}
                placeholder={
                  currentDetail?.configured
                    ? `已保存（${currentDetail.apiKeyMasked}），留空沿用，输入新值则覆盖`
                    : "sk-..."
                }
                value={current.apiKey}
                onChange={(e) => setField("apiKey", e.target.value)}
                className="pr-10"
                autoComplete="off"
              />
              <button
                type="button"
                onClick={() => setShowKey((v) => !v)}
                className="text-muted-foreground hover:text-foreground absolute top-1/2 right-3 -translate-y-1/2"
                tabIndex={-1}
                aria-label={showKey ? "隐藏密钥" : "显示密钥"}
              >
                {showKey ? <EyeSlash className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="base-url">网关地址（OpenAI 兼容）</Label>
            <Input
              id="base-url"
              placeholder={`留空使用平台默认：${defaults?.baseUrl ?? ""}`}
              value={current.baseUrl}
              onChange={(e) => setField("baseUrl", e.target.value)}
              autoComplete="off"
            />
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="chat-model">对话模型</Label>
              <Input
                id="chat-model"
                placeholder={`留空使用默认：${defaults?.chatModel ?? ""}`}
                value={current.chatModel}
                onChange={(e) => setField("chatModel", e.target.value)}
                autoComplete="off"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="title-model">标题模型（选填）</Label>
              <Input
                id="title-model"
                placeholder={`留空使用默认：${defaults?.titleModel ?? ""}`}
                value={current.titleModel}
                onChange={(e) => setField("titleModel", e.target.value)}
                autoComplete="off"
              />
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-3 pt-1">
            <Button onClick={handleSave} disabled={saving}>
              {saving ? "保存中..." : "保存"}
            </Button>
            <Button variant="outline" onClick={handleTest} disabled={testing}>
              <Plug className="mr-1 h-4 w-4" />
              {testing ? "测试中..." : "测试连接"}
            </Button>
            {currentDetail?.configured && (
              <Button variant="ghost" className="text-destructive hover:text-destructive" onClick={handleDelete}>
                <Trash className="mr-1 h-4 w-4" />
                清除
              </Button>
            )}
            {currentDetail?.configured && (
              <span className="text-muted-foreground ml-auto flex items-center gap-1 text-xs">
                <CheckCircle className="h-3.5 w-3.5 text-green-500" weight="fill" />
                当前使用 {currentDetail.apiKeyMasked}
              </span>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
