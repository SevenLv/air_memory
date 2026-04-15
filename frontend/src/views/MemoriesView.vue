<template>
  <div class="memories-view">
    <el-card class="search-card">
      <template #header>
        <span class="card-title">记忆管理</span>
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
      <div class="search-meta">
        <el-tag size="small" type="success">
          共 {{ filteredLogs.length }} 条记忆
        </el-tag>
      </div>
    </el-card>

    <div v-if="loading" class="loading-tip">
      <el-skeleton :rows="3" animated />
    </div>

    <div v-else-if="filteredLogs.length === 0" class="empty-tip">
      <el-empty description="未找到相关记忆" />
    </div>

    <div v-else class="memory-list">
        <el-table :data="pagedLogs" @row-click="handleRowClick">
          <el-table-column prop="memory_id" label="记忆 ID" min-width="280" show-overflow-tooltip />
          <el-table-column label="原始数据" min-width="320" show-overflow-tooltip>
            <template #default="{ row }">
              {{ row.content }}
            </template>
          </el-table-column>
          <el-table-column label="评价值" width="100" align="center">
            <template #default="{ row }">
              {{ formatValueScore(row.value_score) }}
            </template>
          </el-table-column>
          <el-table-column label="提交时间" width="200">
            <template #default="{ row }">
              {{ formatLocalTime(row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="170" align="center">
            <template #default="{ row }">
              <el-button type="primary" link @click.stop="handleRowClick(row)">查看详情</el-button>
              <el-button type="danger" link @click.stop="handleDelete(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>

      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="currentPage"
          :page-size="pageSize"
          :total="filteredLogs.length"
          layout="total, prev, pager, next"
          @current-change="handlePageChange"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { Search, Refresh } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getSaveLogs, deleteMemory } from '../api'
import type { SaveLog } from '../api/types'
import { formatLocalTime } from '../utils/time'

const router = useRouter()

const form = reactive({
  memoryId: '',
  dateRange: null as [string, string] | null,
})

const loading = ref(false)
const allLogs = ref<SaveLog[]>([])
const currentPage = ref(1)
const pageSize = 20

const normalizedLogs = computed(() =>
  allLogs.value.map((log) => ({
    ...log,
    createdAtTs: Date.parse(log.created_at),
  })),
)

const filteredLogs = computed(() => {
  const memoryId = form.memoryId.trim().toLowerCase()
  const startTime = form.dateRange?.[0] ? new Date(form.dateRange[0]).getTime() : null
  const endTime = form.dateRange?.[1] ? new Date(form.dateRange[1]).getTime() : null

  return normalizedLogs.value.filter((log) => {
    if (log.memory_deleted) {
      return false
    }
    if (memoryId && !log.memory_id.toLowerCase().includes(memoryId)) {
      return false
    }
    if (startTime !== null && log.createdAtTs < startTime) {
      return false
    }
    if (endTime !== null && log.createdAtTs > endTime) {
      return false
    }
    return true
  })
})

const pagedLogs = computed(() => {
  const start = (currentPage.value - 1) * pageSize
  return filteredLogs.value.slice(start, start + pageSize)
})

async function fetchLogs(): Promise<void> {
  loading.value = true
  try {
    const data = await getSaveLogs()
    allLogs.value = data.logs
  } catch {
    allLogs.value = []
  } finally {
    loading.value = false
  }
}

function handleSearch(): void {
  currentPage.value = 1
}

function handleReset(): void {
  form.memoryId = ''
  form.dateRange = null
  currentPage.value = 1
}

function handlePageChange(page: number): void {
  currentPage.value = page
}

function handleRowClick(row: SaveLog): void {
  const memoryState = { ...row }
  router.push({
    path: `/memories/${encodeURIComponent(row.memory_id)}`,
    state: { memory: memoryState },
  })
}

function formatValueScore(valueScore: number | null | undefined): string {
  return typeof valueScore === 'number' ? valueScore.toFixed(2) : '--'
}

async function handleDelete(row: SaveLog): Promise<void> {
  try {
    await ElMessageBox.confirm('确定删除该记忆吗', '删除确认', {
      type: 'warning',
      confirmButtonText: '确认',
      cancelButtonText: '取消',
    })
  } catch {
    return
  }

  try {
    await deleteMemory(row.memory_id)
    allLogs.value = allLogs.value.filter((log) => log.memory_id !== row.memory_id)
    currentPage.value = 1
    ElMessage.success('删除成功')
  } catch {
    // 错误提示由 API 拦截器统一处理
  }
}

onMounted(() => {
  fetchLogs()
})
</script>

<style scoped>
.memories-view {
  padding: 24px;
}

.search-card {
  margin-bottom: 20px;
}

.card-title {
  font-size: 1rem;
  font-weight: 600;
}

.search-meta {
  display: flex;
  gap: 8px;
  margin-top: 12px;
}

.loading-tip {
  padding: 16px 0;
}

.empty-tip {
  padding: 40px 0;
}

.memory-list {
  margin-top: 4px;
}

.pagination-wrapper {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
</style>
