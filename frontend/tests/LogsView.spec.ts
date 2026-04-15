import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import ElementPlus from 'element-plus'
import LogsView from '../src/views/LogsView.vue'

vi.mock('../src/api', () => ({
  getSaveLogs: vi.fn().mockResolvedValue({
    logs: Array.from({ length: 25 }).map((_, idx) => {
      const id = 25 - idx
      return {
        id,
        memory_id: `mem-${String(id).padStart(3, '0')}`,
        content: `存储日志内容-${id}`,
        created_at: `2026-04-${String(id).padStart(2, '0')}T10:00:00Z`,
        memory_deleted: false,
        is_garbled: false,
      }
    }),
    count: 25,
  }),
  getQueryLogs: vi.fn().mockResolvedValue({
    logs: Array.from({ length: 22 }).map((_, idx) => {
      const id = 22 - idx
      return {
        id,
        query: `查询条件-${id}`,
        results: JSON.stringify([{ id: `r-${id}` }]),
        fast_only: id % 2 === 0,
        created_at: `2026-04-${String(id).padStart(2, '0')}T11:00:00Z`,
      }
    }),
    count: 22,
  }),
}))

describe('LogsView 视图', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('挂载时加载存储日志并显示时间范围查询和分页', async () => {
    const { getSaveLogs } = await import('../src/api')
    const wrapper = mount(LogsView, {
      global: { plugins: [ElementPlus] },
    })
    await flushPromises()

    expect(getSaveLogs).toHaveBeenCalledTimes(1)
    expect(wrapper.text()).toContain('时间范围')
    expect(wrapper.text()).toContain('共 25 条')
    expect(wrapper.text()).toContain('mem-025')
    expect(wrapper.text()).not.toContain('mem-005')
    expect(wrapper.text()).toContain('存储操作日志')
    expect(wrapper.text()).toContain('查询操作日志')
  })

  it('挂载时不主动加载查询日志（切换标签后才加载）', async () => {
    const { getQueryLogs } = await import('../src/api')
    mount(LogsView, {
      global: { plugins: [ElementPlus] },
    })
    await flushPromises()
    expect(getQueryLogs).not.toHaveBeenCalled()
  })

  it('存储日志支持翻页', async () => {
    const wrapper = mount(LogsView, {
      global: { plugins: [ElementPlus] },
    })
    await flushPromises()

    const pageTwoButton = wrapper.findAll('.el-pager li').find((li) => li.text() === '2')
    expect(pageTwoButton).toBeTruthy()
    await pageTwoButton!.trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('mem-005')
  })

  it('查询日志标签支持按时间筛选和分页', async () => {
    const { getQueryLogs } = await import('../src/api')
    const wrapper = mount(LogsView, {
      global: { plugins: [ElementPlus] },
    })
    await flushPromises()

    await wrapper.findAll('.el-tabs__item')[1].trigger('click')
    await flushPromises()
    expect(getQueryLogs).toHaveBeenCalledTimes(1)

    const datePickers = wrapper.findAllComponents({ name: 'ElDatePicker' })
    await datePickers[1].vm.$emit('update:modelValue', ['2026-04-20T00:00:00', '2026-04-20T23:59:59'])
    await flushPromises()

    const queryButtons = wrapper.findAll('button').filter((btn) => btn.text().includes('查询'))
    await queryButtons[1].trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('共 1 条')
    expect(wrapper.text()).toContain('查询条件-20')
  })

  it('查询结果字段为空时显示占位符，不抛出解析错误', async () => {
    const { getQueryLogs } = await import('../src/api')
    vi.mocked(getQueryLogs).mockResolvedValueOnce({
      logs: [
        {
          id: 1,
          query: '空结果测试',
          results: '',
          fast_only: false,
          created_at: '2026-04-21T11:00:00Z',
        },
      ],
      count: 1,
    })
    const wrapper = mount(LogsView, {
      global: { plugins: [ElementPlus] },
    })
    await flushPromises()

    await wrapper.findAll('.el-tabs__item')[1].trigger('click')
    await flushPromises()
    expect(wrapper.text()).toContain('--')
  })
})
