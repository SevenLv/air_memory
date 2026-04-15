<template>
  <div class="memory-detail-view">
    <el-card>
      <template #header>
        <div class="header-row">
          <span class="card-title">记忆详情</span>
          <el-button link type="primary" @click="router.back()">返回列表</el-button>
        </div>
      </template>

      <div v-if="loading">
        <el-skeleton :rows="4" animated />
      </div>

      <el-empty v-else-if="!detail" description="未找到该记忆" />

      <el-descriptions v-else :column="1" border>
        <el-descriptions-item label="ID">
          {{ detail.memory_id }}
        </el-descriptions-item>
        <el-descriptions-item label="原始数据">
          <pre class="content-pre">{{ detail.content }}</pre>
        </el-descriptions-item>
        <el-descriptions-item label="提交时间">
          {{ formatLocalTime(detail.created_at) }}
        </el-descriptions-item>
        <el-descriptions-item label="价值评分">
          {{ valueScoreText }}
        </el-descriptions-item>
      </el-descriptions>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getSaveLog, getValueScore } from '../api'
import type { SaveLog } from '../api/types'
import { formatLocalTime } from '../utils/time'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const detail = ref<SaveLog | null>(null)
const valueScore = ref<number | null>(null)

const valueScoreText = computed(() => {
  if (valueScore.value === null) {
    return '暂无'
  }
  return valueScore.value.toFixed(4)
})

function toSaveLog(value: unknown): SaveLog | null {
  if (!value || typeof value !== 'object') {
    return null
  }
  const v = value as Record<string, unknown>
  if (
    typeof v.id !== 'number' ||
    typeof v.memory_id !== 'string' ||
    typeof v.content !== 'string' ||
    typeof v.created_at !== 'string' ||
    typeof v.memory_deleted !== 'boolean' ||
    typeof v.is_garbled !== 'boolean'
  ) {
    return null
  }
  return {
    id: v.id,
    memory_id: v.memory_id,
    content: v.content,
    created_at: v.created_at,
    memory_deleted: v.memory_deleted,
    is_garbled: v.is_garbled,
  }
}

async function fetchDetail(): Promise<void> {
  const memoryId = String(route.params.memoryId || '')
  if (!memoryId) {
    detail.value = null
    return
  }

  const stateMemory = toSaveLog(history.state?.memory || null)
  if (stateMemory && stateMemory.memory_id === memoryId) {
    detail.value = stateMemory
  }

  loading.value = true
  try {
    if (!detail.value) {
      detail.value = await getSaveLog(memoryId)
    }
    if (detail.value && !detail.value.memory_deleted) {
      const scoreRes = await getValueScore(memoryId)
      valueScore.value = scoreRes.value_score
    }
  } catch {
    detail.value = null
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchDetail()
})
</script>

<style scoped>
.memory-detail-view {
  padding: 24px;
}

.header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  font-size: 1rem;
  font-weight: 600;
}

.content-pre {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  font-family: inherit;
}
</style>
