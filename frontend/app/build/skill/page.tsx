"use client"
// 作者：langjunnan
// 开发时间：2025年7月23日


import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import LayoutApp from "@/components/layout/layout-app"
import { getSkillCategories, publishSkill, type SkillCategory } from "@/lib/skill"
import { Eye, FileText, Loader2 } from "lucide-react"
import { useEffect, useState } from "react"
import { toast } from "sonner"

export default function BuildSkillPage() {
  const [name, setName] = useState("")
  const [title, setTitle] = useState("")
  const [description, setDescription] = useState("")
  const [categoryId, setCategoryId] = useState<string>("")
  const [sourceUrl, setSourceUrl] = useState("")
  const [body, setBody] = useState("")
  const [categories, setCategories] = useState<SkillCategory[]>([])
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [showPreview, setShowPreview] = useState(false)

  useEffect(() => {
    getSkillCategories()
      .then(setCategories)
      .catch(() => setCategories([]))
  }, [])

  const handlePublish = async () => {
    if (!name.trim()) {
      toast.error("请输入 Skill Name")
      return
    }
    if (!title.trim()) {
      toast.error("请输入标题")
      return
    }
    if (!description.trim()) {
      toast.error("请输入描述（会注入智能体的系统提示）")
      return
    }
    if (!sourceUrl.trim() && !body.trim()) {
      toast.error("请填写来源 URL（含 SKILL.md）或直接粘贴正文")
      return
    }

    setIsSubmitting(true)
    try {
      const skill = await publishSkill({
        name: name.trim(),
        title: title.trim(),
        description: description.trim(),
        category_id: categoryId ? Number(categoryId) : undefined,
        source_url: sourceUrl.trim() || undefined,
        body: body.trim() || undefined,
      })
      toast.success("Skill 发布成功")
      setTimeout(() => {
        window.location.href = `/skills/${skill.owner || "me"}/${skill.name}`
      }, 1200)
    } catch (error) {
      const message = error instanceof Error ? error.message : "发布失败，请重试"
      console.error("发布失败:", error)
      toast.error(message)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <LayoutApp>
      <div className="pt-app-header relative flex min-h-screen flex-col">
        <div className="mx-auto w-full max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
          <div className="flex flex-col gap-8 lg:flex-row">
            {/* Left: Form */}
            <div className="flex-1">
              <h1 className="mb-2 text-3xl font-bold text-foreground">
                Import Skill
              </h1>
              <p className="mb-8 text-muted-foreground">
                Link a skill from GitHub (with a SKILL.md) or paste the content
                directly to make it available on the platform.
              </p>

              <div className="rounded-xl border border-border/50 bg-card p-6">
                {/* Name */}
                <div className="mb-6">
                  <label className="mb-2 block text-sm font-medium text-foreground">
                    Skill Name *
                  </label>
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
                    placeholder="my-skill"
                    className="font-mono"
                  />
                  <p className="mt-2 text-sm text-muted-foreground">
                    小写字母、数字和连字符，最长 64 字符。发布后可通过
                    /skills/你的用户名/{name || "my-skill"} 访问。
                  </p>
                </div>

                {/* Title / Category */}
                <div className="mb-6 grid gap-4 sm:grid-cols-2">
                  <div>
                    <label className="mb-2 block text-sm font-medium text-foreground">
                      标题 *
                    </label>
                    <Input
                      value={title}
                      onChange={(e) => setTitle(e.target.value)}
                      placeholder="我的技能"
                    />
                  </div>
                  <div>
                    <label className="mb-2 block text-sm font-medium text-foreground">
                      分类
                    </label>
                    <select
                      value={categoryId}
                      onChange={(e) => setCategoryId(e.target.value)}
                      className="border-input bg-background flex h-9 w-full rounded-md border px-3 text-sm"
                    >
                      <option value="">不分类</option>
                      {categories.map((c) => (
                        <option key={c.id} value={c.id}>
                          {c.name}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                {/* Description */}
                <div className="mb-6">
                  <label className="mb-2 block text-sm font-medium text-foreground">
                    描述 *（触发说明，会注入智能体系统提示）
                  </label>
                  <Textarea
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    placeholder="这个技能做什么、什么时候触发……（最长 1024 字符）"
                    rows={3}
                  />
                </div>

                {/* Source URL */}
                <div className="mb-6">
                  <label className="mb-2 block text-sm font-medium text-foreground">
                    来源 URL（GitHub 目录，含 SKILL.md）
                  </label>
                  <Input
                    value={sourceUrl}
                    onChange={(e) => setSourceUrl(e.target.value)}
                    placeholder="https://github.com/owner/repo/tree/main/path/to/skill"
                    className="font-mono"
                  />
                  <p className="mt-2 text-sm text-muted-foreground">
                    填写后将自动抓取 SKILL.md 及其引用的 scripts/、references/
                    文件；与正文二选一。
                  </p>
                </div>

                {/* Body */}
                <div className="mb-8">
                  <label className="mb-2 block text-sm font-medium text-foreground">
                    SKILL.md 正文（Markdown）
                  </label>
                  <Textarea
                    value={body}
                    onChange={(e) => setBody(e.target.value)}
                    placeholder={"# My Skill\n\nYou are an expert at…\n\n## When to activate\n- …\n\n## Instructions\n1. …"}
                    rows={10}
                    className="font-mono text-sm"
                  />
                </div>

                {/* Publish Button */}
                <div className="flex justify-end">
                  <Button
                    onClick={handlePublish}
                    disabled={isSubmitting}
                    className="min-w-[140px]"
                  >
                    {isSubmitting ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Publishing...
                      </>
                    ) : (
                      "Publish"
                    )}
                  </Button>
                </div>
              </div>
            </div>

            {/* Right: SKILL.md Reference */}
            <div className="w-full lg:w-[480px]">
              <div className="rounded-xl border border-border/50 bg-card">
                {/* Header */}
                <div className="flex items-center justify-between border-b border-border/50 px-5 py-4">
                  <div className="flex items-center gap-2 text-foreground">
                    <FileText className="h-5 w-5" />
                    <span className="text-lg font-semibold">SKILL.md</span>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setShowPreview(!showPreview)}
                    className="gap-1.5"
                  >
                    <Eye className="h-3.5 w-3.5" />
                    Preview
                  </Button>
                </div>

                {/* Content */}
                <div className="p-5">
                  {showPreview ? (
                    <div className="prose prose-sm dark:prose-invert max-w-none">
                      <h3>{title || "foo-bar"}</h3>
                      <p>{description || "Does foo and bar for the user."}</p>
                      <h4>When to activate</h4>
                      <ul>
                        <li>User asks about foo or bar</li>
                        <li>User needs help with baz</li>
                      </ul>
                      <h4>Instructions</h4>
                      <ol>
                        <li>First, do foo</li>
                        <li>Then apply bar</li>
                        <li>Return baz as the result</li>
                      </ol>
                    </div>
                  ) : (
                    <div className="space-y-4 font-mono text-sm leading-relaxed">
                      {/* YAML Frontmatter */}
                      <div>
                        <p className="mb-2 font-sans text-xs text-muted-foreground">
                          对应表单字段
                        </p>
                        <div className="rounded-lg bg-muted/50 p-4">
                          <p className="text-muted-foreground">---</p>
                          <p>
                            <span className="text-orange-500">name:</span>{" "}
                            {name || "foo-bar"}{" "}
                            <span className="text-muted-foreground">
                              &larr; lowercase, hyphens only, max 64 chars
                            </span>
                          </p>
                          <p>
                            <span className="text-orange-500">description:</span>{" "}
                            {description
                              ? description.slice(0, 60) + (description.length > 60 ? "…" : "")
                              : "Does foo and bar for the user."}{" "}
                            <span className="text-muted-foreground">
                              &larr; max 1024 chars
                            </span>
                          </p>
                          <p className="mt-3 text-muted-foreground">
                            # Markdown body 对应下方「SKILL.md 正文」输入框
                          </p>
                          <p className="text-muted-foreground">---</p>
                        </div>
                      </div>

                      {/* Markdown Body */}
                      <div>
                        <p className="mb-2 font-sans text-xs text-muted-foreground">
                          Markdown Body (skill instructions)
                        </p>
                        <div className="rounded-lg bg-muted/50 p-4">
                          <p>
                            You are an expert at foo. Help users with bar tasks.
                          </p>
                          <p className="mt-3 font-semibold">
                            ## When to activate
                          </p>
                          <p>- User asks about foo or bar</p>
                          <p>- User needs help with baz</p>
                          <p className="mt-3 font-semibold">## Instructions</p>
                          <p>1. First, do foo</p>
                          <p>2. Then apply bar</p>
                          <p>3. Return baz as the result</p>
                        </div>
                      </div>

                      {/* Optional directories */}
                      <div className="border-t border-border/50 pt-4">
                        <p className="mb-1 font-sans text-xs text-muted-foreground">
                          Optional directories:
                        </p>
                        <p className="text-muted-foreground">
                          <span className="text-foreground font-semibold">
                            scripts/
                          </span>{" "}
                          &mdash; executable code agents can run
                        </p>
                        <p className="text-muted-foreground">
                          <span className="text-foreground font-semibold">
                            references/
                          </span>{" "}
                          &mdash; additional docs loaded on demand
                        </p>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </LayoutApp>
  )
}
