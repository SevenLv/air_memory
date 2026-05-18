<template>
  <div class="inputs-view">
    <el-card class="query-card">
      <template #header>
        <span class="card-title">输入信息管理</span>
      </template>
      <el-form :model="form" inline @submit.prevent="handleSearch">
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
          <el-button type="primary" :loading="loading" :icon="Search" native-type="submit">查询</el-button>
          <el-button :icon="Refresh" @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card>
      <template #header>
        <div class="table-header">
          <span class="card-title">输入信息列表</span>
          <el-tag v-if="total > 0" type="info">共 {{ total }} 条</el-tag>
        </div>
      </template>
      <el-table :data="inputs" :loading="loading" @row-click="handleRowClick">
        <el-table-column prop="input_id" label="输入 ID" min-width="320" show-overflow-tooltip />
        <el-table-column prop="query" label="查询内容" min-width="320" show-overflow-tooltip />
        <el-table-column label="创建时间" width="200">
          <template #default="{ row }">
            {{ formatLocalTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" align="center">
          <template #default="{ row }">
            <el-button type="primary" link @click.stop="handleRowClick(row)">查看详情</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div v-if="total > 0" class="pagination-wrapper">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="total"
          layout="total, sizes, prev, pager, next"
          @current-change="handlePageChange"
          @size-change="handlePageSizeChange"
        />
      </div>
      <el-empty v-if="!loading && inputs.length === 0" description="暂无输入信息" />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Search, Refresh } from '@element-plus/icons-vue'
import { getInputs } from '../api'
import type { InputInfo } from '../api/types'
import { formatLocalTime } from '../utils/time'

const router = useRouter()
const loading = ref(false)
const inputs = ref<InputInfo[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)

const form = reactive({
  dateRange: null as [string, string] | null,
})

async function fetchInputs(): Promise<void> {
  loading.value = true
  try {
    const res = await getInputs({
      page: currentPage.value,
      pageSize: pageSize.value,
      startTime: form.dateRange?.[0],
      endTime: form.dateRange?.[1],
    })
    inputs.value = res.inputs
    total.value = res.total
  } catch {
    inputs.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

async function handleSearch(): Promise<void> {
  currentPage.value = 1
  await fetchInputs()
}

async function handlePageChange(page: number): Promise<void> {
  currentPage.value = page
  await fetchInputs()
}

async function handlePageSizeChange(size: number): Promise<void> {
  pageSize.value = size
  currentPage.value = 1
  await fetchInputs()
}

async function handleReset(): Promise<void> {
  form.dateRange = null
  currentPage.value = 1
  pageSize.value = 20
  await fetchInputs()
}

function handleRowClick(row: InputInfo): void {
  const inputState = { ...row }
  router.push({
    name: 'input-detail',
    params: { inputId: row.input_id },
    state: { input: inputState },
  })
}

onMounted(() => {
  fetchInputs()
})
</script>

<style scoped>
.inputs-view {
  padding: 24px;
}

.query-card {
  margin-bottom: 20px;
}

.card-title {
  font-size: 1rem;
  font-weight: 600;
}

.table-header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.pagination-wrapper {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
</style>
