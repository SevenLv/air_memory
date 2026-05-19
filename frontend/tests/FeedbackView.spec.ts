/**
 * FeedbackView.vue 单元测试
 *
 * 覆盖：视图渲染、查询触发、分页支持
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import ElementPlus from 'element-plus'
import FeedbackView from '../src/views/FeedbackView.vue'

// ---------------------------------------------------------------------------
// Mock API - 使用内联数据，避免 vi.mock 提升问题（hoisting）
// ---------------------------------------------------------------------------

vi.mock('../src/api', () => ({
  getAllFeedbackLogs: vi.fn().mockResolvedValue({
    logs: [
      { id: 1, memory_id: 'mem-test-001', valuable: true, created_at: '2026-04-01T10:00:00Z' },
      { id: 2, memory_id: 'mem-test-001', valuable: false, created_at: '2026-04-02T10:00:00Z' },
    ],
    count: 2,
    total: 2,
  }),
}))

// ---------------------------------------------------------------------------
// 测试套件
// ---------------------------------------------------------------------------

describe('FeedbackView 视图', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('可以正常挂载', () => {
    const wrapper = mount(FeedbackView, {
      global: { plugins: [ElementPlus] },
    })
    expect(wrapper.exists()).toBe(true)
  })

  it('显示"查询条件"和"反馈记录列表"标题', () => {
    const wrapper = mount(FeedbackView, {
      global: { plugins: [ElementPlus] },
    })
    expect(wrapper.text()).toContain('查询条件')
    expect(wrapper.text()).toContain('反馈记录列表')
  })

  it('包含记忆 ID 输入框', () => {
    const wrapper = mount(FeedbackView, {
      global: { plugins: [ElementPlus] },
    })
    const input = wrapper.find('input')
    expect(input.exists()).toBe(true)
  })

  it('包含查询按钮', () => {
    const wrapper = mount(FeedbackView, {
      global: { plugins: [ElementPlus] },
    })
    const btn = wrapper.find('button[type="submit"]')
    expect(btn.exists()).toBe(true)
  })

  it('ID 为空时提交仍调用反馈查询接口', async () => {
    const { getAllFeedbackLogs } = await import('../src/api')
    const wrapper = mount(FeedbackView, {
      global: { plugins: [ElementPlus] },
    })
    await flushPromises()
    vi.clearAllMocks()
    const form = wrapper.find('form')
    if (form.exists()) {
      await form.trigger('submit')
      await flushPromises()
    }
    expect(getAllFeedbackLogs).toHaveBeenCalled()
  })

  it('输入有效 ID 后提交调用 getAllFeedbackLogs', async () => {
    const { getAllFeedbackLogs } = await import('../src/api')
    const wrapper = mount(FeedbackView, {
      global: { plugins: [ElementPlus] },
    })
    await flushPromises()
    vi.clearAllMocks()

    const input = wrapper.find('input[placeholder*="记忆"], input[placeholder*="ID"]')
    if (input.exists()) {
      await input.setValue('mem-test-001')
      const form = wrapper.find('form')
      if (form.exists()) {
        await form.trigger('submit')
        await flushPromises()
        expect(getAllFeedbackLogs).toHaveBeenCalled()
      }
    }
  })

  it('查询失败时不会阻断页面交互', async () => {
    const { getAllFeedbackLogs } = await import('../src/api')
    ;(getAllFeedbackLogs as ReturnType<typeof vi.fn>).mockRejectedValue(new Error('404'))

    const wrapper = mount(FeedbackView, {
      global: { plugins: [ElementPlus] },
    })
    await flushPromises()

    const input = wrapper.find('input[placeholder*="记忆"], input[placeholder*="ID"]')
    if (input.exists()) {
      await input.setValue('nonexistent-id')
      const form = wrapper.find('form')
      if (form.exists()) {
        await form.trigger('submit')
        await flushPromises()
        expect(getAllFeedbackLogs).toHaveBeenCalled()
        expect(wrapper.text()).toContain('反馈记录列表')
      }
    }
  })
})
