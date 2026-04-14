/**
 * time.ts 工具函数单元测试
 */
import { describe, it, expect } from 'vitest'
import { formatLocalTime } from '../src/utils/time'

describe('formatLocalTime', () => {
  it('空字符串返回空字符串', () => {
    expect(formatLocalTime('')).toBe('')
  })

  it('无效字符串返回原始字符串', () => {
    expect(formatLocalTime('invalid-date')).toBe('invalid-date')
  })

  it('格式符合 YYYY-MM-DD HH:mm:ss', () => {
    const result = formatLocalTime('2026-04-01T00:00:00Z')
    expect(result).toMatch(/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/)
  })

  it('返回字符串长度为 19', () => {
    const result = formatLocalTime('2026-04-01T00:00:00Z')
    expect(result.length).toBe(19)
  })

  it('不含 T 分隔符和 Z 后缀', () => {
    const result = formatLocalTime('2026-04-01T00:00:00Z')
    expect(result).not.toContain('T')
    expect(result).not.toContain('Z')
  })
})
