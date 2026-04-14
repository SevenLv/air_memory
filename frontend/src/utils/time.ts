/**
 * 时间工具函数
 */

/**
 * 将 ISO 8601 时间字符串转换为用户本地时间，格式为 YYYY-MM-DD HH:mm:ss。
 * @param dateStr - 后端返回的时间字符串（ISO 8601 格式，如 "2026-04-01T10:00:00Z"）
 * @returns 格式化后的本地时间字符串，输入无效时返回原始字符串
 */
export function formatLocalTime(dateStr: string): string {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  if (isNaN(date.getTime())) return dateStr
  const pad = (n: number): string => String(n).padStart(2, '0')
  const year = date.getFullYear()
  const month = pad(date.getMonth() + 1)
  const day = pad(date.getDate())
  const hours = pad(date.getHours())
  const minutes = pad(date.getMinutes())
  const seconds = pad(date.getSeconds())
  return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`
}
