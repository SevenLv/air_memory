/** 记忆条目 */
export interface Memory {
  id: string
  content: string
  similarity: number
  value_score: number
  tier: string
  created_at: string
}

/** 记忆查询响应 */
export interface MemoryQueryResponse {
  memories: Memory[]
  count: number
  query_mode: string
}

/** 存储操作日志条目 */
export interface SaveLog {
  id: number
  memory_id: string
  content: string
  created_at: string
  memory_deleted: boolean
  value_score?: number | null
  is_garbled: boolean  // 新增：服务端计算的乱码检测结果（v1.2.5+）
}

/** 存储操作日志响应 */
export interface SaveLogsResponse {
  logs: SaveLog[]
  count: number
}

/** 查询操作日志条目 */
export interface QueryLog {
  id: number
  query: string
  results: string
  fast_only: boolean
  created_at: string
}

/** 查询操作日志响应 */
export interface QueryLogsResponse {
  logs: QueryLog[]
  count: number
}

/** 反馈日志条目 */
export interface FeedbackLog {
  id: number
  memory_id: string
  valuable: boolean
  created_at: string
}

/** 反馈日志响应 */
export interface FeedbackLogsResponse {
  logs: FeedbackLog[]
  count: number
}

/** 记忆价值评分 */
export interface MemoryValueScore {
  memory_id: string
  value_score: number
  tier: string
  feedback_count: number
}

/** 热/冷层分级存储统计 */
export interface TierStats {
  hot_count: number
  cold_count: number
  hot_memory_mb: number
  memory_budget_mb: number
}

/** 磁盘占用统计 */
export interface DiskStats {
  disk_used_gb: number
  disk_budget_gb: number
  disk_trigger_gb: number
  disk_safe_gb: number
}

/** 系统版本信息 */
export interface AppVersion {
  version: string
}

/** 反馈日志列表响应（含总条数，用于分页） */
export interface FeedbackLogsWithTotalResponse {
  logs: FeedbackLog[]
  count: number
  total: number
}

/** 输入信息条目 */
export interface InputInfo {
  input_id: string
  query: string
  created_at: string
}

/** 输入信息管理列表响应 */
export interface InputsListResponse {
  inputs: InputInfo[]
  count: number
  total: number
}

/** 输入信息关联记忆条目 */
export interface InputMemoryLink {
  memory_id: string
  association_score: number
  total_association_score: number
}

/** 输入信息详情 */
export interface InputDetail {
  input_id: string
  query: string
  created_at: string
  memories: InputMemoryLink[]
}
