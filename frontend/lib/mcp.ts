// 作者：langjunnan
// 开发时间：2025年7月23日

import http from "@/lib/http";
import { API_ROUTE_ADMIN_DEPLOY_LOGS, API_ROUTE_MCP_ADMIN_CATEGORY, API_ROUTE_MCP_ADMIN_CATEGORY_CREATE, API_ROUTE_MCP_ADMIN_SERVER_DETAIL, API_ROUTE_MCP_ADMIN_SERVERS, API_ROUTE_MCP_CATEGORIES, API_ROUTE_MCP_CATEGORIES_RECOMMEND, API_ROUTE_MCP_DEPLOY_PACKAGE, API_ROUTE_MCP_SERVER_DETAIL, API_ROUTE_MCP_SERVER_FEED, API_ROUTE_MCP_SERVER_RECOMMEND, API_ROUTE_MCPS, API_ROUTE_MY_DEPLOY_LOGS, API_ROUTE_MY_MCPS } from "./routes";


// ============ 通用类型 ============

export interface PaginatedData<T> {
  items: T[]
  total: number
  page: number
  size: number
  total_pages: number
  links: {
    first: string
    last: string
    self: string
    next: string | null
    prev: string | null
  }
}

// ============ MCP Category ============

export interface McpCategory {
  id: number
  name: string
}

// ============ MCP Search Server Item ============

export interface McpSearchServerItem {
  id: number
  server_name: string
  description: string
  server_type: string
  avatar: string
  tools: number
  prompts: number
  resources: number
  call_count: number
  owner: string
  needs_auth?: boolean
}

// ============ MCP Server ============

export interface McpServerItem {
  id: number
  server_title: string
  server_name: string
  description: string
  avatar?: string | null
  cover?: string | null
  server_type?: string
  mcp_endpoint?: string
  envs?: Record<string, string>
  server_metadata: {
    meta: any
    protocolVersion: string
    capabilities: {
      experimental: Record<string, any>
      logging: any
      prompts: any
      resources: any
      tools: {
        listChanged: boolean
      }
    }
    serverInfo: {
      name: string
      version: string
    }
    instructions: any
  }
  tools?: Array<{
    name: string
    description: string
    inputSchema: Record<string, any>
  }>
  prompts?: any
  resources?: any
  needs_auth?: boolean
  created_time?: string
  updated_time?: string
  user?: {
    username: string
  }
}

// ============ 广场凭证（MCP 为模板，token 各自配置） ============

export interface McpCredentialStatus {
  needs_auth: boolean
  auth_keys: string[]
  configured: boolean
  enterprise?: {
    id: number
    name: string
    configured: boolean
  } | null
}

export type CredentialScope = "personal" | "enterprise"

/** 查询某 MCP 的凭证配置状态（是否需要 token、需要的 header 键、个人/企业配置情况） */
export function getMcpCredentialStatus(mcpId: number): Promise<McpCredentialStatus> {
  return http.get<McpCredentialStatus>(`${API_ROUTE_MCP_SERVER_DETAIL}/${mcpId}/credential`)
}

/** 保存当前用户对某 MCP 的凭证（整体加密落库；scope=enterprise 时全企业可用） */
export function saveMcpCredential(
  mcpId: number,
  headers: Record<string, string>,
  scope: CredentialScope = "personal"
): Promise<void> {
  return http.put(`${API_ROUTE_MCP_SERVER_DETAIL}/${mcpId}/credential?scope=${scope}`, { headers })
}

/** 清除当前用户对某 MCP 的凭证 */
export function deleteMcpCredential(mcpId: number, scope: CredentialScope = "personal"): Promise<void> {
  return http.delete(`${API_ROUTE_MCP_SERVER_DETAIL}/${mcpId}/credential?scope=${scope}`)
}

/** 当前用户已配置凭证（个人 + 企业共享）的 MCP id 列表，用于过滤需鉴权 MCP */
export function getMcpCredentialConfiguredIds(): Promise<number[]> {
  return http.get<number[]>(`${API_ROUTE_MCPS}credential-server-ids`)
}

export interface McpSearchParams {
  page?: number
  size?: number
  category_id?: number
  keyword?: string
}

export interface McpServerCallResult {
  _meta: any
  content: Array<{
    type: string
    text: string
    annotations?: any
  }>
  isError: boolean
}

// ============ 推荐 ============

