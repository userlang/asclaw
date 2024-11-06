"use client"

import { Header } from "@/components/layout/header"
import { useUser } from "@/components/providers/user-provider"
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
import { enterpriseLogin } from "@/lib/enterprise"
import { SealCheck, SignIn } from "@phosphor-icons/react"
import Link from "next/link"
import { useRouter, useSearchParams } from "next/navigation"
import { Suspense, useState } from "react"

function LoginContent() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const { login } = useUser()
  const [username, setUsername] = useState("")
  const [password, setPassword] = useState("")
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [loggedIn, setLoggedIn] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!username.trim() || !password) {
      setError("请输入用户名和密码")
      return
    }
    setSubmitting(true)
    setError(null)
    try {
      const data = await enterpriseLogin({
        username: username.trim(),
        password,
      })

      // 与平台统一的用户体系：token + 用户信息（SPA 内即时生效）
      login(data.access_token, {
        id: String(data.user.id),
        nickname: data.user.nickname || data.user.username,
        avatar: data.user.avatar || "",
        email: data.user.email || "",
        daily_message_count: 0,
        is_staff: data.user.is_staff ?? false,
        is_superuser: data.user.is_superuser ?? false,
      })

      setLoggedIn(true)
      const callbackUrl = searchParams.get("callbackUrl")
      setTimeout(() => router.push(callbackUrl || "/"), 600)
    } catch {
      // 错误提示由 http 拦截器统一 toast
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <>
      <Header />
      <div className="bg-muted/20 flex min-h-screen items-center justify-center px-4 pt-24 pb-12">
        <div className="w-full max-w-md">
          <Card>
            <CardHeader className="text-center">
              <div className="mb-2 flex justify-center">
                <span className="bg-gradient-to-r from-indigo-500 via-purple-500 to-fuchsia-500 bg-clip-text text-2xl font-bold tracking-tight text-transparent">
                  AsClaw
                </span>
              </div>
              <CardTitle className="text-xl">企业登录</CardTitle>
              <CardDescription>入驻审核通过的企业账号登录平台</CardDescription>
            </CardHeader>
            <CardContent>
              {loggedIn ? (
                <div className="flex flex-col items-center gap-3 py-6 text-center">
                  <SealCheck className="h-12 w-12 text-green-500" weight="fill" />
                  <p className="font-medium">登录成功，正在进入平台...</p>
                </div>
              ) : (
                <form onSubmit={handleSubmit} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="username">用户名</Label>
                    <Input
                      id="username"
                      placeholder="入驻时设置的用户名"
                      value={username}
                      onChange={(e) => {
                        setUsername(e.target.value)
                        setError(null)
                      }}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="password">密码</Label>
                    <Input
                      id="password"
                      type="password"
                      value={password}
                      onChange={(e) => {
                        setPassword(e.target.value)
                        setError(null)
                      }}
                    />
                  </div>
                  {error && <p className="text-sm text-red-500">{error}</p>}
                  <Button
                    type="submit"
                    className="w-full gap-2"
                    disabled={submitting}
                  >
                    <SignIn className="h-4 w-4" weight="fill" />
                    {submitting ? "登录中..." : "登录"}
                  </Button>
                  <p className="text-muted-foreground text-center text-sm">
                    还没有入驻？{" "}
                    <Link
                      href="/enterprise/apply"
                      className="text-primary hover:underline"
                    >
                      申请入驻
                    </Link>
                  </p>
                </form>
              )}
            </CardContent>
          </Card>

          <div className="text-muted-foreground mt-6 text-center text-xs leading-relaxed">
            登录即表示你同意我们的{" "}
            <Link href="/terms" className="text-foreground hover:underline">
              服务条款
            </Link>{" "}
            和{" "}
            <Link href="/privacy" className="text-foreground hover:underline">
              隐私政策
            </Link>
          </div>
          <div className="mt-3 text-center">
            <Link
              href="/"
              className="text-muted-foreground hover:text-foreground text-sm transition-colors"
            >
              &larr; 返回首页
            </Link>
          </div>
        </div>
      </div>
    </>
  )
}

export default function EnterpriseLoginPage() {
  return (
    <Suspense>
      <LoginContent />
    </Suspense>
  )
}
