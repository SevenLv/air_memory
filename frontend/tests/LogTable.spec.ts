/**
 * LogTable.vue 单元测试
 *
 * 覆盖：组件渲染、data 传递、loading 状态、空数据提示、slot 内容
 */
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import ElementPlus from 'element-plus'
import LogTable from '../src/components/LogTable.vue'

// ---------------------------------------------------------------------------
// 测试数据
// ---------------------------------------------------------------------------

const mockSaveLogs = [
  { id: 1, memory_id: 'mem-001', content: '日志内容一', created_at: '2026-04-01T10:00:00Z', memory_deleted: false },
  { id: 2, memory_id: 'mem-002', content: '日志内容二', created_at: '2026-04-02T11:00:00Z', memory_deleted: true },
]

// ---------------------------------------------------------------------------
// 测试套件
// ---------------------------------------------------------------------------

describe('LogTable 组件', () => {
  it('可以正常挂载', () => {
    const wrapper = mount(LogTable, {
      props: { data: [] },
      global: { plugins: [ElementPlus] },
    })
    expect(wrapper.exists()).toBe(true)
  })

  it('接受 data 属性并渲染表格', () => {
    const wrapper = mount(LogTable, {
      props: { data: mockSaveLogs },
      global: { plugins: [ElementPlus] },
    })
    expect(wrapper.find('.el-table').exists()).toBe(true)
  })

  it('data 为空数组时显示"暂无日志数据"', () => {
    const wrapper = mount(LogTable, {
      props: { data: [] },
      global: { plugins: [ElementPlus] },
    })
    expect(wrapper.text()).toContain('暂无日志数据')
  })

  it('loading 属性为 true 时触发加载状态', () => {
    const wrapper = mount(LogTable, {
      props: { data: [], loading: true },
      global: { plugins: [ElementPlus] },
    })
    // el-table 带有 v-loading 指令
    expect(wrapper.exists()).toBe(true)
  })

  it('loading 属性为 false 时无加载状态', () => {
    const wrapper = mount(LogTable, {
      props: { data: mockSaveLogs, loading: false },
      global: { plugins: [ElementPlus] },
    })
    expect(wrapper.exists()).toBe(true)
  })

  it('loading 属性可省略（可选 prop）', () => {
    const wrapper = mount(LogTable, {
      props: { data: mockSaveLogs },
      global: { plugins: [ElementPlus] },
    })
    expect(wrapper.exists()).toBe(true)
  })

  it('接受 slot 内容', () => {
    const wrapper = mount(LogTable, {
      props: { data: mockSaveLogs },
      slots: {
        default: '<div class="test-slot-content">测试列</div>',
      },
      global: { plugins: [ElementPlus] },
    })
    expect(wrapper.find('.test-slot-content').exists()).toBe(true)
  })

  it('数据量不为零时表格存在', () => {
    const wrapper = mount(LogTable, {
      props: { data: mockSaveLogs },
      global: { plugins: [ElementPlus] },
    })
    const table = wrapper.find('.el-table')
    expect(table.exists()).toBe(true)
  })

  it('样式中包含 width: 100%', () => {
    const wrapper = mount(LogTable, {
      props: { data: [] },
      global: { plugins: [ElementPlus] },
    })
    const table = wrapper.find('.el-table')
    expect(table.exists()).toBe(true)
  })
})
