"use client"

import { Header } from "@/components/layout/header"
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
import { Textarea } from "@/components/ui/textarea"
import { applyEnterprise } from "@/lib/enterprise"
import { BuildingOffice, CheckCircle } from "@phosphor-icons/react"
import Link from "next/link"
import { useState } from "react"

const initialForm = {
  name: "",
  credit_code: "",
  legal_person: "",
  contact_name: "",
  contact_phone: "",
  contact_email: "",
  address: "",
  description: "",
  username: "",
  password: "",
  confirmPassword: "",
}

export default function EnterpriseApplyPage() {
  const [form, setForm] = useState(initialForm)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [submitted, setSubmitted] = useState(false)

  const setField = (field: string, value: string) => {
    setForm((prev) => ({ ...prev, [field]: value }))
    setError(null)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (
      !form.name.trim() ||
      !form.credit_code.trim() ||
      !form.contact_name.trim() ||
      !form.contact_phone.trim()
    ) {
      setError("请填写企业名称、统一社会信用代码、联系人和联系电话")
      return
    }
    if (!form.username.trim()) {
      setError("请设置登录用户名")
      return
    }
    if (form.password.length < 6) {
      setError("登录密码至少 6 位")
      return
    }
    if (form.password !== form.confirmPassword) {
      setError("两次输入的密码不一致")
      return
    }

    setSubmitting(true)
    try {
      await applyEnterprise({
        name: form.name.trim(),
        credit_code: form.credit_code.trim(),
        legal_person: form.legal_person.trim() || undefined,
        contact_name: form.contact_name.trim(),
        contact_phone: form.contact_phone.trim(),
        contact_email: form.contact_email.trim() || undefined,
        address: form.address.trim() || undefined,
        description: form.description.trim() || undefined,
        username: form.username.trim(),
        password: form.password,
      })
      setSubmitted(true)
    } catch {
      // 错误提示由 http 拦截器统一 toast
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <>
      <Header />
      <div className="bg-muted/20 min-h-screen pt-24 pb-12">
      <div className="mx-auto w-full max-w-3xl px-4 sm:px-6">
        <div className="mb-8 text-center">
          <div className="mb-4 inline-flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-500 via-purple-500 to-fuchsia-500 shadow-sm">
            <BuildingOffice className="h-7 w-7 text-white" weight="fill" />
          </div>
          <h1 className="text-2xl font-bold">申请入驻平台</h1>
          <p className="text-muted-foreground mt-2 text-sm">
            提交企业资质信息，管理员审核通过后即可使用企业账号登录
          </p>
        </div>

        {submitted ? (
          <Card>
            <CardContent className="flex flex-col items-center gap-4 py-12 text-center">
              <CheckCircle className="h-14 w-14 text-green-500" weight="fill" />
              <div>
                <p className="text-lg font-semibold">入驻申请已提交</p>
                <p className="text-muted-foreground mt-1 text-sm">
                  我们会尽快完成审核，审核通过后企业账号即可登录平台
                </p>
              </div>
              <div className="flex gap-3">
                <Button asChild variant="outline">
                  <Link href="/">返回首页</Link>
                </Button>
                <Button asChild>
                  <Link href="/enterprise/login">前往企业登录</Link>
                </Button>
              </div>
            </CardContent>
          </Card>
        ) : (
          <form onSubmit={handleSubmit}>
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">企业信息</CardTitle>
                <CardDescription>请填写与企业资质相关的真实信息</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                  <div className="space-y-2">
                    <Label>
                      企业名称 <span className="text-red-500">*</span>
                    </Label>
                    <Input
                      placeholder="营业执照上的企业名称"
                      value={form.name}
                      onChange={(e) => setField("name", e.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>
                      统一社会信用代码（营业执照）{" "}
                      <span className="text-red-500">*</span>
                    </Label>
                    <Input
                      placeholder="18 位统一社会信用代码"
                      value={form.credit_code}
                      onChange={(e) => setField("credit_code", e.target.value)}
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                  <div className="space-y-2">
                    <Label>法定代表人</Label>
                    <Input
                      placeholder="选填"
                      value={form.legal_person}
                      onChange={(e) => setField("legal_person", e.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>注册地址</Label>
                    <Input
                      placeholder="选填"
                      value={form.address}
                      onChange={(e) => setField("address", e.target.value)}
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                  <div className="space-y-2">
                    <Label>
                      联系人 <span className="text-red-500">*</span>
                    </Label>
                    <Input
                      value={form.contact_name}
                      onChange={(e) => setField("contact_name", e.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>
                      联系电话 <span className="text-red-500">*</span>
                    </Label>
                    <Input
                      value={form.contact_phone}
                      onChange={(e) => setField("contact_phone", e.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>联系邮箱</Label>
                    <Input
                      type="email"
                      placeholder="选填"
                      value={form.contact_email}
                      onChange={(e) => setField("contact_email", e.target.value)}
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label>企业简介</Label>
                  <Textarea
                    rows={3}
                    placeholder="简单介绍企业主营业务（选填）"
                    className="resize-none"
                    value={form.description}
                    onChange={(e) => setField("description", e.target.value)}
                  />
                </div>
              </CardContent>
            </Card>

            <Card className="mt-4">
              <CardHeader>
                <CardTitle className="text-lg">设置企业账号</CardTitle>
                <CardDescription>
                  用于审核通过后登录平台，请妥善保管
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                  <div className="space-y-2">
                    <Label>
                      登录用户名 <span className="text-red-500">*</span>
                    </Label>
                    <Input
                      placeholder="字母、数字或下划线"
                      value={form.username}
                      onChange={(e) => setField("username", e.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>
                      登录密码 <span className="text-red-500">*</span>
                    </Label>
                    <Input
                      type="password"
                      placeholder="至少 6 位"
                      value={form.password}
                      onChange={(e) => setField("password", e.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>
                      确认密码 <span className="text-red-500">*</span>
                    </Label>
                    <Input
                      type="password"
                      value={form.confirmPassword}
                      onChange={(e) =>
                        setField("confirmPassword", e.target.value)
                      }
                    />
                  </div>
                </div>

                {error && <p className="text-sm text-red-500">{error}</p>}

                <Button type="submit" className="w-full" disabled={submitting}>
                  {submitting ? "提交中..." : "提交入驻申请"}
                </Button>

                <p className="text-muted-foreground text-center text-sm">
                  已有企业账号？{" "}
                  <Link
                    href="/enterprise/login"
                    className="text-primary hover:underline"
                  >
                    前往登录
                  </Link>
                </p>
              </CardContent>
            </Card>
          </form>
        )}
      </div>
      </div>
    </>
  )
}
