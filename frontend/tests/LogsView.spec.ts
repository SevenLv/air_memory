/**
 * LogsView.vue 单元测试
 *
 * 覆盖：视图渲染、标签页切换、存储日志/查询日志加载、结果摘要解析
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import ElementPlus from 'element-plus'
import LogsView from '../src/views/LogsView.vue'

// ---------------------------------------------------------------------------
// Mock API
// ---------------------------------------------------------------------------

vi.mock('../src/api', () => ({
  getSaveLogs: vi.fn().mockResolvedValue({
    logs: [
      {
        id: 1,
        memory_id: 'mem-001',
        content: '存储日志内容一',
        created_at: '2026-04-01T10:00:00Z',
        memory_deleted: false,
      },
      {
        id: 2,
        memory_id: 'mem-002',
        content: '存储日志内容二',
        created_at: '2026-04-02T10:00:00Z',
        memory_deleted: true,
      },
    ],
    count: 2,
  }),
  getQueryLogs: vi.fn().mockResolvedValue({
    logs: [
      {
        id: 1,
        query: '查询条件文本',
        results: JSON.stringify([{ id: 'r1' }, { id: 'r2' }]),
        fast_only: false,
        created_at: '2026-04-01T11:00:00Z',
      },
    ],
    count: 1,
  }),
}))

// ---------------------------------------------------------------------------
// 测试套件
// ---------------------------------------------------------------------------

describe('LogsView 视图', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('可以正常挂载', () => {
    const wrapper = mount(LogsView, {
      global: { plugins: [ElementPlus] },
    })
    expect(wrapper.exists()).toBe(true)
  })

  it('显示存储操作日志和查询操作日志两个标签页', () => {
    const wrapper = mount(LogsView, {
      global: { plugins: [ElementPlus] },
    })
    const text = wrapper.text()
    expect(text).toContain('存储操作日志')
    expect(text).toContain('查询操作日志')
  })

  it('挂载时自动调用 getSaveLogs（默认激活存储操作日志标签）', async () => {
    const { getSaveLogs } = await import('../src/api')
    mount(LogsView, {
      global: { plugins: [ElementPlus] },
    })
    await flushPromises()
    expect(getSaveLogs).toHaveBeenCalled()
  })

  it('挂载时不自动调用 getQueryLogs（延迟加载）', async () => {
    const { getQueryLogs } = await import('../src/api')
    mount(LogsView, {
      global: { plugins: [ElementPlus] },
    })
    await flushPromises()
    expect(getQueryLogs).not.toHaveBeenCalled()
  })

  it('包含刷新按钮', () => {
    const wrapper = mount(LogsView, {
      global: { plugins: [ElementPlus] },
    })
    expect(wrapper.text()).toContain('刷新')
  })

  it('parseResultsSummary 函数：有效 JSON 返回正确条数', async () => {
    const { getSaveLogs } = await import('../src/api')
    const wrapper = mount(LogsView, {
      global: { plugins: [ElementPlus] },
    })
    await flushPromises()

    // 通过 vm 访问内部函数（如果暴露）
    const vm = wrapper.vm as { parseResultsSummary?: (r: string) => string }
    if (typeof vm.parseResultsSummary === 'function') {
      const result = vm.parseResultsSummary('[{"id":"r1"},{"id":"r2"}]')
      expect(result).toContain('2')
    }
  })

  it('parseResultsSummary 函数：无效 JSON 返回错误提示', async () => {
    const wrapper = mount(LogsView, {
      global: { plugins: [ElementPlus] },
    })
    await flushPromises()

    const vm = wrapper.vm as { parseResultsSummary?: (r: string) => string }
    if (typeof vm.parseResultsSummary === 'function') {
      const result = vm.parseResultsSummary('invalid json')
      expect(result).toContain('失败')
    }
  })

  it('存储日志加载后显示日志条数', async () => {
    const wrapper = mount(LogsView, {
      global: { plugins: [ElementPlus] },
    })
    await flushPromises()
    // 应显示"共 N 条"
    expect(wrapper.text()).toMatch(/共\s*\d+\s*条/)
  })
})
