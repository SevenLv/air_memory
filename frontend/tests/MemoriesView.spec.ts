import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import ElementPlus from 'element-plus'
import { ElMessageBox } from 'element-plus'
import MemoriesView from '../src/views/MemoriesView.vue'

const push = vi.fn()

vi.mock('vue-router', () => ({
  useRouter: () => ({ push }),
}))

vi.mock('../src/api', () => ({
  getSaveLogs: vi.fn().mockResolvedValue({
    logs: Array.from({ length: 25 }).map((_, idx) => {
      const n = 25 - idx
      const scoreMap: Record<number, number> = {
        25: 0.85,
        23: 0.55,
        22: 0.25,
      }
      return {
        id: n,
        memory_id: `mem-${String(n).padStart(3, '0')}`,
        content: `内容-${n}`,
        created_at: `2026-04-${String((n % 28) + 1).padStart(2, '0')}T10:00:00Z`,
        memory_deleted: n === 24,
        value_score: scoreMap[n] ?? Number((n / 100).toFixed(2)),
        is_garbled: false,
      }
    }),
    count: 25,
  }),
  deleteMemory: vi.fn().mockResolvedValue(undefined),
}))

describe('MemoriesView 视图', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.spyOn(ElMessageBox, 'confirm').mockResolvedValue('confirm' as never)
  })

  it('挂载后默认加载最近记忆列表并显示总数', async () => {
    const { getSaveLogs } = await import('../src/api')
    const wrapper = mount(MemoriesView, {
      global: { plugins: [ElementPlus] },
    })
    await flushPromises()

    expect(getSaveLogs).toHaveBeenCalledTimes(1)
    expect(wrapper.text()).toContain('记忆管理')
    expect(wrapper.text()).toContain('共 24 条记忆')
    expect(wrapper.text()).toContain('mem-025')
    expect(wrapper.text()).not.toContain('mem-024')
    expect(wrapper.text()).toContain('0.25')
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

  it('点击删除后调用删除接口并从列表移除', async () => {
    const { deleteMemory } = await import('../src/api')
    const wrapper = mount(MemoriesView, {
      global: { plugins: [ElementPlus] },
    })
    await flushPromises()

    const rowTextBefore = wrapper.text()
    expect(rowTextBefore).toContain('mem-025')

    const deleteBtn = wrapper.findAll('button').find((btn) => btn.text().includes('删除'))
    expect(deleteBtn).toBeTruthy()
    await deleteBtn!.trigger('click')
    await flushPromises()

    expect(deleteMemory).toHaveBeenCalledWith('mem-025')
    expect(wrapper.text()).not.toContain('mem-025')
  })

  it('根据评价值为行设置背景色对应的样式类', async () => {
    const wrapper = mount(MemoriesView, {
      global: { plugins: [ElementPlus] },
    })
    await flushPromises()

    const html = wrapper.html()
    expect(html).toContain('memory-row-high')
    expect(html).toContain('memory-row-medium')
    expect(html).toContain('memory-row-low')
  })
})