export interface McpRecommendServerCapabilities {
  tools?: { listChanged?: boolean }
  logging?: any
  prompts?: { listChanged?: boolean } | null
  resources?: { subscribe?: boolean; listChanged?: boolean } | null
  completions?: any
  experimental?: Record<string, any> | null
}

export interface McpRecommendServer {
  server_title: string
  server_name: string
  description: string
  server_type: "hosted" | "local"
  capabilities: McpRecommendServerCapabilities
  tools: number
  user: {
    username: string
    nickname: string
    avatar: string
  }
}

export interface McpRecommendCategory {
  id: number
  name: string
  servers: McpRecommendServer[]
}
// ============ Admin MCP Server ============

export interface McpAdminServerItem {
  id: number
  server_title: string
  server_name: string
  description: string
  server_type: "hosted" | "local"
  compile_type: "package" | "stdio"
  git?: string
  created_time: string
  updated_time?: string | null
}

export interface McpAdminServersParams {
  page?: number
  size?: number
  keyword?: string
  server_type?: string
  compile_type?: "package" | "stdio"
  is_public?: number
  transport?: "stdio" | "sse" | "streamable"
}

export interface McpAdminServerDetailItem {
  id: number
  server_name: string
  server_title: string
  is_public: number
  is_recommend: number
  description: string
  server_type: "hosted" | "local"
  compile_type: "package" | "stdio"
  git?: string
  user: {
    username: string
    avatar: string
  }
  category: {
    id: number
    name: string
    is_recommend: number
  }
}

export interface McpAdminServerUpdateParams {
  category_id: number
  description: string
  server_title: string
  is_public: number
  is_recommend: number
}

// ============ Admin Category ============

export interface McpAdminCategoryItem {
  id: number
  name: string
  is_recommend: number
  created_time: string
  updated_time?: string | null
}

export interface McpAdminCategoryParams {
  is_recommend?: number
}

export interface McpAdminCategoryCreateParams {
  name: string
  is_recommend: number
}

/** 获取 MCP 分类列表 */
export function getMcpCategories(): Promise<McpCategory[]> {
  return http.get<McpCategory[]>(API_ROUTE_MCP_CATEGORIES)
}

/** 搜索 MCP 服务器 */
export function searchMcpServers(
  params: McpSearchParams = {}
): Promise<PaginatedData<McpSearchServerItem>> {
  return http.get<PaginatedData<McpSearchServerItem>>(API_ROUTE_MCPS, {
    page: params.page || 1,
    size: params.size || 10,
    category_id: params.category_id || undefined,
    keyword: params.keyword || undefined,
  })
}

/** 获取 MCP 服务器 feed */
export function getMcpServerFeed(): Promise<McpServerItem[]> {
  return http.get<McpServerItem[]>(API_ROUTE_MCP_SERVER_FEED)
}

/** 获取 MCP 服务器详情 */
export function getMcpServerDetail(
  username: string,
  serverName: string
): Promise<McpServerItem> {
  return http.get<McpServerItem>(
    `${API_ROUTE_MCP_SERVER_DETAIL}/${username}/${serverName}`
  )
}

/** 调用 MCP 服务器工具 */
export function callMcpServerTool(
  username: string,
  serverName: string,
  toolName: string,
  args: Record<string, any>
): Promise<McpServerCallResult> {
  return http.post<McpServerCallResult>(
    `${API_ROUTE_MCPS}invoke`,
    {
      username,
      server_name: serverName,
      tool_name: toolName,
      arguments: args,
    }
  )
}

/** 获取推荐 MCP 服务器（分类） */
export function getMcpServerRecommend(): Promise<McpRecommendCategory[]> {
  return http.get<McpRecommendCategory[]>(API_ROUTE_MCP_CATEGORIES_RECOMMEND)
}

// ============ 推荐列表（扁平） ============

export interface McpRecommendItem {
  server_name: string
  description: string
  server_type: "hosted" | "local"
  owner: string
  cover?: string | null
  needs_auth?: boolean
  call_count: number
}

/** 获取推荐 MCP 服务器（扁平列表） */
export function getMcpRecommendList(): Promise<McpRecommendItem[]> {
  return http.get<McpRecommendItem[]>(API_ROUTE_MCP_SERVER_RECOMMEND)
}

/** 管理端 - 获取 MCP 服务器列表 */
export function getMcpAdminServers(
  params: McpAdminServersParams = {}
): Promise<PaginatedData<McpAdminServerItem>> {
  return http.post<PaginatedData<McpAdminServerItem>>(
    API_ROUTE_MCP_ADMIN_SERVERS,
    {
      page: params.page || 1,
      size: params.size || 20,
      ...params,
    }
  )
}

