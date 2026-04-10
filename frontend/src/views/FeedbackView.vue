<template>
  <div class="feedback-view">
    <!-- 查询面板 -->
    <el-card class="query-card">
      <template #header>
        <span class="card-title">反馈记录查询</span>
      </template>
      <el-form :model="form" inline @submit.prevent="handleSearch">
        <el-form-item label="记忆 ID">
          <el-input
            v-model="form.memoryId"
            placeholder="请输入记忆 ID"
            clearable
            style="width: 360px"
          />
        </el-form-item>
        <el-form-item>
          <el-button
            type="primary"
            :loading="loading"
            native-type="submit"
            :icon="Search"
          >
            查询
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 价值评分面板 -->
    <el-card v-if="valueScore" class="value-card">
      <template #header>
        <span class="card-title">综合价值评分</span>
      </template>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="记忆 ID">
          {{ valueScore.memory_id }}
        </el-descriptions-item>
        <el-descriptions-item label="所在层">
          <el-tag :type="valueScore.tier === 'hot' ? 'danger' : 'info'">
            {{ valueScore.tier === 'hot' ? '热层' : '冷层' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="综合价值评分">
          <el-progress
            :percentage="Math.round(valueScore.value_score * 100)"
            :color="scoreColor(valueScore.value_score)"
            style="width: 200px"
          />
          <span class="score-text">{{ valueScore.value_score.toFixed(4) }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="反馈次数">
          {{ valueScore.feedback_count }}
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- 反馈历史表格 -->
    <el-card v-if="feedbackLogs !== null" class="logs-card">
      <template #header>
        <div class="logs-header">
          <span class="card-title">历次反馈记录</span>
          <el-tag type="info">共 {{ feedbackLogs.length }} 条</el-tag>
        </div>
      </template>
      <LogTable :data="feedbackLogs" :loading="loading">
        <el-table-column prop="id" label="ID" width="70" align="center" />
        <el-table-column prop="created_at" label="时间" width="200" />
        <el-table-column prop="memory_id" label="记忆 ID" show-overflow-tooltip />
        <el-table-column label="反馈结果" width="120" align="center">
          <template #default="{ row }">
            <el-tag :type="row.valuable ? 'success' : 'danger'" size="small">
              {{ row.valuable ? '有价值' : '无价值' }}
            </el-tag>
          </template>
        </el-table-column>
      </LogTable>
    </el-card>

    <!-- 空状态 -->
    <div v-if="hasSearched && !valueScore && !loading" class="empty-tip">
      <el-empty description="未找到该记忆的评分信息" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import { getValueScore, getFeedbackLogs } from '../api'
import type { MemoryValueScore, FeedbackLog } from '../api/types'
import LogTable from '../components/LogTable.vue'

const form = reactive({ memoryId: '' })
const loading = ref(false)
const hasSearched = ref(false)
const valueScore = ref<MemoryValueScore | null>(null)
const feedbackLogs = ref<FeedbackLog[] | null>(null)

/** 根据评分返回进度条颜色 */
function scoreColor(score: number): string {
  if (score >= 0.7) return '#67c23a'
  if (score >= 0.4) return '#e6a23c'
  return '#f56c6c'
}

/** 查询指定记忆的价值评分与反馈历史 */
async function handleSearch(): Promise<void> {
  const id = form.memoryId.trim()
  if (!id) {
    ElMessage.warning('请输入记忆 ID')
    return
  }
  hasSearched.value = true
  loading.value = true
  valueScore.value = null
  feedbackLogs.value = null
  try {
    const [vs, fl] = await Promise.all([
      getValueScore(id),
      getFeedbackLogs(id),
    ])
    valueScore.value = vs
    feedbackLogs.value = fl.logs
  } catch {
    // 错误已由 axios 拦截器统一提示
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.feedback-view {
  padding: 24px;
}

.query-card {
  margin-bottom: 20px;
}

.value-card {
  margin-bottom: 20px;
}

.logs-card {
  margin-bottom: 20px;
}

.card-title {
  font-size: 1rem;
  font-weight: 600;
}

.logs-header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.score-text {
  margin-left: 8px;
  font-size: 0.9rem;
  color: #606266;
}

.empty-tip {
  padding: 40px 0;
}
</style>
