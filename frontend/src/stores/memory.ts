import { defineStore } from 'pinia'
import { ref } from 'vue'
import { queryMemories, deleteMemory } from '../api'
import type { Memory } from '../api/types'

/** 记忆状态管理 Store */
export const useMemoryStore = defineStore('memory', () => {
  const memories = ref<Memory[]>([])
  const loading = ref(false)
  const queryMode = ref<string>('')
  const count = ref(0)

  /** 查询记忆列表 */
  async function fetchMemories(
    query: string,
    topK: number = 5,
    fastOnly: boolean = false,
  ): Promise<void> {
    loading.value = true
    try {
      const res = await queryMemories(query, topK, fastOnly)
      memories.value = res.memories
      count.value = res.count
      queryMode.value = res.query_mode
    } finally {
      loading.value = false
    }
  }

  /** 删除指定记忆并从列表中移除 */
  async function removeMemory(memoryId: string): Promise<void> {
    await deleteMemory(memoryId)
    memories.value = memories.value.filter((m) => m.id !== memoryId)
    count.value = memories.value.length
  }

  return { memories, loading, queryMode, count, fetchMemories, removeMemory }
})
