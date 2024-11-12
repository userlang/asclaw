"use client"
// 作者：langjunnan
// 开发时间：2025年7月23日


import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Textarea } from "@/components/ui/textarea"
import LayoutApp from "@/components/layout/layout-app"
import { useUser } from "@/components/providers/user-provider"
import { publishAgent, updateAgent, type AgentFullDetail } from "@/lib/agent"
import { getMyMcps, type MyMcpItem } from "@/lib/mcp"
import { getMySkills, type MySkillItem } from "@/lib/skill"
import { Bot, Check, Loader2, Wrench, Zap } from "lucide-react"
import { useEffect, useState } from "react"
import { toast } from "sonner"

type Props = {
  // 编辑模式：传 agentId + 初始数据
  editAgent?: AgentFullDetail | null
}

export default function BuildAgentPage({ editAgent }: Props) {
  const isEdit = !!editAgent
  const { user } = useUser()

  const [name, setName] = useState(editAgent?.name ?? "")
  const [title, setTitle] = useState(editAgent?.title ?? "")
  const [description, setDescription] = useState(editAgent?.description ?? "")
  const [systemPrompt, setSystemPrompt] = useState(editAgent?.system_prompt ?? "")
  const [prologue, setPrologue] = useState(editAgent?.prologue ?? "")
  const [isPublic, setIsPublic] = useState(editAgent?.is_public ?? false)
  const [enableSuggest, setEnableSuggest] = useState(editAgent?.enable_suggest ?? false)
  const [enableSearch, setEnableSearch] = useState(editAgent?.enable_search ?? false)

  const [mcps, setMcps] = useState<MyMcpItem[]>([])
  const [skills, setSkills] = useState<MySkillItem[]>([])
  const [selectedMcps, setSelectedMcps] = useState<Set<string>>(
    () => new Set(editAgent?.mcps ?? [])
  )
  const [selectedSkills, setSelectedSkills] = useState<Set<string>>(
    () => new Set(editAgent?.skills ?? [])
  )
  const [isSubmitting, setIsSubmitting] = useState(false)

  useEffect(() => {
    getMyMcps({ page: 1, size: 50 })
      .then((d) => setMcps(d.items))
      .catch(() => setMcps([]))
    getMySkills({ page: 1, size: 50 })
      .then((d) => setSkills(d.items))
      .catch(() => setSkills([]))
  }, [])

  const toggleMcp = (item: MyMcpItem) => {
    const key = `${item.user.username}/${item.server_name}`
    setSelectedMcps((prev) => {
      const next = new Set(prev)
      if (next.has(key)) next.delete(key)
      else next.add(key)
      return next
    })
  }

  const toggleSkill = (item: MySkillItem) => {
    const key = `${item.owner}/${item.name}`
    setSelectedSkills((prev) => {
      const next = new Set(prev)
      if (next.has(key)) next.delete(key)
      else next.add(key)
      return next
    })
  }

  const handleSubmit = async () => {
    if (!name.trim()) {
      toast.error("请输入 Agent Name")
      return
    }
    if (!title.trim()) {
      toast.error("请输入标题")
      return
    }
    if (!systemPrompt.trim()) {
      toast.error("请填写系统提示词（决定这个 Agent 的行为）")
      return
    }

    setIsSubmitting(true)
    try {
      const payload = {
        name: name.trim(),
        title: title.trim(),
        description: description.trim() || undefined,
        system_prompt: systemPrompt.trim(),
        prologue: prologue.trim() || undefined,
        mcps: [...selectedMcps],
        skills: [...selectedSkills],
        enable_search: enableSearch,
        enable_suggest: enableSuggest,
        is_public: isPublic,
      }
      if (isEdit) {
        await updateAgent(editAgent!.id, payload)
        toast.success("Agent 已更新")
        setTimeout(() => {
          window.location.href = `/agent/${editAgent!.owner}/${editAgent!.name}`
        }, 1000)
      } else {
        const agent = await publishAgent(payload)
        toast.success("Agent 创建成功")
        // owner 优先取接口返回值，异常时用当前登录用户名兜底（"me" 不是真实用户名，跳过去必 404）
        const owner = agent.owner || user?.username
        setTimeout(() => {
          window.location.href = owner ? `/agent/${owner}/${agent.name}` : "/agent"
        }, 1000)
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : "保存失败，请重试"
      console.error("保存失败:", error)
      toast.error(message)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <LayoutApp>
      <div className="pt-app-header relative flex min-h-screen flex-col">
        <div className="mx-auto w-full max-w-5xl px-4 py-10 sm:px-6 lg:px-8">
          <h1 className="mb-2 text-3xl font-bold text-foreground">
            {isEdit ? "编辑 Agent" : "创建 Agent"}
          </h1>
          <p className="mb-8 text-muted-foreground">
            配置一个可对话的智能体：系统提示词决定它的行为，绑定 MCP
            让它能调用外部工具，绑定 Skill 注入专业能力。
          </p>

          <div className="space-y-6">
            {/* 基础信息 */}
            <section className="rounded-xl border border-border/50 bg-card p-6">
              <h2 className="mb-4 flex items-center gap-2 text-lg font-semibold">
                <Bot className="h-5 w-5" />
                基础信息
              </h2>
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <Label className="mb-2 block">Agent Name *</Label>
                  <Input
                    value={name}
                    onChange={(e) =>
                      setName(
                        e.target.value
                          .toLowerCase()
                          .replace(/[^a-z0-9][^a-z0-9-]*/g, "-")
                          .replace(/^-+|-+$/g, "")
                      )
                    }
                    placeholder="my-agent"
                    className="font-mono"
                    disabled={isEdit}
                  />
                  <p className="mt-1.5 text-xs text-muted-foreground">
                    小写字母、数字、连字符{isEdit && "（创建后不可修改）"}
                  </p>
                </div>
                <div>
                  <Label className="mb-2 block">标题 *</Label>
                  <Input
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    placeholder="我的智能体"
                  />
                </div>
              </div>
              <div className="mt-4">
                <Label className="mb-2 block">描述</Label>
                <Textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="这个 Agent 能做什么（展示在广场列表）"
                  rows={2}
                />
              </div>
            </section>

            {/* 提示词 */}
            <section className="rounded-xl border border-border/50 bg-card p-6">
              <h2 className="mb-4 text-lg font-semibold">提示词</h2>
              <div className="space-y-4">
                <div>
                  <Label className="mb-2 block">系统提示词 *</Label>
                  <Textarea
                    value={systemPrompt}
                    onChange={(e) => setSystemPrompt(e.target.value)}
                    placeholder={"你是……（角色定义）\n你的能力：……\n工作流程：1. … 2. …\n输出要求：……"}
                    rows={6}
                    className="font-mono text-sm"
                  />
                  <p className="mt-1.5 text-xs text-muted-foreground">
                    聊天时作为主系统提示词注入；绑定的 Skill 会追加在后面。
                  </p>
                </div>
                <div>
                  <Label className="mb-2 block">开场白</Label>
                  <Textarea
                    value={prologue}
                    onChange={(e) => setPrologue(e.target.value)}
                    placeholder="你好！我可以帮你……"
                    rows={2}
                  />
                </div>
              </div>
            </section>

            {/* MCP 绑定 */}
            <section className="rounded-xl border border-border/50 bg-card p-6">
              <h2 className="mb-1 flex items-center gap-2 text-lg font-semibold">
                <Wrench className="h-5 w-5" />
                绑定 MCP（外部工具）
              </h2>
              <p className="mb-4 text-sm text-muted-foreground">
                从「我的 MCP」中选择。聊天时这些服务器的全部工具都会注册给 Agent。
              </p>
              {mcps.length === 0 ? (
                <p className="text-muted-foreground rounded-lg bg-muted/40 px-4 py-6 text-center text-sm">
                  还没有 MCP —— 先到 MCP 模块导入一个
                </p>
              ) : (
                <div className="grid gap-2 sm:grid-cols-2">
                  {mcps.map((m) => {
                    const key = `${m.user.username}/${m.server_name}`
                    const checked = selectedMcps.has(key)
                    return (
                      <button
                        key={m.id}
                        type="button"
                        onClick={() => toggleMcp(m)}
                        className={`flex items-center justify-between rounded-lg border px-4 py-3 text-left transition-colors ${
                          checked
                            ? "border-primary bg-primary/5"
                            : "hover:bg-muted/40 border-border/50"
                        }`}
                      >
                        <div className="min-w-0">
                          <p className="truncate text-sm font-medium">
                            {m.server_title}
                          </p>
                          <p className="text-muted-foreground truncate text-xs">
                            {key}
                          </p>
                        </div>
                        {checked && (
                          <Check className="text-primary h-4 w-4 shrink-0" />
                        )}
                      </button>
                    )
                  })}
                </div>
              )}
            </section>

            {/* Skill 绑定 */}
            <section className="rounded-xl border border-border/50 bg-card p-6">
              <h2 className="mb-1 flex items-center gap-2 text-lg font-semibold">
                <Zap className="h-5 w-5" />
                绑定 Skill（专业能力）
              </h2>
              <p className="mb-4 text-sm text-muted-foreground">
                从「我的 Skill」中选择。聊天时技能描述与 SKILL.md 正文会注入系统提示词。
              </p>
              {skills.length === 0 ? (
                <p className="text-muted-foreground rounded-lg bg-muted/40 px-4 py-6 text-center text-sm">
                  还没有 Skill —— 先到 Skill 模块发布一个
                </p>
              ) : (
                <div className="grid gap-2 sm:grid-cols-2">
                  {skills.map((s) => {
                    const key = `${s.owner}/${s.name}`
                    const checked = selectedSkills.has(key)
                    return (
                      <button
                        key={s.id}
                        type="button"
                        onClick={() => toggleSkill(s)}
                        className={`flex items-center justify-between rounded-lg border px-4 py-3 text-left transition-colors ${
                          checked
                            ? "border-primary bg-primary/5"
                            : "hover:bg-muted/40 border-border/50"
                        }`}
                      >
                        <div className="min-w-0">
                          <p className="truncate text-sm font-medium">
                            {s.title || s.name}
                          </p>
                          <p className="text-muted-foreground truncate text-xs">
                            {key}
                          </p>
                        </div>
                        {checked && (
                          <Check className="text-primary h-4 w-4 shrink-0" />
                        )}
                      </button>
                    )
                  })}
                </div>
              )}
            </section>

            {/* 开关 */}
            <section className="rounded-xl border border-border/50 bg-card p-6">
              <h2 className="mb-4 text-lg font-semibold">能力开关</h2>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium">公开到广场</p>
                    <p className="text-muted-foreground text-xs">
                      开启后所有企业可见；关闭仅本企业与你自己可见
                    </p>
                  </div>
                  <Switch checked={isPublic} onCheckedChange={setIsPublic} />
                </div>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium">联网搜索</p>
                    <p className="text-muted-foreground text-xs">
                      允许 Agent 搜索互联网信息
                    </p>
                  </div>
                  <Switch checked={enableSearch} onCheckedChange={setEnableSearch} />
                </div>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium">问题建议</p>
                    <p className="text-muted-foreground text-xs">
                      回答后给出后续问题建议
                    </p>
                  </div>
                  <Switch checked={enableSuggest} onCheckedChange={setEnableSuggest} />
                </div>
              </div>
            </section>

            {/* 提交 */}
            <div className="flex justify-end gap-3">
              <Button
                variant="outline"
                onClick={() => window.history.back()}
                disabled={isSubmitting}
              >
                取消
              </Button>
              <Button onClick={handleSubmit} disabled={isSubmitting} className="min-w-[140px]">
                {isSubmitting ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    保存中...
                  </>
                ) : isEdit ? (
                  "保存修改"
                ) : (
                  "创建 Agent"
                )}
              </Button>
            </div>
          </div>
        </div>
      </div>
    </LayoutApp>
  )
}
