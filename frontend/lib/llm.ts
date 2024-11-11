// 作者：langjunnan
// 开发时间：2025年7月23日

import http from "@/lib/http"
import { API_ROUTE_LLM_CREDENTIAL } from "./routes"

// ============ 用户/商户自己的模型密钥（BYOK，OpenAI 兼容网关） ============

export interface LlmCredentialDetail {
  configured: boolean
  baseUrl: string | null
  chatModel: string | null
  titleModel: string | null
  apiKeyMasked: string | null
}

export interface LlmEnterpriseCredentialDetail extends LlmCredentialDetail {
  id: number
  name: string
}

export interface LlmCredentialStatus {
  personal: LlmCredentialDetail
  enterprise: LlmEnterpriseCredentialDetail | null
  defaults: {
    baseUrl: string
    chatModel: string
    titleModel: string
  }
}

export interface LlmCredentialParams {
  api_key: string
  base_url?: string
  chat_model?: string
  title_model?: string
}

export type LlmCredentialScope = "personal" | "enterprise"

export interface LlmCredentialTestResult {
  ok: boolean
  model?: string
  error?: string
}

/** 查询我的模型密钥配置（密钥仅掩码回显） */
export function getLlmCredential(): Promise<LlmCredentialStatus> {
  return http.get<LlmCredentialStatus>(API_ROUTE_LLM_CREDENTIAL)
}

/** 保存模型密钥（scope=personal 个人 / enterprise 企业共享） */
export function saveLlmCredential(
  params: LlmCredentialParams,
  scope: LlmCredentialScope = "personal"
): Promise<null> {
  return http.put<null>(`${API_ROUTE_LLM_CREDENTIAL}?scope=${scope}`, params)
}

/** 清除模型密钥 */
export function deleteLlmCredential(scope: LlmCredentialScope = "personal"): Promise<null> {
  return http.delete<null>(API_ROUTE_LLM_CREDENTIAL, {
    params: { scope },
  })
}

/** 测试网关连通性（用表单值直接试连，不落库） */
export function testLlmCredential(params: LlmCredentialParams): Promise<LlmCredentialTestResult> {
  return http.post<LlmCredentialTestResult>(`${API_ROUTE_LLM_CREDENTIAL}/test`, params)
}

/** 个人与企业共享是否都没有可用密钥（聊天拦截判断用） */
export function isLlmUnconfigured(status: LlmCredentialStatus): boolean {
  const personalOk = !!status.personal?.configured
  const enterpriseOk = !!status.enterprise?.configured
  return !personalOk && !enterpriseOk
}
