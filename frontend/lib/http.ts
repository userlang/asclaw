// 作者：langjunnan
// 开发时间：2025年7月23日

import { toast } from "@/components/ui/toast";
import axios, { AxiosInstance } from "axios";


/** 统一响应体 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export interface ApiResponse<T = any> {
  code: number
  msg: string
  data: T
}

/** 业务异常 */
export class BusinessError extends Error {
  code: number
  constructor(code: number, msg: string) {
    super(msg)
    this.code = code
    this.name = "BusinessError"
  }
}

const instance: AxiosInstance = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_BASE_URL,
  timeout: 30000,
  headers: { "Content-Type": "application/json" },
})

// ---- 请求拦截：自动携带 token ----
instance.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("auth_token")
    if (token) {
      config.headers["Authorization"] = `Bearer ${token}`
    }
  }
  return config
})

/** 登录失效统一处理：清 token、友好提示并跳登录页（登录后跳回原页面） */
function handleAuthExpired() {
  if (typeof window === "undefined") return
  // 登录页本身不发跳转，避免死循环
  if (window.location.pathname.startsWith("/enterprise/login")) return
  localStorage.removeItem("auth_token")
  toast({
    title: "请先登录",
    description: "您还未登录或登录状态已失效，正在跳转登录页…",
    status: "error",
  })
  setTimeout(() => {
    window.location.href = `/enterprise/login?callbackUrl=${encodeURIComponent(window.location.pathname)}`
  }, 1200)
}

// ---- 响应拦截：统一错误处理 ----
instance.interceptors.response.use(
  (response) => {
    const res = response.data as ApiResponse

    // 业务 code !== 200 视为错误
    if (res.code !== 200) {
      // 业务 code 401（HTTP 200 形态）同样视为登录失效
      if (res.code === 401) {
        handleAuthExpired()
      }
      const errMsg = res.msg || "请求失败"
      toast({ title: "请求失败", description: errMsg, status: "error" })
      return Promise.reject(new BusinessError(res.code, errMsg))
    }

    return response
  },
  (error) => {
    const status: number | undefined = error.response?.status

    // HTTP 401：未登录/token 失效 → 友好提示并跳登录页，不再重复弹原始报错
    if (status === 401) {
      handleAuthExpired()
      return Promise.reject(new BusinessError(401, "登录已失效，请重新登录"))
    }

    let errMsg: string
    if (!error.response) {
      // 网络错误 / 超时
      errMsg =
        error.code === "ECONNABORTED"
          ? "请求超时，请稍后重试"
          : "网络异常，请检查网络连接"
    } else {
      // 优先使用后端返回的业务错误信息（如 403 的业务权限提示）
      const serverMsg = error.response.data?.msg
      if (serverMsg) {
        errMsg = serverMsg
      } else {
        // HTTP status 错误
        const messages: Record<number, string> = {
          400: "请求参数错误",
          403: "没有权限访问",
          404: "请求资源不存在",
          500: "服务器内部错误",
          502: "网关错误",
          503: "服务不可用",
        }
        errMsg = messages[status as number] || `请求失败 (${status})`
      }
    }

    toast({ title: "请求失败", description: errMsg, status: "error" })
    return Promise.reject(new BusinessError(error.response?.status || 0, errMsg))
  }
)

/** 过滤掉 null / undefined 的参数 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
function filterParams(params: Record<string, any>): Record<string, any> {
  return Object.fromEntries(
    Object.entries(params).filter(([, v]) => v !== undefined && v !== null)
  )
}

/**
 * 统一请求工具
 *
 * 用法:
 *   http.get<UserItem>('/api/user', { id: 1 })
 *   http.post<null>('/api/user', { name: 'test' })
 *
 * 返回值直接是响应体中的 data 字段
 */
const http = {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  async get<T = any>(url: string, params: Record<string, any> = {}): Promise<T> {
    const res = await instance.get<ApiResponse<T>>(url, {
      params: filterParams(params),
    })
    return res.data.data
  },

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  async post<T = any>(url: string, data: any = {}): Promise<T> {
    const res = await instance.post<ApiResponse<T>>(url, data)
    return res.data.data
  },

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  async put<T = any>(url: string, data: any = {}): Promise<T> {
    const res = await instance.put<ApiResponse<T>>(url, data)
    return res.data.data
  },

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  async delete<T = any>(url: string, params: Record<string, any> = {}): Promise<T> {
    const res = await instance.delete<ApiResponse<T>>(url, {
      params: filterParams(params),
    })
    return res.data.data
  },

  /** DELETE 请求，携带 body（用于批量删除等场景） */
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  async deleteBody<T = any>(url: string, data: any = {}): Promise<T> {
    const res = await instance.delete<ApiResponse<T>>(url, { data })
    return res.data.data
  },

  /** 需要拿到完整响应体 { code, msg, data } 时使用 */
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  async getRaw<T = any>(url: string, params: Record<string, any> = {}): Promise<ApiResponse<T>> {
    const res = await instance.get<ApiResponse<T>>(url, {
      params: filterParams(params),
    })
    return res.data
  },

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  async postRaw<T = any>(url: string, data: any = {}): Promise<ApiResponse<T>> {
    const res = await instance.post<ApiResponse<T>>(url, data)
    return res.data
  },
}

export default http
