import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import ElementPlus from 'element-plus'
import { createRouter, createWebHashHistory } from 'vue-router'
import MemoryDetailView from '../src/views/MemoryDetailView.vue'

vi.mock('../src/api', () => ({
  getMemoryDetail: vi.fn().mockResolvedValue({
    id: 1,
    memory_id: 'mem-001',
    content: '详细原始数据',
    created_at: '2026-04-01T10:00:00Z',
    memory_deleted: false,
    is_garbled: false,
    value_score: 0.88,
    tier: 'hot',
    feedback_count: 3,
    value_updated_at: '2026-04-01T11:00:00Z',
    message: 'ok',
  }),
}))

describe('MemoryDetailView 视图', () => {
  const router = createRouter({
    history: createWebHashHistory(),
    routes: [
      { path: '/memories', component: { template: '<div>list</div>' } },
      { path: '/memories/:memoryId', component: MemoryDetailView },
    ],
  })

  beforeEach(async () => {
    vi.clearAllMocks()
    await router.push('/memories/mem-001')
    await router.isReady()
  })

  it('挂载后加载并展示记忆详情字段', async () => {
    const { getMemoryDetail } = await import('../src/api')
    const wrapper = mount(MemoryDetailView, {
      global: { plugins: [ElementPlus, router] },
    })
    await flushPromises()
    expect(getMemoryDetail).toHaveBeenCalledWith('mem-001')
    expect(wrapper.text()).toContain('mem-001')
    expect(wrapper.text()).toContain('详细原始数据')
    expect(wrapper.text()).toContain('0.8800')
  })
})
