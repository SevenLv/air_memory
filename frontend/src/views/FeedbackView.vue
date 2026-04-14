<template>
  <div class="feedback-view">
    <!-- 查询条件面板 -->
    <el-card class="query-card">
      <template #header>
        <span class="card-title">查询条件</span>
      </template>
      <el-form :model="form" inline @submit.prevent="handleSearch">
        <el-form-item label="记忆 ID">
          <el-input
            v-model="form.memoryId"
            placeholder="输入记忆 ID（可选）"
            clearable
            style="width: 300px"
          />
        </el-form-item>
        <el-form-item label="时间范围">
          <el-date-picker
            v-model="form.dateRange"
            type="datetimerange"
            range-separator="至"
            start-placeholder="开始时间"
            end-placeholder="结束时间"
            format="YYYY-MM-DD HH:mm:ss"
            value-format="YYYY-MM-DDTHH:mm:ss"
            style="width: 380px"
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
          <el-button :icon="Refresh" @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 价值评分面板（仅当按记忆 ID 查询时显示） -->
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

    <!-- 反馈记录列表 -->
    <el-card class="logs-card">
      <template #header>
        <div class="logs-header">
          <span class="card-title">反馈记录列表</span>
          <el-tag v-if="total > 0" type="info">共 {{ total }} 条</el-tag>
        </div>
      </template>
      <LogTable :data="feedbackLogs" :loading="loading">
        <el-table-column prop="id" label="ID" width="70" align="center" />
        <el-table-column label="时间" width="200">
          <template #default="{ row }">
            {{ formatLocalTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="memory_id" label="记忆 ID" show-overflow-tooltip />
        <el-table-column label="反馈结果" width="120" align="center">
          <template #default="{ row }">
            <el-tag :type="row.valuable ? 'success' : 'danger'" size="small">
              {{ row.valuable ? '有价值' : '无价值' }}
            </el-tag>
          </template>
        </el-table-column>
      </LogTable>
      <!-- 分页 -->
      <div v-if="total > 0" class="pagination-wrapper">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="total"
          layout="total, sizes, prev, pager, next"
          @size-change="handlePageSizeChange"
          @current-change="handlePageChange"
        />
      </div>
      <!-- 空状态 -->
      <el-empty v-if="!loading && feedbackLogs.length === 0 && hasSearched" description="暂无反馈记录" />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { Search, Refresh } from '@element-plus/icons-vue'
import { getAllFeedbackLogs, getValueScore } from '../api'
import { formatLocalTime } from '../utils/time'
import type { FeedbackLog, MemoryValueScore } from '../api/types'
import LogTable from '../components/LogTable.vue'
import { formatLocalTime } from '../utils/time'

const form = reactive({
  memoryId: '',
  dateRange: null as [string, string] | null,
})

const loading = ref(false)
const hasSearched = ref(false)
const feedbackLogs = ref<FeedbackLog[]>([])
const valueScore = ref<MemoryValueScore | null>(null)
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)

/** 根据评分返回进度条颜色 */
function scoreColor(score: number): string {
  if (score >= 0.7) return '#67c23a'
  if (score >= 0.4) return '#e6a23c'
  return '#f56c6c'
}

/** 执行查询 */
async function handleSearch(): Promise<void> {
  currentPage.value = 1
  await fetchLogs()
}

/** 重置表单并清空结果 */
function handleReset(): void {
  form.memoryId = ''
  form.dateRange = null
  feedbackLogs.value = []
  valueScore.value = null
  total.value = 0
  hasSearched.value = false
  currentPage.value = 1
}

/** 页码变更时重新查询 */
async function handlePageChange(page: number): Promise<void> {
  currentPage.value = page
  await fetchLogs()
}

/** 每页条数变更时重新查询 */
async function handlePageSizeChange(size: number): Promise<void> {
  pageSize.value = size
  currentPage.value = 1
  await fetchLogs()
}

/** 获取反馈记录列表 */
async function fetchLogs(): Promise<void> {
  hasSearched.value = true
  loading.value = true
  valueScore.value = null
  try {
    const params = {
      page: currentPage.value,
      pageSize: pageSize.value,
      memoryId: form.memoryId.trim() || undefined,
      startTime: form.dateRange?.[0] || undefined,
      endTime: form.dateRange?.[1] || undefined,
    }
    const [logsRes] = await Promise.all([
      getAllFeedbackLogs(params),
      // 若指定了记忆 ID，同步查询价值评分
      form.memoryId.trim()
        ? getValueScore(form.memoryId.trim()).then((v) => {
            valueScore.value = v
          }).catch(() => {
            // 记忆不存在时静默处理
          })
        : Promise.resolve(),
    ])
    feedbackLogs.value = logsRes.logs
    total.value = logsRes.total
  } catch {
    // 错误已由 axios 拦截器统一提示
  } finally {
    loading.value = false
  }
}

// 初始加载全部反馈记录（第一页）
onMounted(() => {
  fetchLogs()
})
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

.pagination-wrapper {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
</style>
