import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import ElementPlus from 'element-plus'
import MemoriesView from '../src/views/MemoriesView.vue'

const push = vi.fn()

vi.mock('vue-router', () => ({
  useRouter: () => ({ push }),
}))

vi.mock('../src/api', () => ({
  getSaveLogs: vi.fn().mockResolvedValue({
    logs: Array.from({ length: 25 }).map((_, idx) => {
      const n = 25 - idx
      return {
        id: n,
        memory_id: `mem-${String(n).padStart(3, '0')}`,
        content: `内容-${n}`,
        created_at: `2026-04-${String((n % 28) + 1).padStart(2, '0')}T10:00:00Z`,
        memory_deleted: false,
        is_garbled: false,
      }
    }),
    count: 25,
  }),
}))

describe('MemoriesView 视图', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('挂载后默认加载最近记忆列表并显示总数', async () => {
    const { getSaveLogs } = await import('../src/api')
    const wrapper = mount(MemoriesView, {
      global: { plugins: [ElementPlus] },
    })
    await flushPromises()

    expect(getSaveLogs).toHaveBeenCalledTimes(1)
    expect(wrapper.text()).toContain('记忆管理')
    expect(wrapper.text()).toContain('共 25 条记忆')
    expect(wrapper.text()).toContain('mem-025')
    expect(wrapper.text()).not.toContain('mem-001')
  })

  it('支持按记忆 ID 查询', async () => {
    const wrapper = mount(MemoriesView, {
      global: { plugins: [ElementPlus] },
    })
    await flushPromises()

    const input = wrapper.find('input[placeholder*="记忆 ID"]')
    await input.setValue('mem-003')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(wrapper.text()).toContain('mem-003')
    expect(wrapper.text()).not.toContain('mem-025')
  })

  it('点击查看详情时跳转到详情页', async () => {
    const wrapper = mount(MemoriesView, {
      global: { plugins: [ElementPlus] },
    })
    await flushPromises()

    const detailBtn = wrapper.findAll('button').find((btn) => btn.text().includes('查看详情'))
    expect(detailBtn).toBeTruthy()
    await detailBtn!.trigger('click')

    expect(push).toHaveBeenCalled()
    expect(push.mock.calls[0][0]).toMatchObject({
      path: expect.stringContaining('/memories/'),
      state: expect.objectContaining({
        memory: expect.objectContaining({ memory_id: expect.any(String) }),
      }),
    })
  })
})
