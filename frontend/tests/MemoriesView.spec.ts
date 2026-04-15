import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import ElementPlus from 'element-plus'
import { createRouter, createWebHashHistory } from 'vue-router'
import MemoriesView from '../src/views/MemoriesView.vue'

vi.mock('../src/api', () => ({
  getMemoryManageList: vi.fn().mockResolvedValue({
    logs: [
      {
        id: 1,
        memory_id: 'mem-001',
        content: '测试记忆内容',
        created_at: '2026-04-01T10:00:00Z',
        memory_deleted: false,
        is_garbled: false,
        value_score: 0.6,
      },
    ],
    count: 1,
    total: 1,
  }),
}))

describe('MemoriesView 视图（记忆管理）', () => {
  const router = createRouter({
    history: createWebHashHistory(),
    routes: [
      { path: '/memories', component: MemoriesView },
      { path: '/memories/:memoryId', component: { template: '<div>detail</div>' } },
    ],
  })

  beforeEach(async () => {
    vi.clearAllMocks()
    await router.push('/memories')
    await router.isReady()
  })

  it('挂载后默认加载最近记忆列表', async () => {
    const { getMemoryManageList } = await import('../src/api')
    mount(MemoriesView, {
      global: { plugins: [ElementPlus, router] },
    })
    await flushPromises()
    expect(getMemoryManageList).toHaveBeenCalledWith(
      expect.objectContaining({ page: 1, pageSize: 20 }),
    )
  })

  it('显示列表标题与数据', async () => {
    const wrapper = mount(MemoriesView, {
      global: { plugins: [ElementPlus, router] },
    })
    await flushPromises()
    expect(wrapper.text()).toContain('最近记忆列表')
    expect(wrapper.text()).toContain('mem-001')
  })

  it('提交记忆 ID 查询时带上筛选参数', async () => {
    const { getMemoryManageList } = await import('../src/api')
    const wrapper = mount(MemoriesView, {
      global: { plugins: [ElementPlus, router] },
    })
    await flushPromises()
    const input = wrapper.find('input[placeholder*="记忆 ID"]')
    await input.setValue('mem-001')
    await wrapper.find('form').trigger('submit')
    await flushPromises()
    expect(getMemoryManageList).toHaveBeenLastCalledWith(
      expect.objectContaining({ memoryId: 'mem-001', page: 1, pageSize: 20 }),
    )
  })

  it('点击查看详情可跳转到详情路由', async () => {
    const wrapper = mount(MemoriesView, {
      global: { plugins: [ElementPlus, router] },
    })
    await flushPromises()
    const detailBtn = wrapper.findAll('button').find((btn) => btn.text().includes('查看详情'))
    expect(detailBtn).toBeDefined()
    await detailBtn!.trigger('click')
    await flushPromises()
    expect(router.currentRoute.value.path).toBe('/memories/mem-001')
  })
})