/** 管理端 - 获取 MCP 服务器详情 */
export function getMcpAdminServerDetail(
  serverId: string | number
): Promise<McpAdminServerDetailItem> {
  return http.get<McpAdminServerDetailItem>(
    `${API_ROUTE_MCP_ADMIN_SERVER_DETAIL}/${serverId}`
  )
}

/** 管理端 - 更新 MCP 服务器 */
export function updateMcpAdminServer(
  serverId: string | number,
  params: McpAdminServerUpdateParams
): Promise<null> {
  return http.put<null>(
    `${API_ROUTE_MCP_ADMIN_SERVER_DETAIL}/${serverId}`,
    params
  )
}

/** 管理端 - 获取分类列表 */
export function getMcpAdminCategories(
  params: McpAdminCategoryParams = {}
): Promise<PaginatedData<McpAdminCategoryItem>> {
  return http.post<PaginatedData<McpAdminCategoryItem>>(
    API_ROUTE_MCP_ADMIN_CATEGORY,
    {
      is_recommend: params.is_recommend ?? -1,
      ...params,
    }
  )
}

/** 管理端 - 创建分类 */
export function createMcpAdminCategory(
  params: McpAdminCategoryCreateParams
): Promise<null> {
  return http.post<null>(API_ROUTE_MCP_ADMIN_CATEGORY_CREATE, params)
}

/** 修改 MCP 头像（仅创建者；置空恢复默认机器人头像） */
export function updateMcpAvatar(mcpId: number, avatar: string | null): Promise<null> {
  return http.put<null>(`${API_ROUTE_MCP_SERVER_DETAIL}/${mcpId}/avatar`, { avatar })
}

/** 修改 MCP 封面（仅创建者；置空清除封面，首页样式用） */
export function updateMcpCover(mcpId: number, cover: string | null): Promise<null> {
  return http.put<null>(`${API_ROUTE_MCP_SERVER_DETAIL}/${mcpId}/cover`, { cover })
}

// ============ MCP 提交 ============

export interface McpSubmitData {
  server_title: string
  description?: string
  mcpServers: any
}

/** 提交 MCP 服务器配置 */
export function submitMcpServer(data: McpSubmitData): Promise<any> {
  return http.post(API_ROUTE_MCP_DEPLOY_PACKAGE, data)
}

// ============ My MCPs ============

export interface MyMcpItem {
  id: number
  server_title: string
  server_name: string
  description: string | null
  server_type: string
  is_public: boolean | null
  needs_auth?: boolean
  user: {
    username: string
    avatar: string | null
  }
  created_time: string
  updated_time: string | null
}

/** 获取我的 MCP 列表 */
export function getMyMcps(
  params: { page?: number; size?: number } = {}
): Promise<PaginatedData<MyMcpItem>> {
  return http.get<PaginatedData<MyMcpItem>>(API_ROUTE_MY_MCPS, {
    page: params.page ?? 1,
    size: params.size ?? 20,
  })
}

// ============ Deploy Logs ============

export type DeployLogStatus = 'PENDING' | 'STARTED' | 'SUCCESS' | 'FAILURE' | 'RETRY' | 'REVOKED'

export interface DeployLogItem {
  id: number
  task_id: string
  task_status: DeployLogStatus
  task_result: string | null
  traceback: string | null
  server_title: string | null
  created_time: string
  updated_time: string | null
}

/** 获取我的部署记录 */
export function getMyDeployLogs(
  params: { page?: number; size?: number } = {}
): Promise<PaginatedData<DeployLogItem>> {
  return http.get<PaginatedData<DeployLogItem>>(API_ROUTE_MY_DEPLOY_LOGS, {
    page: params.page ?? 1,
    size: params.size ?? 20,
  })
}

// ============ Admin Deploy Logs ============

export interface AdminDeployLogItem extends DeployLogItem {
  username: string | null
}

export interface AdminDeployLogSearchParams {
  page?: number
  size?: number
  username?: string
  server_title?: string
  task_status?: string
}

/** 管理端 - 查询所有部署日志 */
export function getAdminDeployLogs(
  params: AdminDeployLogSearchParams = {}
): Promise<PaginatedData<AdminDeployLogItem>> {
  const { page = 1, size = 20, ...filters } = params
  return http.post<PaginatedData<AdminDeployLogItem>>(API_ROUTE_ADMIN_DEPLOY_LOGS, {
    page,
    size,
    ...filters,
  })
}
