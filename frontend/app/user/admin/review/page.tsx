"use client"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import {
  EnterpriseItem,
  ENTERPRISE_STATUS,
  deleteEnterprise,
  getEnterpriseList,
  reviewEnterprise,
  updateEnterprise,
} from "@/lib/enterprise"
import AdminLayout from "@/components/layout/admin-layout"
import { useUser } from "@/components/providers/user-provider"
import {
  CheckCircle,
  PencilSimple,
  ArrowClockwise,
  Trash,
  XCircle,
} from "@phosphor-icons/react"
import { useCallback, useEffect, useState } from "react"

const PAGE_SIZE = 10

const statusBadge = (status: number) => {
  if (status === ENTERPRISE_STATUS.APPROVED)
    return <Badge className="bg-green-100 text-green-700">已通过</Badge>
  if (status === ENTERPRISE_STATUS.REJECTED)
    return <Badge variant="destructive">已拒绝</Badge>
  return <Badge variant="secondary">待审核</Badge>
}

export default function ReviewPage() {
  const { user } = useUser()
  const [items, setItems] = useState<EnterpriseItem[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [statusFilter, setStatusFilter] = useState<string>("all")
  const [keyword, setKeyword] = useState("")
  const [loading, setLoading] = useState(false)
  const [selected, setSelected] = useState<Set<number>>(new Set())

  // 编辑弹窗
  const [editing, setEditing] = useState<EnterpriseItem | null>(null)
  const [editForm, setEditForm] = useState({
    name: "",
    credit_code: "",
    contact_name: "",
    contact_phone: "",
    username: "",
    password: "",
  })
  const [saving, setSaving] = useState(false)

  const isAdmin = !!user && (user.is_staff || user.is_superuser)

  const load = useCallback(async () => {
    if (!isAdmin) return
    setLoading(true)
    try {
      const res = await getEnterpriseList({
        status:
          statusFilter === "all" ? undefined : Number.parseInt(statusFilter, 10),
        keyword: keyword.trim() || undefined,
        page,
        size: PAGE_SIZE,
      })
      setItems(res.items)
      setTotal(res.total)
      setSelected(new Set())
    } catch {
      // toast 由拦截器处理
    } finally {
      setLoading(false)
    }
  }, [isAdmin, statusFilter, keyword, page])

  useEffect(() => {
    load()
  }, [load])

  const toggleSelect = (id: number) => {
    setSelected((prev) => {
      const next = new Set(prev)
      if (next.has(id)) {
        next.delete(id)
      } else {
        next.add(id)
      }
      return next
    })
  }

  const toggleSelectAll = () => {
    setSelected((prev) =>
      prev.size === items.length ? new Set() : new Set(items.map((i) => i.id))
    )
  }

  const handleReview = async (pks: number[], status: 1 | 2) => {
    if (pks.length === 0) return
    let reject_reason: string | undefined
    if (status === 2) {
      reject_reason = window.prompt("请输入拒绝原因（将展示给商家）") || undefined
      if (reject_reason === undefined) return
    }
    try {
      await reviewEnterprise(pks, status, reject_reason)
      await load()
    } catch {
      // toast 由拦截器处理
    }
  }

  const handleDelete = async (pks: number[]) => {
    if (pks.length === 0) return
    if (!window.confirm(`确认删除选中的 ${pks.length} 条企业记录？删除后不可恢复`))
      return
    try {
      await deleteEnterprise(pks)
      await load()
    } catch {
      // toast 由拦截器处理
    }
  }

  const openEdit = (item: EnterpriseItem) => {
    setEditing(item)
    setEditForm({
      name: item.name,
      credit_code: item.credit_code,
      contact_name: item.contact_name,
      contact_phone: item.contact_phone,
      username: item.username,
      password: "",
    })
  }

  const handleSaveEdit = async () => {
    if (!editing) return
    setSaving(true)
    try {
      await updateEnterprise(editing.id, {
        name: editForm.name.trim(),
        credit_code: editForm.credit_code.trim(),
        contact_name: editForm.contact_name.trim(),
        contact_phone: editForm.contact_phone.trim(),
        username: editForm.username.trim(),
        password: editForm.password || undefined,
      })
      setEditing(null)
      await load()
    } catch {
      // toast 由拦截器处理
    } finally {
      setSaving(false)
    }
  }

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE))

  return (
    <AdminLayout>
      <div className="mx-auto w-full max-w-7xl pb-6">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">商家审核</h1>
          <p className="text-muted-foreground mt-1 text-sm">
            审核企业入驻申请，通过后企业账号方可登录平台
          </p>
        </div>
        <Button variant="outline" onClick={load} disabled={loading}>
          <ArrowClockwise className="mr-1 h-4 w-4" />
          刷新
        </Button>
      </div>

      {/* 筛选栏 */}
      <div className="mb-4 flex flex-wrap items-center gap-3">
        <div className="flex gap-1 rounded-lg border p-1">
          {[
            { key: "all", label: "全部" },
            { key: "0", label: "待审核" },
            { key: "1", label: "已通过" },
            { key: "2", label: "已拒绝" },
          ].map((s) => (
            <button
              key={s.key}
              onClick={() => {
                setStatusFilter(s.key)
                setPage(1)
              }}
              className={`rounded-md px-3 py-1.5 text-sm transition-colors ${
                statusFilter === s.key
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-muted"
              }`}
            >
              {s.label}
            </button>
          ))}
        </div>
        <Input
          placeholder="搜索企业名称..."
          className="h-9 w-64"
          value={keyword}
          onChange={(e) => {
            setKeyword(e.target.value)
            setPage(1)
          }}
        />
      </div>

      {/* 批量操作栏 */}
      {selected.size > 0 && (
        <div className="border-primary/30 bg-primary/5 mb-4 flex items-center justify-between rounded-lg border px-4 py-2">
          <span className="text-sm">已选中 {selected.size} 条</span>
          <div className="flex gap-2">
            <Button
              size="sm"
              className="gap-1"
              onClick={() => handleReview([...selected], 1)}
            >
              <CheckCircle className="h-4 w-4" weight="fill" />
              批量通过
            </Button>
            <Button
              size="sm"
              variant="outline"
              className="gap-1"
              onClick={() => handleReview([...selected], 2)}
            >
              <XCircle className="h-4 w-4" />
              批量拒绝
            </Button>
            <Button
              size="sm"
              variant="destructive"
              className="gap-1"
              onClick={() => handleDelete([...selected])}
            >
              <Trash className="h-4 w-4" />
              批量删除
            </Button>
          </div>
        </div>
      )}

      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-10">
                  <input
                    type="checkbox"
                    className="accent-primary h-4 w-4"
                    checked={items.length > 0 && selected.size === items.length}
                    onChange={toggleSelectAll}
                  />
                </TableHead>
                <TableHead>企业名称</TableHead>
                <TableHead>信用代码</TableHead>
                <TableHead>联系人</TableHead>
                <TableHead>账号</TableHead>
                <TableHead>状态</TableHead>
                <TableHead>申请时间</TableHead>
                <TableHead className="text-right">操作</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={8} className="py-10 text-center">
                    <div className="border-primary mx-auto h-6 w-6 animate-spin rounded-full border-b-2" />
                  </TableCell>
                </TableRow>
              ) : items.length === 0 ? (
                <TableRow>
                  <TableCell
                    colSpan={8}
                    className="text-muted-foreground py-10 text-center"
                  >
                    暂无企业入驻申请
                  </TableCell>
                </TableRow>
              ) : (
                items.map((item) => (
                  <TableRow key={item.id}>
                    <TableCell>
                      <input
                        type="checkbox"
                        className="accent-primary h-4 w-4"
                        checked={selected.has(item.id)}
                        onChange={() => toggleSelect(item.id)}
                      />
                    </TableCell>
                    <TableCell>
                      <div className="font-medium">{item.name}</div>
                      {item.description && (
                        <div className="text-muted-foreground line-clamp-1 max-w-[200px] text-xs">
                          {item.description}
                        </div>
                      )}
                    </TableCell>
                    <TableCell className="font-mono text-xs">
                      {item.credit_code}
                    </TableCell>
                    <TableCell>
                      <div>{item.contact_name}</div>
                      <div className="text-muted-foreground text-xs">
                        {item.contact_phone}
                      </div>
                    </TableCell>
                    <TableCell className="font-mono text-xs">
                      {item.username}
                    </TableCell>
                    <TableCell>{statusBadge(item.status)}</TableCell>
                    <TableCell className="text-muted-foreground text-xs">
                      {item.created_time}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-1">
                        {item.status === ENTERPRISE_STATUS.PENDING && (
                          <>
                            <Button
                              size="sm"
                              variant="outline"
                              className="gap-1 text-green-600"
                              onClick={() => handleReview([item.id], 1)}
                            >
                              <CheckCircle className="h-3.5 w-3.5" weight="fill" />
                              通过
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              className="gap-1 text-red-600"
                              onClick={() => handleReview([item.id], 2)}
                            >
                              <XCircle className="h-3.5 w-3.5" />
                              拒绝
                            </Button>
                          </>
                        )}
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => openEdit(item)}
                        >
                          <PencilSimple className="h-3.5 w-3.5" />
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          className="text-red-600"
                          onClick={() => handleDelete([item.id])}
                        >
                          <Trash className="h-3.5 w-3.5" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* 分页 */}
      {total > PAGE_SIZE && (
        <div className="mt-4 flex items-center justify-center gap-2">
          <Button
            variant="outline"
            size="sm"
            disabled={page <= 1}
            onClick={() => setPage((p) => p - 1)}
          >
            上一页
          </Button>
          <span className="text-muted-foreground text-sm">
            {page} / {totalPages}
          </span>
          <Button
            variant="outline"
            size="sm"
            disabled={page >= totalPages}
            onClick={() => setPage((p) => p + 1)}
          >
            下一页
          </Button>
        </div>
      )}

      {/* 编辑弹窗 */}
      <Dialog open={!!editing} onOpenChange={(open) => !open && setEditing(null)}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>修改企业信息</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <Label>企业名称</Label>
                <Input
                  value={editForm.name}
                  onChange={(e) =>
                    setEditForm((p) => ({ ...p, name: e.target.value }))
                  }
                />
              </div>
              <div className="space-y-1.5">
                <Label>信用代码</Label>
                <Input
                  value={editForm.credit_code}
                  onChange={(e) =>
                    setEditForm((p) => ({ ...p, credit_code: e.target.value }))
                  }
                />
              </div>
              <div className="space-y-1.5">
                <Label>联系人</Label>
                <Input
                  value={editForm.contact_name}
                  onChange={(e) =>
                    setEditForm((p) => ({ ...p, contact_name: e.target.value }))
                  }
                />
              </div>
              <div className="space-y-1.5">
                <Label>联系电话</Label>
                <Input
                  value={editForm.contact_phone}
                  onChange={(e) =>
                    setEditForm((p) => ({ ...p, contact_phone: e.target.value }))
                  }
                />
              </div>
              <div className="space-y-1.5">
                <Label>登录用户名</Label>
                <Input
                  value={editForm.username}
                  onChange={(e) =>
                    setEditForm((p) => ({ ...p, username: e.target.value }))
                  }
                />
              </div>
              <div className="space-y-1.5">
                <Label>重置密码（留空不改）</Label>
                <Input
                  type="password"
                  placeholder="至少 6 位"
                  value={editForm.password}
                  onChange={(e) =>
                    setEditForm((p) => ({ ...p, password: e.target.value }))
                  }
                />
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditing(null)}>
              取消
            </Button>
            <Button onClick={handleSaveEdit} disabled={saving}>
              {saving ? "保存中..." : "保存"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 未登录管理员提示（auth-guard 会跳转，这里兜底） */}
      {!isAdmin && (
        <p className="text-muted-foreground mt-8 text-center text-sm">
          需要管理员权限
        </p>
      )}
    </div>
    </AdminLayout>
  )
}
