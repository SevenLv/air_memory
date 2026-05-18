import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import ElementPlus from 'element-plus'
import InputDetailView from '../src/views/InputDetailView.vue'

const back = vi.fn()

vi.mock('vue-router', () => ({
  useRoute: () => ({ params: { inputId: 'input-001' } }),
  useRouter: () => ({ back }),
}))

vi.mock('../src/api', () => ({
  getInputDetail: vi.fn().mockResolvedValue({
    input_id: 'input-001',
    query: '输入查询内容',
    created_at: '2026-05-01T10:00:00Z',
    memories: [
      {
        memory_id: 'mem-001',
        association_score: 0.75,
        total_association_score: 1.25,
      },
    ],
  }),
}))

describe('InputDetailView 视图', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('显示输入信息详情与关联记忆', async () => {
    const wrapper = mount(InputDetailView, {
      global: { plugins: [ElementPlus] },
    })
    await flushPromises()

    expect(wrapper.text()).toContain('输入信息详情')
    expect(wrapper.text()).toContain('input-001')
    expect(wrapper.text()).toContain('输入查询内容')
    expect(wrapper.text()).toContain('mem-001')
    expect(wrapper.text()).toContain('1.25')
  })
})
