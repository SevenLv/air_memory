import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import ElementPlus from 'element-plus'
import InputsView from '../src/views/InputsView.vue'

const push = vi.fn()

vi.mock('vue-router', () => ({
  useRouter: () => ({ push }),
}))

vi.mock('../src/api', () => ({
  getInputs: vi.fn().mockResolvedValue({
    inputs: [
      {
        input_id: 'input-001',
        query: '第一条输入',
        created_at: '2026-05-01T10:00:00Z',
      },
    ],
    count: 1,
    total: 1,
  }),
}))

describe('InputsView 视图', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('挂载后加载输入信息列表并支持跳转详情', async () => {
    const { getInputs } = await import('../src/api')
    const wrapper = mount(InputsView, {
      global: { plugins: [ElementPlus] },
    })
    await flushPromises()

    expect(getInputs).toHaveBeenCalled()
    expect(wrapper.text()).toContain('输入信息管理')
    expect(wrapper.text()).toContain('input-001')

    const detailBtn = wrapper.findAll('button').find((btn) => btn.text().includes('查看详情'))
    expect(detailBtn).toBeTruthy()
    await detailBtn!.trigger('click')

    expect(push).toHaveBeenCalledWith({
      name: 'input-detail',
      params: { inputId: 'input-001' },
      state: {
        input: {
          input_id: 'input-001',
          query: '第一条输入',
          created_at: '2026-05-01T10:00:00Z',
        },
      },
    })
  })
})
