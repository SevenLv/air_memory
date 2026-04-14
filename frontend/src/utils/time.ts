/**
 * 将 ISO 8601 UTC 时间字符串转换为用户本地时间显示
 * 兼容带时区信息的格式（+00:00）和无时区的格式
 */
export function formatLocalTime(isoString: string): string {
  if (!isoString) return '-'
  try {
    const date = new Date(isoString)
    if (isNaN(date.getTime())) return isoString
    return date.toLocaleString(undefined, {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false,
    })
  } catch {
    return isoString
  }
}
