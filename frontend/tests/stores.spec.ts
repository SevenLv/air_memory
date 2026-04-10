/**
 * Pinia Stores 单元测试 - useMemoryStore 和 useLogStore
 *
 * 覆盖：状态初始值、fetchMemories、removeMemory、fetchSaveLogs、fetchQueryLogs
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

// ---------------------------------------------------------------------------
// Mock API - 内联数据，避免 vi.mock hoisting 问题
// ---------------------------------------------------------------------------

vi.mock('../src/api', () => ({
  queryMemories: vi.fn().mockResolvedValue({
    memories: [
      { id: 'mem-001', content: '记忆内容一', similarity: 0.9, value_score: 0.5, tier: 'cold', created_at: '2026-04-01T10:00:00Z' },
      { id: 'mem-002', content: '记忆内容二', similarity: 0.8, value_score: 0.7, tier: 'hot', created_at: '2026-04-02T10:00:00Z' },
    ],
    count: 2,
    query_mode: 'deep',
  }),
  deleteMemory: vi.fn().mockResolvedValue(undefined),
  getSaveLogs: vi.fn().mockResolvedValue({
    logs: [
      { id: 1, memory_id: 'mem-001', content: '存储内容', created_at: '2026-04-01T10:00:00Z', memory_deleted: false },
    ],
    count: 1,
  }),
  getQueryLogs: vi.fn().mockResolvedValue({
    logs: [
      { id: 1, query: '查询文本', results: '[]', fast_only: false, created_at: '2026-04-01T10:00:00Z' },
    ],
    count: 1,
  }),
}))

// ---------------------------------------------------------------------------
// useMemoryStore 测试
// ---------------------------------------------------------------------------

describe('useMemoryStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('初始状态：memories 为空数组', async () => {
    const { useMemoryStore } = await import('../src/stores/memory')
    const store = useMemoryStore()
    expect(store.memories).toEqual([])
  })

  it('初始状态：loading 为 false', async () => {
    const { useMemoryStore } = await import('../src/stores/memory')
    const store = useMemoryStore()
    expect(store.loading).toBe(false)
  })

  it('初始状态：count 为 0', async () => {
    const { useMemoryStore } = await import('../src/stores/memory')
    const store = useMemoryStore()
    expect(store.count).toBe(0)
  })

  it('fetchMemories 成功后更新 memories 列表', async () => {
    const { useMemoryStore } = await import('../src/stores/memory')
    const store = useMemoryStore()
    await store.fetchMemories('测试查询', 5, false)
    expect(store.memories).toHaveLength(2)
    expect(store.memories[0].id).toBe('mem-001')
  })

  it('fetchMemories 成功后更新 count', async () => {
    const { useMemoryStore } = await import('../src/stores/memory')
    const store = useMemoryStore()
    await store.fetchMemories('测试查询')
    expect(store.count).toBe(2)
  })

  it('fetchMemories 成功后更新 queryMode', async () => {
    const { useMemoryStore } = await import('../src/stores/memory')
    const store = useMemoryStore()
    await store.fetchMemories('测试查询')
    expect(store.queryMode).toBe('deep')
  })

  it('fetchMemories 期间 loading 为 true，完成后为 false', async () => {
    const { useMemoryStore } = await import('../src/stores/memory')
    const store = useMemoryStore()
    const promise = store.fetchMemories('查询')
    expect(store.loading).toBe(true)
    await promise
    expect(store.loading).toBe(false)
  })

  it('removeMemory 调用 deleteMemory API', async () => {
    const { deleteMemory } = await import('../src/api')
    const { useMemoryStore } = await import('../src/stores/memory')
    const store = useMemoryStore()
    await store.fetchMemories('查询')
    await store.removeMemory('mem-001')
    expect(deleteMemory).toHaveBeenCalledWith('mem-001')
  })

  it('removeMemory 从 memories 列表中移除对应项', async () => {
    const { useMemoryStore } = await import('../src/stores/memory')
    const store = useMemoryStore()
    await store.fetchMemories('查询')
    expect(store.memories).toHaveLength(2)
    await store.removeMemory('mem-001')
    expect(store.memories).toHaveLength(1)
    expect(store.memories[0].id).toBe('mem-002')
  })

  it('removeMemory 后 count 更新为剩余数量', async () => {
    const { useMemoryStore } = await import('../src/stores/memory')
    const store = useMemoryStore()
    await store.fetchMemories('查询')
    await store.removeMemory('mem-001')
    expect(store.count).toBe(1)
  })

  it('fetchMemories API 抛出异常时 loading 仍恢复为 false', async () => {
    const { queryMemories } = await import('../src/api')
    ;(queryMemories as ReturnType<typeof vi.fn>).mockRejectedValueOnce(new Error('网络错误'))

    const { useMemoryStore } = await import('../src/stores/memory')
    const store = useMemoryStore()
    try {
      await store.fetchMemories('查询')
    } catch {
      // 忽略错误
    }
    expect(store.loading).toBe(false)
  })
})

// ---------------------------------------------------------------------------
// useLogStore 测试
// ---------------------------------------------------------------------------

describe('useLogStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('初始状态：saveLogs 为空数组', async () => {
    const { useLogStore } = await import('../src/stores/log')
    const store = useLogStore()
    expect(store.saveLogs).toEqual([])
  })

  it('初始状态：queryLogs 为空数组', async () => {
    const { useLogStore } = await import('../src/stores/log')
    const store = useLogStore()
    expect(store.queryLogs).toEqual([])
  })

  it('初始状态：saveLoading 为 false', async () => {
    const { useLogStore } = await import('../src/stores/log')
    const store = useLogStore()
    expect(store.saveLoading).toBe(false)
  })

  it('初始状态：queryLoading 为 false', async () => {
    const { useLogStore } = await import('../src/stores/log')
    const store = useLogStore()
    expect(store.queryLoading).toBe(false)
  })

  it('fetchSaveLogs 成功后更新 saveLogs', async () => {
    const { useLogStore } = await import('../src/stores/log')
    const store = useLogStore()
    await store.fetchSaveLogs()
    expect(store.saveLogs).toHaveLength(1)
    expect(store.saveLogs[0].memory_id).toBe('mem-001')
  })

  it('fetchSaveLogs 期间 saveLoading 为 true，完成后为 false', async () => {
    const { useLogStore } = await import('../src/stores/log')
    const store = useLogStore()
    const promise = store.fetchSaveLogs()
    expect(store.saveLoading).toBe(true)
    await promise
    expect(store.saveLoading).toBe(false)
  })

  it('fetchQueryLogs 成功后更新 queryLogs', async () => {
    const { useLogStore } = await import('../src/stores/log')
    const store = useLogStore()
    await store.fetchQueryLogs()
    expect(store.queryLogs).toHaveLength(1)
    expect(store.queryLogs[0].query).toBe('查询文本')
  })

  it('fetchQueryLogs 期间 queryLoading 为 true，完成后为 false', async () => {
    const { useLogStore } = await import('../src/stores/log')
    const store = useLogStore()
    const promise = store.fetchQueryLogs()
    expect(store.queryLoading).toBe(true)
    await promise
    expect(store.queryLoading).toBe(false)
  })

  it('fetchSaveLogs API 异常时 saveLoading 恢复为 false', async () => {
    const { getSaveLogs } = await import('../src/api')
    ;(getSaveLogs as ReturnType<typeof vi.fn>).mockRejectedValueOnce(new Error('网络错误'))

    const { useLogStore } = await import('../src/stores/log')
    const store = useLogStore()
    try {
      await store.fetchSaveLogs()
    } catch {
      // 忽略
    }
    expect(store.saveLoading).toBe(false)
  })

  it('fetchQueryLogs API 异常时 queryLoading 恢复为 false', async () => {
    const { getQueryLogs } = await import('../src/api')
    ;(getQueryLogs as ReturnType<typeof vi.fn>).mockRejectedValueOnce(new Error('网络错误'))

    const { useLogStore } = await import('../src/stores/log')
    const store = useLogStore()
    try {
      await store.fetchQueryLogs()
    } catch {
      // 忽略
    }
    expect(store.queryLoading).toBe(false)
  })
})
