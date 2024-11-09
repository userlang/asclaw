// 作者：langjunnan
// 开发时间：2025年7月23日

import http from "@/lib/http"
import { API_ROUTE_AUTH_ME, API_ROUTE_OAUTH_USER } from "./routes"

// ============ 用户 ============

export interface UserItem {
  nickname: string
  avatar: string
}

export interface AuthMeData {
  id: string
  nickname: string
  avatar: string
  email?: string
  [key: string]: any
}

/** 获取当前 OAuth 用户 */
export function getCurrentUser(): Promise<UserItem> {
  return http.get<UserItem>(API_ROUTE_OAUTH_USER)
}

/** 获取当前登录用户信息 */
export function getAuthMe(): Promise<AuthMeData> {
  return http.get<AuthMeData>(API_ROUTE_AUTH_ME)
}
