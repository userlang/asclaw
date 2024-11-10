"use client"
// 作者：langjunnan
// 开发时间：2025年7月23日

// 广场 MCP 凭证配置弹窗：MCP 为模板，token 各自配置（加密存储）
// 支持个人凭证 / 企业共享凭证（企业凭证对该企业下所有用户生效）

import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import {
  CredentialScope,
  deleteMcpCredential,
  getMcpCredentialStatus,
  McpCredentialStatus,
  saveMcpCredential,
} from "@/lib/mcp"
import { Building2, KeyRound, Loader2, Trash2, UserRound } from "lucide-react"
import { useEffect, useState } from "react"
import { toast } from "sonner"

interface CredentialDialogProps {
  mcpId: number
  serverTitle: string
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function CredentialDialog({ mcpId, serverTitle, open, onOpenChange }: CredentialDialogProps) {
  const [status, setStatus] = useState<McpCredentialStatus | null>(null)
  const [values, setValues] = useState<Record<string, string>>({})
  const [scope, setScope] = useState<CredentialScope>("personal")
  const [isSaving, setIsSaving] = useState(false)

  useEffect(() => {
    if (!open) return
    let cancelled = false
    getMcpCredentialStatus(mcpId)
      .then((res) => {
        if (!cancelled) setStatus(res)
      })
      .catch(() => toast.error("获取凭证状态失败"))
    return () => {
      cancelled = true
    }
  }, [open, mcpId])

  const handleSave = async () => {
    const filled: Record<string, string> = {}
    for (const key of status?.auth_keys ?? []) {
      const v = values[key]?.trim()
      if (v) filled[key] = v
    }
    if (Object.keys(filled).length === 0) {
      toast.error("请至少填写一项凭证")
      return
    }
    try {
      setIsSaving(true)
      await saveMcpCredential(mcpId, filled, scope)
      toast.success(scope === "enterprise" ? "企业共享凭证已保存（加密存储）" : "凭证已保存（加密存储）")
      const res = await getMcpCredentialStatus(mcpId)
      setStatus(res)
      setValues({})
    } catch {
      toast.error("保存失败，请重试")
    } finally {
      setIsSaving(false)
    }
  }

  const handleClear = async (clearScope: CredentialScope) => {
    try {
      setIsSaving(true)
      await deleteMcpCredential(mcpId, clearScope)
      toast.success(clearScope === "enterprise" ? "已清除企业共享凭证" : "已清除个人凭证")
      const res = await getMcpCredentialStatus(mcpId)
      setStatus(res)
    } catch {
      toast.error("清除失败，请重试")
    } finally {
      setIsSaving(false)
    }
  }

  const hasEnterprise = !!status?.enterprise

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <KeyRound className="h-4 w-4 text-primary" />
            配置 {serverTitle} 的凭证
          </DialogTitle>
          <DialogDescription>
            该 MCP 需要鉴权。填写你自己在官方平台注册的 token，加密存储、仅本人（或企业成员）可用，
            调用时不会使用发布者的凭证。
          </DialogDescription>
        </DialogHeader>

        {!status ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
          </div>
        ) : (
          <div className="space-y-3">
            {/* 凭证范围：有关联企业时才可选企业共享 */}
            {hasEnterprise && (
              <div className="grid grid-cols-2 gap-2">
                <button
                  onClick={() => setScope("personal")}
                  className={`flex items-center justify-center gap-1.5 rounded-md border px-3 py-2 text-xs font-medium transition-colors ${
                    scope === "personal"
                      ? "border-primary bg-primary/5 text-primary"
                      : "text-muted-foreground hover:bg-accent"
                  }`}
                >
                  <UserRound className="h-3.5 w-3.5" />
                  仅我自己
                </button>
                <button
                  onClick={() => setScope("enterprise")}
                  className={`flex items-center justify-center gap-1.5 rounded-md border px-3 py-2 text-xs font-medium transition-colors ${
                    scope === "enterprise"
                      ? "border-primary bg-primary/5 text-primary"
                      : "text-muted-foreground hover:bg-accent"
                  }`}
                >
                  <Building2 className="h-3.5 w-3.5" />
                  {status.enterprise?.name}（全员共享）
                </button>
              </div>
            )}

            {/* 已配置状态提示 */}
            {status.configured && scope === "personal" && (
              <div className="rounded-md bg-emerald-500/10 px-3 py-2 text-xs text-emerald-600 dark:text-emerald-400">
                ✓ 已配置个人凭证，重新填写将覆盖
              </div>
            )}
            {status.enterprise?.configured && scope === "enterprise" && (
              <div className="rounded-md bg-emerald-500/10 px-3 py-2 text-xs text-emerald-600 dark:text-emerald-400">
                ✓ 企业已配置共享凭证，重新填写将覆盖
              </div>
            )}

            {status.auth_keys.length === 0 ? (
              <p className="text-muted-foreground text-sm">未检测到需要配置的鉴权字段</p>
            ) : (
              status.auth_keys.map((key) => (
                <div key={key} className="space-y-1.5">
                  <label className="text-foreground text-xs font-medium">
                    {key.startsWith("url:") ? `URL 参数 ${key.slice(4)}` : key}
                  </label>
                  <Input
                    type="password"
                    placeholder={
                      key.startsWith("url:")
                        ? `填入 ${key.slice(4)} 参数的值，如高德开放平台申请的 key`
                        : "粘贴完整 header 值，如 Bearer ghp_xxxx"
                    }
                    value={values[key] ?? ""}
                    onChange={(e) => setValues((prev) => ({ ...prev, [key]: e.target.value }))}
                  />
                </div>
              ))
            )}
          </div>
        )}

        <DialogFooter className="gap-2">
          {status?.configured && scope === "personal" && (
            <Button variant="outline" size="sm" onClick={() => handleClear("personal")} disabled={isSaving}>
              <Trash2 className="mr-1 h-3.5 w-3.5" />
              清除个人
            </Button>
          )}
          {status?.enterprise?.configured && scope === "enterprise" && (
            <Button variant="outline" size="sm" onClick={() => handleClear("enterprise")} disabled={isSaving}>
              <Trash2 className="mr-1 h-3.5 w-3.5" />
              清除企业
            </Button>
          )}
          <Button size="sm" onClick={handleSave} disabled={isSaving || !status}>
            {isSaving && <Loader2 className="mr-1 h-3.5 w-3.5 animate-spin" />}
            保存{scope === "enterprise" ? "（企业）" : ""}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
