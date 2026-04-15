<template>
  <div class="memories-view">
    <el-card class="query-card">
      <template #header>
        <span class="card-title">记忆管理查询</span>
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
          <el-button type="primary" :loading="loading" native-type="submit" :icon="Search">
            查询
          </el-button>
          <el-button :icon="Refresh" @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="list-card">
      <template #header>
        <div class="list-header">
          <span class="card-title">最近记忆列表</span>
          <el-tag type="info">共 {{ total }} 条</el-tag>
        </div>
      </template>

      <el-table
        :data="items"
        v-loading="loading"
        border
        stripe
        style="width: 100%"
        empty-text="暂无记忆数据"
        @row-click="goDetail"
      >
        <el-table-column prop="id" label="日志 ID" width="90" align="center" />
        <el-table-column label="提交时间" width="200">
          <template #default="{ row }">
            {{ formatLocalTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="memory_id" label="记忆 ID" min-width="220" show-overflow-tooltip />
        <el-table-column label="原始数据" min-width="220" show-overflow-tooltip>
          <template #default="{ row }">
            {{ row.content }}
          </template>
        </el-table-column>
        <el-table-column label="价值评分" width="120" align="center">
          <template #default="{ row }">
            {{ Number(row.value_score).toFixed(4) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="110" align="center">
          <template #default="{ row }">
            <el-button type="primary" link @click.stop="goDetail(row)">查看详情</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div v-if="total > 0" class="pagination-wrapper">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[20, 50, 100]"
          :total="total"
          layout="total, sizes, prev, pager, next"
          @size-change="handlePageSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Search, Refresh } from '@element-plus/icons-vue'
import { getMemoryManageList } from '../api'
import type { MemoryManageItem } from '../api/types'
import { formatLocalTime } from '../utils/time'

const form = reactive({
  memoryId: '',
  dateRange: null as [string, string] | null,
})

const router = useRouter()
const loading = ref(false)
const items = ref<MemoryManageItem[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)

async function handleSearch(): Promise<void> {
  currentPage.value = 1
  await fetchList()
}

function handleReset(): void {
  form.memoryId = ''
  form.dateRange = null
  currentPage.value = 1
  pageSize.value = 20
  fetchList()
}

async function handlePageChange(page: number): Promise<void> {
  currentPage.value = page
  await fetchList()
}

async function handlePageSizeChange(size: number): Promise<void> {
  pageSize.value = size
  currentPage.value = 1
  await fetchList()
}

function goDetail(row: MemoryManageItem): void {
  router.push(`/memories/${row.memory_id}`)
}

async function fetchList(): Promise<void> {
  loading.value = true
  try {
    const res = await getMemoryManageList({
      page: currentPage.value,
      pageSize: pageSize.value,
      memoryId: form.memoryId.trim() || undefined,
      startTime: form.dateRange?.[0] || undefined,
      endTime: form.dateRange?.[1] || undefined,
    })
    items.value = res.logs
    total.value = res.total
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchList()
})
</script>

<style scoped>
.memories-view {
  padding: 24px;
}

.query-card {
  margin-bottom: 20px;
}

.card-title {
  font-size: 1rem;
  font-weight: 600;
}

.list-card {
  margin-bottom: 20px;
}

.list-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.pagination-wrapper {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
</style>
