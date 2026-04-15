<template>
  <div class="logs-view">
    <el-tabs v-model="activeTab" type="card" @tab-change="handleTabChange">
      <!-- 存储操作日志 -->
      <el-tab-pane label="存储操作日志" name="save">
        <div class="tab-toolbar">
          <el-form inline @submit.prevent="handleSaveSearch">
            <el-form-item label="时间范围">
              <el-date-picker
                v-model="saveForm.dateRange"
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
                :loading="logStore.saveLoading"
                :icon="Search"
                native-type="submit"
              >
                查询
              </el-button>
              <el-button :icon="Refresh" @click="handleSaveReset">重置</el-button>
              <el-button
                type="primary"
                plain
                :icon="Refresh"
                :loading="logStore.saveLoading"
                @click="logStore.fetchSaveLogs()"
              >
                刷新
              </el-button>
            </el-form-item>
          </el-form>
          <el-tag type="info">共 {{ filteredSaveLogs.length }} 条</el-tag>
        </div>
        <LogTable :data="pagedSaveLogs" :loading="logStore.saveLoading">
          <el-table-column prop="id" label="ID" width="70" align="center" />
          <el-table-column label="时间" width="200">
            <template #default="{ row }">
              {{ formatLocalTime(row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column prop="memory_id" label="记忆 ID" width="240" show-overflow-tooltip />
          <el-table-column label="原始内容" min-width="200" show-overflow-tooltip>
            <template #default="{ row }">
              <span v-if="isGarbled(row)">
                <el-tooltip
                  content="此记录内容疑似因编码问题损坏（历史遗留），新版本新增的记忆不受影响"
                  placement="top"
                >
                  <el-tag type="warning" size="small" style="margin-right: 6px;">乱码</el-tag>
                </el-tooltip>
                <span class="garbled-text">{{ row.content }}</span>
              </span>
              <span v-else>{{ row.content }}</span>
            </template>
          </el-table-column>
          <el-table-column label="状态" width="100" align="center">
            <template #default="{ row }">
              <el-tag :type="row.memory_deleted ? 'info' : 'success'" size="small">
                {{ row.memory_deleted ? '已删除' : '存在' }}
              </el-tag>
            </template>
          </el-table-column>
        </LogTable>
        <div v-if="filteredSaveLogs.length > 0" class="pagination-wrapper">
          <el-pagination
            v-model:current-page="saveCurrentPage"
            v-model:page-size="savePageSize"
            :page-sizes="[10, 20, 50, 100]"
            :total="filteredSaveLogs.length"
            layout="total, sizes, prev, pager, next"
            @size-change="handleSavePageSizeChange"
            @current-change="handleSavePageChange"
          />
        </div>
      </el-tab-pane>

      <!-- 查询操作日志 -->
      <el-tab-pane label="查询操作日志" name="query">
        <div class="tab-toolbar">
          <el-form inline @submit.prevent="handleQuerySearch">
            <el-form-item label="时间范围">
              <el-date-picker
                v-model="queryForm.dateRange"
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
                :loading="logStore.queryLoading"
                :icon="Search"
                native-type="submit"
              >
                查询
              </el-button>
              <el-button :icon="Refresh" @click="handleQueryReset">重置</el-button>
              <el-button
                type="primary"
                plain
                :icon="Refresh"
                :loading="logStore.queryLoading"
                @click="logStore.fetchQueryLogs()"
              >
                刷新
              </el-button>
            </el-form-item>
          </el-form>
          <el-tag type="info">共 {{ filteredQueryLogs.length }} 条</el-tag>
        </div>
        <LogTable :data="pagedQueryLogs" :loading="logStore.queryLoading">
          <el-table-column prop="id" label="ID" width="70" align="center" />
          <el-table-column label="时间" width="200">
            <template #default="{ row }">
              {{ formatLocalTime(row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column prop="query" label="查询条件" show-overflow-tooltip />
          <el-table-column label="查询模式" width="120" align="center">
            <template #default="{ row }">
              <el-tag :type="row.fast_only ? 'warning' : 'primary'" size="small">
                {{ row.fast_only ? '快速模式' : '深度模式' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="结果摘要" show-overflow-tooltip>
            <template #default="{ row }">
              <span class="results-summary">{{ parseResultsSummary(row.results) }}</span>
            </template>
          </el-table-column>
        </LogTable>
        <div v-if="filteredQueryLogs.length > 0" class="pagination-wrapper">
          <el-pagination
            v-model:current-page="queryCurrentPage"
            v-model:page-size="queryPageSize"
            :page-sizes="[10, 20, 50, 100]"
            :total="filteredQueryLogs.length"
            layout="total, sizes, prev, pager, next"
            @size-change="handleQueryPageSizeChange"
            @current-change="handleQueryPageChange"
          />
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref, onMounted } from 'vue'
import { Search, Refresh } from '@element-plus/icons-vue'
import { useLogStore } from '../stores/log'
import { formatLocalTime } from '../utils/time'
import LogTable from '../components/LogTable.vue'
import type { SaveLog } from '../api/types'

const logStore = useLogStore()
const activeTab = ref('save')
const saveForm = reactive({
  dateRange: null as [string, string] | null,
})
const queryForm = reactive({
  dateRange: null as [string, string] | null,
})
const saveCurrentPage = ref(1)
const queryCurrentPage = ref(1)
const savePageSize = ref(20)
const queryPageSize = ref(20)

function parseTimestamp(value: string): number {
  const ts = Date.parse(value)
  return Number.isNaN(ts) ? 0 : ts
}

function isInRange(createdAt: string, dateRange: [string, string] | null): boolean {
  if (!dateRange) {
    return true
  }
  const createdAtTs = parseTimestamp(createdAt)
  const startTs = parseTimestamp(dateRange[0])
  const endTs = parseTimestamp(dateRange[1])
  return createdAtTs >= startTs && createdAtTs <= endTs
}

const filteredSaveLogs = computed(() =>
  logStore.saveLogs.filter((log) => isInRange(log.created_at, saveForm.dateRange)),
)

const filteredQueryLogs = computed(() =>
  logStore.queryLogs.filter((log) => isInRange(log.created_at, queryForm.dateRange)),
)

const pagedSaveLogs = computed(() => {
  const start = (saveCurrentPage.value - 1) * savePageSize.value
  return filteredSaveLogs.value.slice(start, start + savePageSize.value)
})

const pagedQueryLogs = computed(() => {
  const start = (queryCurrentPage.value - 1) * queryPageSize.value
  return filteredQueryLogs.value.slice(start, start + queryPageSize.value)
})

/** 解析查询结果摘要：results 字段存储 JSON 字符串，展示结果数量 */
function parseResultsSummary(results: unknown): string {
  if (typeof results !== 'string' || results.length === 0) {
    return '--'
  }
  try {
    const parsed = JSON.parse(results) as unknown[]
    return `${parsed.length} 条结果`
  } catch (e) {
    console.error('解析查询结果 JSON 失败:', e)
    return '（结果解析失败）'
  }
}

/** 判断存储日志内容是否疑似乱码
 * 优先使用服务端计算的 is_garbled 字段（v1.2.5+），兜底使用客户端检测 */
function isGarbled(row: SaveLog): boolean {
  // 优先信任服务端权威结果
  if (typeof row.is_garbled === 'boolean') {
    return row.is_garbled
  }
  // 兜底：客户端检测（兼容旧版 API）
  const content = row.content
  if (!content || content.length === 0) return false
  const questionCount = (content.match(/\?/g) ?? []).length
  const questionRatio = questionCount / content.length
  // 场景一：纯 ASCII 问号（CP1252 损坏）
  const hasNonAscii = [...content].some((c) => c.charCodeAt(0) > 127)
  if (!hasNonAscii && questionRatio > 0.5 && content.length >= 2) return true
  // 场景二：混合乱码
  if (hasNonAscii && questionRatio > 0.3) return true
  return false
}

/** 切换标签时按需加载数据 */
function handleTabChange(tab: string): void {
  if (tab === 'save' && logStore.saveLogs.length === 0) {
    logStore.fetchSaveLogs()
  } else if (tab === 'query' && logStore.queryLogs.length === 0) {
    logStore.fetchQueryLogs()
  }
}

function handleSaveSearch(): void {
  saveCurrentPage.value = 1
}

function handleSaveReset(): void {
  saveForm.dateRange = null
  saveCurrentPage.value = 1
}

function handleSavePageChange(page: number): void {
  saveCurrentPage.value = page
}

function handleSavePageSizeChange(pageSize: number): void {
  savePageSize.value = pageSize
  saveCurrentPage.value = 1
}

function handleQuerySearch(): void {
  queryCurrentPage.value = 1
}

function handleQueryReset(): void {
  queryForm.dateRange = null
  queryCurrentPage.value = 1
}

function handleQueryPageChange(page: number): void {
  queryCurrentPage.value = page
}

function handleQueryPageSizeChange(pageSize: number): void {
  queryPageSize.value = pageSize
  queryCurrentPage.value = 1
}

onMounted(() => {
  logStore.fetchSaveLogs()
})
</script>

<style scoped>
.logs-view {
  padding: 24px;
}

.tab-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
}

.results-summary {
  color: #606266;
}

.garbled-text {
  color: #909399;
  font-style: italic;
}

.pagination-wrapper {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
</style>
