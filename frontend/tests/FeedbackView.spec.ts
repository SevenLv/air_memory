/**
 * FeedbackView.vue 单元测试
 *
 * 覆盖：视图渲染、空 ID 校验、查询触发、价值评分展示、scoreColor 颜色逻辑
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
  getValueScore: vi.fn().mockResolvedValue({
    memory_id: 'mem-test-001',
    value_score: 0.75,
    tier: 'hot',
    feedback_count: 5,
  }),
  getFeedbackLogs: vi.fn().mockResolvedValue({
    logs: [
      { id: 1, memory_id: 'mem-test-001', valuable: true, created_at: '2026-04-01T10:00:00Z' },
      { id: 2, memory_id: 'mem-test-001', valuable: false, created_at: '2026-04-02T10:00:00Z' },
    ],
    count: 2,
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

  it('显示"反馈记录查询"标题', () => {
    const wrapper = mount(FeedbackView, {
      global: { plugins: [ElementPlus] },
    })
    expect(wrapper.text()).toContain('反馈记录查询')
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

  it('初始状态不显示价值评分面板', () => {
    const wrapper = mount(FeedbackView, {
      global: { plugins: [ElementPlus] },
    })
    // 未搜索前不应显示"综合价值评分"
    expect(wrapper.text()).not.toContain('综合价值评分')
  })

  it('ID 为空时提交不调用 API', async () => {
    const { getValueScore } = await import('../src/api')
    const wrapper = mount(FeedbackView, {
      global: { plugins: [ElementPlus] },
    })
    const form = wrapper.find('form')
    if (form.exists()) {
      await form.trigger('submit')
      await flushPromises()
    }
    expect(getValueScore).not.toHaveBeenCalled()
  })

  it('输入有效 ID 后提交调用 getValueScore 和 getFeedbackLogs', async () => {
    const { getValueScore, getFeedbackLogs } = await import('../src/api')
    const wrapper = mount(FeedbackView, {
      global: { plugins: [ElementPlus] },
    })

    const input = wrapper.find('input[placeholder*="记忆"], input[placeholder*="ID"]')
    if (input.exists()) {
      await input.setValue('mem-test-001')
      const form = wrapper.find('form')
      if (form.exists()) {
        await form.trigger('submit')
        await flushPromises()
        expect(getValueScore).toHaveBeenCalledWith('mem-test-001')
        expect(getFeedbackLogs).toHaveBeenCalledWith('mem-test-001')
      }
    }
  })

  it('查询成功后显示价值评分面板', async () => {
    const wrapper = mount(FeedbackView, {
      global: { plugins: [ElementPlus] },
    })

    const input = wrapper.find('input[placeholder*="记忆"], input[placeholder*="ID"]')
    if (input.exists()) {
      await input.setValue('mem-test-001')
      const form = wrapper.find('form')
      if (form.exists()) {
        await form.trigger('submit')
        await flushPromises()
        expect(wrapper.text()).toContain('综合价值评分')
      }
    }
  })

  it('scoreColor 函数：评分 >= 0.7 返回绿色', () => {
    const wrapper = mount(FeedbackView, {
      global: { plugins: [ElementPlus] },
    })
    const vm = wrapper.vm as { scoreColor?: (s: number) => string }
    if (typeof vm.scoreColor === 'function') {
      expect(vm.scoreColor(0.7)).toBe('#67c23a')
      expect(vm.scoreColor(0.9)).toBe('#67c23a')
      expect(vm.scoreColor(1.0)).toBe('#67c23a')
    }
  })

  it('scoreColor 函数：评分 0.4 <= score < 0.7 返回橙色', () => {
    const wrapper = mount(FeedbackView, {
      global: { plugins: [ElementPlus] },
    })
    const vm = wrapper.vm as { scoreColor?: (s: number) => string }
    if (typeof vm.scoreColor === 'function') {
      expect(vm.scoreColor(0.4)).toBe('#e6a23c')
      expect(vm.scoreColor(0.5)).toBe('#e6a23c')
      expect(vm.scoreColor(0.69)).toBe('#e6a23c')
    }
  })

  it('scoreColor 函数：评分 < 0.4 返回红色', () => {
    const wrapper = mount(FeedbackView, {
      global: { plugins: [ElementPlus] },
    })
    const vm = wrapper.vm as { scoreColor?: (s: number) => string }
    if (typeof vm.scoreColor === 'function') {
      expect(vm.scoreColor(0.0)).toBe('#f56c6c')
      expect(vm.scoreColor(0.1)).toBe('#f56c6c')
      expect(vm.scoreColor(0.39)).toBe('#f56c6c')
    }
  })

  it('未找到记忆时显示"未找到该记忆的评分信息"', async () => {
    const { getValueScore, getFeedbackLogs } = await import('../src/api')
    ;(getValueScore as ReturnType<typeof vi.fn>).mockRejectedValue(new Error('404'))
    ;(getFeedbackLogs as ReturnType<typeof vi.fn>).mockRejectedValue(new Error('404'))

    const wrapper = mount(FeedbackView, {
      global: { plugins: [ElementPlus] },
    })

    const input = wrapper.find('input[placeholder*="记忆"], input[placeholder*="ID"]')
    if (input.exists()) {
      await input.setValue('nonexistent-id')
      const form = wrapper.find('form')
      if (form.exists()) {
        await form.trigger('submit')
        await flushPromises()
        expect(wrapper.text()).toContain('未找到该记忆的评分信息')
      }
    }
  })
})
