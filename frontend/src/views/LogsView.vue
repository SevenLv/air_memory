<template>
  <div class="logs-view">
    <el-tabs v-model="activeTab" type="card" @tab-change="handleTabChange">
      <!-- 存储操作日志 -->
      <el-tab-pane label="存储操作日志" name="save">
        <div class="tab-toolbar">
          <el-button
            type="primary"
            :icon="Refresh"
            :loading="logStore.saveLoading"
            @click="logStore.fetchSaveLogs()"
          >
            刷新
          </el-button>
          <el-tag type="info">共 {{ logStore.saveLogs.length }} 条</el-tag>
        </div>
        <LogTable :data="logStore.saveLogs" :loading="logStore.saveLoading">
          <el-table-column prop="id" label="ID" width="70" align="center" />
          <el-table-column prop="created_at" label="时间" width="200" />
          <el-table-column prop="memory_id" label="记忆 ID" width="240" show-overflow-tooltip />
          <el-table-column label="原始内容" min-width="200" show-overflow-tooltip>
            <template #default="{ row }">
              <span v-if="isGarbled(row.content)">
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
      </el-tab-pane>

      <!-- 查询操作日志 -->
      <el-tab-pane label="查询操作日志" name="query">
        <div class="tab-toolbar">
          <el-button
            type="primary"
            :icon="Refresh"
            :loading="logStore.queryLoading"
            @click="logStore.fetchQueryLogs()"
          >
            刷新
          </el-button>
          <el-tag type="info">共 {{ logStore.queryLogs.length }} 条</el-tag>
        </div>
        <LogTable :data="logStore.queryLogs" :loading="logStore.queryLoading">
          <el-table-column prop="id" label="ID" width="70" align="center" />
          <el-table-column prop="created_at" label="时间" width="200" />
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
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Refresh } from '@element-plus/icons-vue'
import { useLogStore } from '../stores/log'
import LogTable from '../components/LogTable.vue'

const logStore = useLogStore()
const activeTab = ref('save')

/** 解析查询结果摘要：results 字段存储 JSON 字符串，展示结果数量 */
function parseResultsSummary(results: string): string {
  try {
    const parsed = JSON.parse(results) as unknown[]
    return `${parsed.length} 条结果`
  } catch (e) {
    console.error('解析查询结果 JSON 失败:', e)
    return '（结果解析失败）'
  }
}

/** 检测内容是否疑似乱码（主要特征：含有非 ASCII 字符时问号占比 > 30%） */
function isGarbled(content: string): boolean {
  if (!content || content.length === 0) return false
  // 纯 ASCII 内容不视为乱码
  const hasNonAscii = [...content].some((c) => c.charCodeAt(0) > 127)
  if (!hasNonAscii) return false
  const questionCount = (content.match(/\?/g) ?? []).length
  return questionCount / content.length > 0.3
}

/** 切换标签时按需加载数据 */
function handleTabChange(tab: string): void {
  if (tab === 'save' && logStore.saveLogs.length === 0) {
    logStore.fetchSaveLogs()
  } else if (tab === 'query' && logStore.queryLogs.length === 0) {
    logStore.fetchQueryLogs()
  }
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
</style>
