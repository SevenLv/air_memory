import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import ElementPlus from 'element-plus'
import MemoryDetailView from '../src/views/MemoryDetailView.vue'

const back = vi.fn()

vi.mock('vue-router', () => ({
  useRoute: () => ({ params: { memoryId: 'mem-001%3Apart' } }),
  useRouter: () => ({ back }),
}))

vi.mock('../src/api', () => ({
  getSaveLog: vi.fn().mockResolvedValue({
    id: 1,
    memory_id: 'mem-001:part',
    content: '这是一条原始记忆',
    created_at: '2026-04-15T03:00:00Z',
    memory_deleted: false,
    total_association_score: 0.75,
    is_garbled: false,
  }),
}))

describe('MemoryDetailView 视图', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('显示记忆详情完整字段', async () => {
    const { getSaveLog } = await import('../src/api')
    const wrapper = mount(MemoryDetailView, {
      global: { plugins: [ElementPlus] },
    })
    await flushPromises()

    expect(getSaveLog).toHaveBeenCalledWith('mem-001:part')
    expect(wrapper.text()).toContain('记忆详情')
    expect(wrapper.text()).toContain('mem-001:part')
    expect(wrapper.text()).toContain('这是一条原始记忆')
    expect(wrapper.text()).toContain('价值评分')
    expect(wrapper.text()).toContain('0.7500')
  })
})
