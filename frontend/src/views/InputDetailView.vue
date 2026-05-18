<template>
  <div class="input-detail-view">
    <el-card>
      <template #header>
        <div class="header-row">
          <span class="card-title">输入信息详情</span>
          <el-button type="primary" link @click="router.back()">返回列表</el-button>
        </div>
      </template>

      <div v-if="loading">
        <el-skeleton :rows="4" animated />
      </div>

      <el-empty v-else-if="!detail" description="未找到该输入信息" />

      <div v-else>
        <el-descriptions :column="1" border class="detail-desc">
          <el-descriptions-item label="输入 ID">{{ detail.input_id }}</el-descriptions-item>
          <el-descriptions-item label="查询内容">
            <pre class="query-pre">{{ detail.query }}</pre>
          </el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ formatLocalTime(detail.created_at) }}</el-descriptions-item>
        </el-descriptions>

        <el-table :data="detail.memories" class="memory-table">
          <el-table-column prop="memory_id" label="记忆 ID" min-width="280" show-overflow-tooltip />
          <el-table-column prop="association_score" label="关联评分" width="140" align="center" />
          <el-table-column prop="total_association_score" label="关联评分总量" width="160" align="center" />
        </el-table>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getInputDetail } from '../api'
import type { InputDetail, InputInfo } from '../api/types'
import { formatLocalTime } from '../utils/time'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const detail = ref<InputDetail | null>(null)

function toInputInfo(value: unknown): InputInfo | null {
  if (!value || typeof value !== 'object') {
    return null
  }
  const v = value as Record<string, unknown>
  if (
    typeof v.input_id !== 'string' ||
    typeof v.query !== 'string' ||
    typeof v.created_at !== 'string'
  ) {
    return null
  }
  return {
    input_id: v.input_id,
    query: v.query,
    created_at: v.created_at,
  }
}

async function fetchDetail(): Promise<void> {
  const inputId = String(route.params.inputId || '')
  if (!inputId) {
    detail.value = null
    return
  }

  const stateInput = toInputInfo(history.state?.input || null)
  if (stateInput && stateInput.input_id === inputId) {
    detail.value = {
      ...stateInput,
      memories: [],
    }
  }

  loading.value = true
  try {
    detail.value = await getInputDetail(inputId)
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
.input-detail-view {
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

.detail-desc {
  margin-bottom: 16px;
}

.query-pre {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  font-family: inherit;
}
</style>
