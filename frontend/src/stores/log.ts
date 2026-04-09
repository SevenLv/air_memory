import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getSaveLogs, getQueryLogs } from '../api'
import type { SaveLog, QueryLog } from '../api/types'

/** 日志状态管理 Store */
export const useLogStore = defineStore('log', () => {
  const saveLogs = ref<SaveLog[]>([])
  const queryLogs = ref<QueryLog[]>([])
  const saveLoading = ref(false)
  const queryLoading = ref(false)

  /** 获取存储操作日志 */
  async function fetchSaveLogs(): Promise<void> {
    saveLoading.value = true
    try {
      const res = await getSaveLogs()
      saveLogs.value = res.logs
    } finally {
      saveLoading.value = false
    }
  }

  /** 获取查询操作日志 */
  async function fetchQueryLogs(): Promise<void> {
    queryLoading.value = true
    try {
      const res = await getQueryLogs()
      queryLogs.value = res.logs
    } finally {
      queryLoading.value = false
    }
  }

  return { saveLogs, queryLogs, saveLoading, queryLoading, fetchSaveLogs, fetchQueryLogs }
})
