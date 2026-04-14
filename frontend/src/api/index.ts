import axios, { type AxiosError } from 'axios'
import { ElMessage } from 'element-plus'
import type {
  MemoryQueryResponse,
  SaveLogsResponse,
  QueryLogsResponse,
  FeedbackLogsResponse,
  MemoryValueScore,
  TierStats,
  DiskStats,
  AppVersion,
} from './types'

/** 统一 Axios 实例 */
const apiClient = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
})

// 响应拦截器：统一处理 4xx/5xx 错误
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    const status = error.response?.status
    const data = error.response?.data as { detail?: string } | undefined
    const detail = data?.detail ?? '网络请求失败'
    if (status && status >= 400) {
      ElMessage.error(`请求错误 ${status}: ${detail}`)
    } else {
      ElMessage.error(`网络错误: ${detail}`)
    }
    return Promise.reject(error)
  },
)

export default apiClient

/** 查询记忆 */
export async function queryMemories(
  query: string,
  topK: number = 5,
  fastOnly: boolean = false,
): Promise<MemoryQueryResponse> {
  const res = await apiClient.get<MemoryQueryResponse>('/memories', {
    params: { query, top_k: topK, fast_only: fastOnly },
  })
  return res.data
}

/** 删除记忆 */
export async function deleteMemory(memoryId: string): Promise<void> {
  await apiClient.delete(`/memories/${memoryId}`)
}

/** 获取存储操作日志 */
export async function getSaveLogs(): Promise<SaveLogsResponse> {
  const res = await apiClient.get<SaveLogsResponse>('/logs/save')
  return res.data
}

/** 获取查询操作日志 */
export async function getQueryLogs(): Promise<QueryLogsResponse> {
  const res = await apiClient.get<QueryLogsResponse>('/logs/query')
  return res.data
}

/** 获取指定记忆的反馈日志 */
export async function getFeedbackLogs(
  memoryId: string,
  page: number = 1,
  pageSize: number = 20,
): Promise<FeedbackLogsResponse> {
  const res = await apiClient.get<FeedbackLogsResponse>(
    `/memories/${memoryId}/feedback/logs`,
    { params: { page, page_size: pageSize } },
  )
  return res.data
}

/** 获取指定记忆的价值评分 */
export async function getValueScore(memoryId: string): Promise<MemoryValueScore> {
  const res = await apiClient.get<MemoryValueScore>(`/memories/${memoryId}/value-score`)
  return res.data
}

/** 获取分级存储统计 */
export async function getTierStats(): Promise<TierStats> {
  const res = await apiClient.get<TierStats>('/admin/tier-stats')
  return res.data
}

/** 获取磁盘占用统计 */
export async function getDiskStats(): Promise<DiskStats> {
  const res = await apiClient.get<DiskStats>('/admin/disk-stats')
  return res.data
}

/** 获取系统版本号 */
export async function getVersion(): Promise<AppVersion> {
  const res = await apiClient.get<AppVersion>('/version')
  return res.data
}
