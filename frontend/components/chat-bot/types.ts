// 作者：langjunnan
// 开发时间：2025年7月23日

export type SearchType = "mcp" | "skill" | "agent"

export type SelectedContext = {
  type: SearchType
  owner: string
  name: string
  label: string
}

export type SearchResult = {
  owner: string
  name: string
  label: string
  description: string
  avatar: string
  id?: number
  needs_auth?: boolean
}
