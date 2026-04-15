<template>
  <div class="memory-detail-view">
    <el-card class="detail-card" v-loading="loading">
      <template #header>
        <div class="detail-header">
          <span class="card-title">记忆详情</span>
          <el-button type="primary" link @click="goBack">返回列表</el-button>
        </div>
      </template>

      <el-empty v-if="!loading && !detail" description="未找到记忆详情" />

      <el-descriptions v-else-if="detail" :column="1" border>
        <el-descriptions-item label="日志 ID">{{ detail.id }}</el-descriptions-item>
        <el-descriptions-item label="记忆 ID">{{ detail.memory_id }}</el-descriptions-item>
        <el-descriptions-item label="提交时间">
          {{ formatLocalTime(detail.created_at) }}
        </el-descriptions-item>
        <el-descriptions-item label="原始数据">
          <pre class="detail-content">{{ detail.content }}</pre>
        </el-descriptions-item>
        <el-descriptions-item label="价值评分">
          {{ Number(detail.value_score).toFixed(4) }}
        </el-descriptions-item>
        <el-descriptions-item label="所在层级">{{ detail.tier }}</el-descriptions-item>
        <el-descriptions-item label="反馈次数">{{ detail.feedback_count }}</el-descriptions-item>
        <el-descriptions-item label="评分更新时间">
          {{ detail.value_updated_at ? formatLocalTime(detail.value_updated_at) : '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="状态">
          {{ detail.memory_deleted ? '已删除' : '存在' }}
        </el-descriptions-item>
      </el-descriptions>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getMemoryDetail } from '../api'
import type { MemoryDetail } from '../api/types'
import { formatLocalTime } from '../utils/time'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const detail = ref<MemoryDetail | null>(null)

function goBack(): void {
  router.push('/memories')
}

async function fetchDetail(): Promise<void> {
  const memoryId = String(route.params.memoryId || '').trim()
  if (!memoryId) {
    detail.value = null
    return
  }
  loading.value = true
  try {
    detail.value = await getMemoryDetail(memoryId)
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

.detail-card {
  margin-bottom: 20px;
}

.detail-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.card-title {
  font-size: 1rem;
  font-weight: 600;
}

.detail-content {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  font-family: inherit;
}
</style>
