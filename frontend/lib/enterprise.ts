import http from "@/lib/http"
import { PaginatedData } from "@/lib/mcp"
import {
  API_ROUTE_ENTERPRISE_ADMIN,
  API_ROUTE_ENTERPRISE_ADMIN_STATUS,
  API_ROUTE_ENTERPRISE_APPLY,
  API_ROUTE_ENTERPRISE_LOGIN,
} from "./routes"

// ============ 企业入驻 ============

/** 审核状态：0 待审核 / 1 已通过 / 2 已拒绝 */
export const ENTERPRISE_STATUS = {
  PENDING: 0,
  APPROVED: 1,
  REJECTED: 2,
} as const

export const ENTERPRISE_STATUS_LABEL: Record<number, string> = {
  0: "待审核",
  1: "已通过",
  2: "已拒绝",
}

export interface EnterpriseApplyParams {
  name: string
  credit_code: string
  legal_person?: string
  contact_name: string
  contact_phone: string
  contact_email?: string
  license_url?: string
  address?: string
  description?: string
  username: string
  password: string
}

/** 提交企业入驻申请 */
export function applyEnterprise(params: EnterpriseApplyParams): Promise<null> {
  return http.post<null>(API_ROUTE_ENTERPRISE_APPLY, params)
}

/** 登录返回：标准用户 JWT + 用户信息（企业账号已关联 sys_user） */
export interface EnterpriseLoginResult {
  access_token: string
  access_token_expire_time: string
  session_uuid: string
  user: {
    id: number
    username: string
    nickname: string
    avatar: string | null
    email: string | null
    is_staff: boolean
    is_superuser: boolean
  }
}

/** 企业账号登录（仅审核通过的企业；非企业用户名走平台用户密码登录） */
export function enterpriseLogin(params: {
  username: string
  password: string
}): Promise<EnterpriseLoginResult> {
  return http.post<EnterpriseLoginResult>(API_ROUTE_ENTERPRISE_LOGIN, params)
}

// ============ 管理端 ============

export interface EnterpriseItem {
  id: number
  name: string
  credit_code: string
  legal_person: string | null
  contact_name: string
  contact_phone: string
  contact_email: string | null
  license_url: string | null
  address: string | null
  description: string | null
  username: string
  status: number
  reject_reason: string | null
  reviewed_time: string | null
  created_time: string
}

export interface EnterpriseSearchParams {
  status?: number
  keyword?: string
  page?: number
  size?: number
}

/** 管理端：企业列表（分页） */
export function getEnterpriseList(
  params: EnterpriseSearchParams = {}
): Promise<PaginatedData<EnterpriseItem>> {
  return http.post<PaginatedData<EnterpriseItem>>(
    `${API_ROUTE_ENTERPRISE_ADMIN}?page=${params.page || 1}&size=${params.size || 10}` +
      (params.status !== undefined ? `&status=${params.status}` : "") +
      (params.keyword ? `&keyword=${encodeURIComponent(params.keyword)}` : ""),
    {}
  )
}

export interface EnterpriseUpdateParams {
  name?: string
  credit_code?: string
  legal_person?: string
  contact_name?: string
  contact_phone?: string
  contact_email?: string
  license_url?: string
  address?: string
  description?: string
  username?: string
  password?: string
}

/** 管理端：修改企业信息 / 重置商家密码 */
export function updateEnterprise(
  id: number,
  params: EnterpriseUpdateParams
): Promise<null> {
  return http.put<null>(`${API_ROUTE_ENTERPRISE_ADMIN}/${id}`, params)
}

/** 管理端：批量审核（status: 1 通过 / 2 拒绝） */
export function reviewEnterprise(
  pks: number[],
  status: 1 | 2,
  reject_reason?: string
): Promise<{ count: number }> {
  return http.put<{ count: number }>(API_ROUTE_ENTERPRISE_ADMIN_STATUS, {
    pks,
    status,
    reject_reason: reject_reason || undefined,
  })
}

/** 管理端：批量删除企业 */
export function deleteEnterprise(pks: number[]): Promise<{ count: number }> {
  return http.deleteBody<{ count: number }>(API_ROUTE_ENTERPRISE_ADMIN, { pks })
}
