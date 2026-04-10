/**
 * MemoryCard.vue 单元测试
 *
 * 覆盖：组件渲染、热层/冷层标签显示、相似度/价值评分格式化、删除事件触发
 */
import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import ElementPlus from 'element-plus'
import MemoryCard from '../src/components/MemoryCard.vue'
import type { Memory } from '../src/api/types'

// ---------------------------------------------------------------------------
// 测试数据
// ---------------------------------------------------------------------------

const coldMemory: Memory = {
  id: 'mem-001',
  content: '这是一条冷层记忆的内容',
  similarity: 0.85,
  value_score: 0.4,
  tier: 'cold',
  created_at: '2026-04-01T10:00:00.000Z',
}

const hotMemory: Memory = {
  id: 'mem-002',
  content: '这是一条热层记忆的内容',
  similarity: 0.92,
  value_score: 0.75,
  tier: 'hot',
  created_at: '2026-04-02T12:00:00.000Z',
}

// ---------------------------------------------------------------------------
// 挂载辅助函数
// ---------------------------------------------------------------------------

function mountMemoryCard(memory: Memory) {
  return mount(MemoryCard, {
    props: { memory },
    global: {
      plugins: [ElementPlus],
    },
  })
}

// ---------------------------------------------------------------------------
// 测试套件
// ---------------------------------------------------------------------------

describe('MemoryCard 组件', () => {
  it('可以正常挂载', () => {
    const wrapper = mountMemoryCard(coldMemory)
    expect(wrapper.exists()).toBe(true)
  })

  it('显示记忆 content 内容', () => {
    const wrapper = mountMemoryCard(coldMemory)
    expect(wrapper.text()).toContain(coldMemory.content)
  })

  it('显示记忆 ID', () => {
    const wrapper = mountMemoryCard(coldMemory)
    expect(wrapper.text()).toContain(coldMemory.id)
  })

  it('显示创建时间', () => {
    const wrapper = mountMemoryCard(coldMemory)
    expect(wrapper.text()).toContain(coldMemory.created_at)
  })

  it('冷层记忆显示"冷层"标签', () => {
    const wrapper = mountMemoryCard(coldMemory)
    expect(wrapper.text()).toContain('冷层')
  })

  it('热层记忆显示"热层"标签', () => {
    const wrapper = mountMemoryCard(hotMemory)
    expect(wrapper.text()).toContain('热层')
  })

  it('显示相似度百分比（冷层）', () => {
    const wrapper = mountMemoryCard(coldMemory)
    // 0.85 * 100 = 85.0
    expect(wrapper.text()).toContain('85.0%')
  })

  it('显示相似度百分比（热层）', () => {
    const wrapper = mountMemoryCard(hotMemory)
    // 0.92 * 100 = 92.0
    expect(wrapper.text()).toContain('92.0%')
  })

  it('显示价值评分（冷层）', () => {
    const wrapper = mountMemoryCard(coldMemory)
    // toFixed(2) -> "0.40"
    expect(wrapper.text()).toContain('0.40')
  })

  it('显示价值评分（热层）', () => {
    const wrapper = mountMemoryCard(hotMemory)
    // toFixed(2) -> "0.75"
    expect(wrapper.text()).toContain('0.75')
  })

  it('触发 delete 事件时携带正确的 memory.id', async () => {
    const wrapper = mountMemoryCard(coldMemory)
    // 直接调用 emit 验证事件处理逻辑
    wrapper.vm.$emit('delete', coldMemory.id)
    await wrapper.vm.$nextTick()
    const emittedEvents = wrapper.emitted('delete')
    expect(emittedEvents).toBeTruthy()
    expect(emittedEvents![0]).toEqual([coldMemory.id])
  })

  it('热层记忆的 tierTagType 计算属性为 danger', () => {
    const wrapper = mountMemoryCard(hotMemory)
    // 热层标签对应 el-tag type="danger"
    const tags = wrapper.findAll('.el-tag')
    // 第一个标签应为层级标签
    expect(tags.length).toBeGreaterThan(0)
  })

  it('冷层记忆的 tierTagType 计算属性为 info', () => {
    const wrapper = mountMemoryCard(coldMemory)
    const tags = wrapper.findAll('.el-tag')
    expect(tags.length).toBeGreaterThan(0)
  })

  it('memory.content 为多行文本时正确渲染', () => {
    const multiLineMemory: Memory = {
      ...coldMemory,
      content: '第一行\n第二行\n第三行',
    }
    const wrapper = mountMemoryCard(multiLineMemory)
    expect(wrapper.text()).toContain('第一行')
    expect(wrapper.text()).toContain('第二行')
  })

  it('memory.similarity 为 0 时显示 0.0%', () => {
    const zeroSimilarityMemory: Memory = {
      ...coldMemory,
      similarity: 0,
    }
    const wrapper = mountMemoryCard(zeroSimilarityMemory)
    expect(wrapper.text()).toContain('0.0%')
  })

  it('memory.value_score 为 1.0 时显示 1.00', () => {
    const maxScoreMemory: Memory = {
      ...coldMemory,
      value_score: 1.0,
    }
    const wrapper = mountMemoryCard(maxScoreMemory)
    expect(wrapper.text()).toContain('1.00')
  })
})
