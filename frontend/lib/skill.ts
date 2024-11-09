// 作者：langjunnan
// 开发时间：2025年7月23日

import http from "@/lib/http"
import { PaginatedData } from "@/lib/mcp"
import {
  API_ROUTE_MY_SKILLS,
  API_ROUTE_SKILLS,
  API_ROUTE_SKILL_ADMIN_CATEGORY,
  API_ROUTE_SKILL_ADMIN_CATEGORY_CREATE,
  API_ROUTE_SKILL_ADMIN_SERVER_DETAIL,
  API_ROUTE_SKILL_ADMIN_SERVERS,
  API_ROUTE_SKILL_CATEGORIES,
  API_ROUTE_SKILL_DELETE,
  API_ROUTE_SKILL_FILES,
  API_ROUTE_SKILL_INSTALL,
  API_ROUTE_SKILL_PUBLISH,
} from "./routes"

// ============ Skill Category ============

export interface SkillCategory {
  id: number
  name: string
}

// ============ Skill Search Item ============

export interface SkillSearchItem {
  name: string
  description: string
  path: string
  owner: string
  avatar: string
  favorite_count: number
}

// ============ Skill Detail ============

export interface SkillDetail {
  name: string
  title: string
  description: string | null
  body: string | null
  path: string | null
  repository: string | null
  source_url: string | null
  install_count: number
  owner: string
  avatar: string
  category: string | null
  favorite_count: number
}

/** 获取 Skill 详情（公开） */
export function getSkillDetail(owner: string, skillName: string): Promise<SkillDetail> {
  return http.get<SkillDetail>(`/api/v1/skill/${encodeURIComponent(owner)}/${encodeURIComponent(skillName)}`)
}

export interface SkillSearchParams {
  page?: number
  size?: number
  category_id?: number
  keyword?: string
}

/** 获取 Skill 分类列表 */
export function getSkillCategories(): Promise<SkillCategory[]> {
  return http.get<SkillCategory[]>(API_ROUTE_SKILL_CATEGORIES)
}

/** 搜索 Skill */
export function searchSkills(
  params: SkillSearchParams = {}
): Promise<PaginatedData<SkillSearchItem>> {
  return http.get<PaginatedData<SkillSearchItem>>(API_ROUTE_SKILLS, {
    page: params.page || 1,
    size: params.size || 20,
    category_id: params.category_id || undefined,
    keyword: params.keyword || undefined,
  })
}

// ============ Skill Publish ============

export interface SkillPublishParams {
  name: string
  title: string
  description: string
  category_id?: number
  source_url?: string
  body?: string
}

/** 发布（导入）Skill */
export function publishSkill(params: SkillPublishParams): Promise<SkillDetail> {
  return http.post<SkillDetail>(API_ROUTE_SKILL_PUBLISH, params)
}

/** 删除我的 Skill */
export function deleteMySkill(skillId: number): Promise<null> {
  return http.delete<null>(`${API_ROUTE_SKILL_DELETE}/${skillId}`)
}

/** Skill 附加文件 */
export interface SkillFile {
  file_path: string
  content: string | null
}

/** 获取 Skill 附加文件列表 */
export function getSkillFiles(skillId: number): Promise<SkillFile[]> {
  return http.get<SkillFile[]>(`${API_ROUTE_SKILL_FILES}/${skillId}/files`)
}

/** 在线体验计数（进入 chat 时调用） */
export function trackSkillInstall(skillId: number): Promise<null> {
  return http.post<null>(`${API_ROUTE_SKILL_INSTALL}/${skillId}/install`)
}

// ============ Admin Skill ============

export interface SkillAdminItem {
  id: number
  name: string
  title: string
  avatar: string | null
  description: string | null
  repository: string | null
  owner: string
  is_public: boolean | null
  created_time: string
  updated_time: string | null
}

export interface SkillAdminSearchParams {
  page?: number
  size?: number
  keyword?: string
  category_id?: number
}

export interface SkillAdminCategoryItem {
  id: number
  name: string
  is_recommend: number
  created_time: string
  updated_time: string | null
}

export interface SkillAdminCategoryParams {
  is_recommend?: number
}

export interface SkillAdminCategoryCreateParams {
  name: string
  is_recommend: number
}

/** 管理端 - 获取 Skill 列表 */
export function getSkillAdminServers(
  params: SkillAdminSearchParams = {}
): Promise<PaginatedData<SkillAdminItem>> {
  return http.post<PaginatedData<SkillAdminItem>>(API_ROUTE_SKILL_ADMIN_SERVERS, {
    page: params.page || 1,
    size: params.size || 20,
    keyword: params.keyword || "",
    category_id: params.category_id ?? 0,
  })
}

/** 管理端 - 删除 Skill */
export function deleteSkillAdmin(skillId: string | number): Promise<null> {
  return http.delete<null>(`${API_ROUTE_SKILL_ADMIN_SERVER_DETAIL}/${skillId}`)
}

/** 管理端 - 获取 Skill 分类列表 */
export function getSkillAdminCategories(
  params: SkillAdminCategoryParams = {}
): Promise<PaginatedData<SkillAdminCategoryItem>> {
  return http.post<PaginatedData<SkillAdminCategoryItem>>(API_ROUTE_SKILL_ADMIN_CATEGORY, {
    is_recommend: params.is_recommend ?? -1,
  })
}

/** 管理端 - 创建 Skill 分类 */
export function createSkillAdminCategory(
  params: SkillAdminCategoryCreateParams
): Promise<null> {
  return http.post<null>(API_ROUTE_SKILL_ADMIN_CATEGORY_CREATE, params)
}

// ============ My Skills ============

export interface MySkillItem {
  id: number
  name: string
  title: string
  avatar: string | null
  description: string | null
  repository: string | null
  owner: string
  is_public: boolean | null
  created_time: string
  updated_time: string | null
}

/** 获取我的 Skill 列表 */
export function getMySkills(
  params: { page?: number; size?: number } = {}
): Promise<PaginatedData<MySkillItem>> {
  return http.get<PaginatedData<MySkillItem>>(API_ROUTE_MY_SKILLS, {
    page: params.page ?? 1,
    size: params.size ?? 20,
  })
}
