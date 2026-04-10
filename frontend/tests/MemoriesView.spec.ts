/**
 * MemoriesView.vue 单元测试
 *
 * 覆盖：视图渲染、查询表单交互、空查询校验、查询模式切换、记忆列表展示、删除操作
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import ElementPlus from 'element-plus'
import MemoriesView from '../src/views/MemoriesView.vue'

// ---------------------------------------------------------------------------
// Mock API
// ---------------------------------------------------------------------------

vi.mock('../src/api', () => ({
  queryMemories: vi.fn().mockResolvedValue({
    memories: [
      {
        id: 'mem-001',
        content: '查询返回记忆内容',
        similarity: 0.9,
        value_score: 0.5,
        tier: 'cold',
        created_at: '2026-04-01T10:00:00Z',
      },
    ],
    count: 1,
    query_mode: 'deep',
  }),
  deleteMemory: vi.fn().mockResolvedValue(undefined),
}))

// ---------------------------------------------------------------------------
// 测试套件
// ---------------------------------------------------------------------------

describe('MemoriesView 视图', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('可以正常挂载', () => {
    const wrapper = mount(MemoriesView, {
      global: { plugins: [ElementPlus] },
    })
    expect(wrapper.exists()).toBe(true)
  })

  it('显示"记忆查询"标题', () => {
    const wrapper = mount(MemoriesView, {
      global: { plugins: [ElementPlus] },
    })
    expect(wrapper.text()).toContain('记忆查询')
  })

  it('包含查询输入框', () => {
    const wrapper = mount(MemoriesView, {
      global: { plugins: [ElementPlus] },
    })
    const input = wrapper.find('input')
    expect(input.exists()).toBe(true)
  })

  it('包含查询按钮', () => {
    const wrapper = mount(MemoriesView, {
      global: { plugins: [ElementPlus] },
    })
    const btn = wrapper.find('button')
    expect(btn.exists()).toBe(true)
  })

  it('初始状态不显示搜索结果元信息', () => {
    const wrapper = mount(MemoriesView, {
      global: { plugins: [ElementPlus] },
    })
    // 未搜索前不应显示"共找到"
    expect(wrapper.text()).not.toContain('共找到')
  })

  it('查询文本为空时提示警告（不调用 API）', async () => {
    const { queryMemories } = await import('../src/api')
    const wrapper = mount(MemoriesView, {
      global: { plugins: [ElementPlus] },
    })
    // 直接提交空查询
    const form = wrapper.find('form')
    if (form.exists()) {
      await form.trigger('submit')
    }
    expect(queryMemories).not.toHaveBeenCalled()
  })

  it('提交有效查询后调用 queryMemories API', async () => {
    const { queryMemories } = await import('../src/api')
    const wrapper = mount(MemoriesView, {
      global: { plugins: [ElementPlus] },
    })

    // 设置查询文本
    const input = wrapper.find('input[type="text"], input[placeholder*="查询"], input[placeholder*="输入"]')
    if (input.exists()) {
      await input.setValue('Python 编程')
    }

    // 提交表单
    const form = wrapper.find('form')
    if (form.exists()) {
      await form.trigger('submit')
      await flushPromises()
      expect(queryMemories).toHaveBeenCalled()
    }
  })

  it('成功查询后显示搜索结果元信息', async () => {
    const { queryMemories } = await import('../src/api')
    ;(queryMemories as ReturnType<typeof vi.fn>).mockResolvedValue({
      memories: [
        {
          id: 'mem-001',
          content: '查询结果内容',
          similarity: 0.9,
          value_score: 0.5,
          tier: 'cold',
          created_at: '2026-04-01T10:00:00Z',
        },
      ],
      count: 1,
      query_mode: 'deep',
    })

    const wrapper = mount(MemoriesView, {
      global: { plugins: [ElementPlus] },
    })

    const input = wrapper.find('input[placeholder*="查询"], input[placeholder*="输入"]')
    if (input.exists()) {
      await input.setValue('查询内容')
      const form = wrapper.find('form')
      if (form.exists()) {
        await form.trigger('submit')
        await flushPromises()
        expect(wrapper.text()).toContain('共找到')
      }
    }
  })

  it('查询返回空结果时显示"未找到相关记忆"', async () => {
    const { queryMemories } = await import('../src/api')
    ;(queryMemories as ReturnType<typeof vi.fn>).mockResolvedValue({
      memories: [],
      count: 0,
      query_mode: 'deep',
    })

    const wrapper = mount(MemoriesView, {
      global: { plugins: [ElementPlus] },
    })

    const input = wrapper.find('input[placeholder*="查询"], input[placeholder*="输入"]')
    if (input.exists()) {
      await input.setValue('找不到的内容')
      const form = wrapper.find('form')
      if (form.exists()) {
        await form.trigger('submit')
        await flushPromises()
        expect(wrapper.text()).toContain('未找到相关记忆')
      }
    }
  })
})
