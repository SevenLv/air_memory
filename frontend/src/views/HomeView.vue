<template>
  <div class="home-view">
    <!-- 欢迎卡片 -->
    <el-card class="welcome-card">
      <template #header>
        <span>AIR Memory 管理控制台</span>
      </template>
      <p class="welcome-text">欢迎使用 AIR Memory 记忆管理系统</p>
      <p class="welcome-desc">本系统为 AI Agent 提供高效的记忆存储与查询服务，支持分级存储（热层/冷层）和价值评分驱动的智能迁移。</p>
    </el-card>

    <!-- 分级存储统计面板 -->
    <div class="stats-section">
      <div class="stats-header">
        <span class="stats-title">分级存储统计</span>
        <el-button
          size="small"
          :icon="Refresh"
          :loading="statsLoading"
          @click="loadStats"
        >
          刷新
        </el-button>
      </div>

      <el-row :gutter="16">
        <!-- 热层记忆数量 -->
        <el-col :span="6">
          <el-card class="stat-card stat-card--hot" shadow="hover">
            <div class="stat-card__value">{{ tierStats?.hot_count ?? '-' }}</div>
            <div class="stat-card__label">热层记忆数量</div>
          </el-card>
        </el-col>
        <!-- 冷层记忆数量 -->
        <el-col :span="6">
          <el-card class="stat-card stat-card--cold" shadow="hover">
            <div class="stat-card__value">{{ tierStats?.cold_count ?? '-' }}</div>
            <div class="stat-card__label">冷层记忆数量</div>
          </el-card>
        </el-col>
        <!-- 内存占用 -->
        <el-col :span="6">
          <el-card class="stat-card stat-card--memory" shadow="hover">
            <div class="stat-card__value">
              {{ tierStats ? `${tierStats.hot_memory_mb} MB` : '-' }}
            </div>
            <div class="stat-card__label">
              热层内存占用
              <span v-if="tierStats" class="stat-card__sub">
                / {{ tierStats.memory_budget_mb }} MB 上限
              </span>
            </div>
            <el-progress
              v-if="tierStats"
              :percentage="memoryUsagePercent"
              :color="memoryProgressColor"
              :stroke-width="6"
              style="margin-top: 8px"
            />
          </el-card>
        </el-col>
        <!-- 磁盘占用 -->
        <el-col :span="6">
          <el-card class="stat-card stat-card--disk" shadow="hover">
            <div class="stat-card__value">
              {{ diskStats ? `${diskStats.disk_used_gb} GB` : '-' }}
            </div>
            <div class="stat-card__label">
              冷层磁盘占用
              <span v-if="diskStats" class="stat-card__sub">
                / {{ diskStats.disk_budget_gb }} GB 上限
              </span>
            </div>
            <el-progress
              v-if="diskStats"
              :percentage="diskUsagePercent"
              :color="diskProgressColor"
              :stroke-width="6"
              style="margin-top: 8px"
            />
          </el-card>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Refresh } from '@element-plus/icons-vue'
import { getTierStats, getDiskStats } from '../api'
import type { TierStats, DiskStats } from '../api/types'

const tierStats = ref<TierStats | null>(null)
const diskStats = ref<DiskStats | null>(null)
const statsLoading = ref(false)

/** 内存使用率百分比 */
const memoryUsagePercent = computed(() => {
  if (!tierStats.value) return 0
  const pct = (tierStats.value.hot_memory_mb / tierStats.value.memory_budget_mb) * 100
  return Math.min(Math.round(pct), 100)
})

/** 磁盘使用率百分比 */
const diskUsagePercent = computed(() => {
  if (!diskStats.value) return 0
  const pct = (diskStats.value.disk_used_gb / diskStats.value.disk_budget_gb) * 100
  return Math.min(Math.round(pct), 100)
})

/** 内存进度条颜色 */
const memoryProgressColor = computed(() => {
  if (memoryUsagePercent.value >= 90) return '#f56c6c'
  if (memoryUsagePercent.value >= 70) return '#e6a23c'
  return '#67c23a'
})

/** 磁盘进度条颜色 */
const diskProgressColor = computed(() => {
  if (diskUsagePercent.value >= 90) return '#f56c6c'
  if (diskUsagePercent.value >= 70) return '#e6a23c'
  return '#67c23a'
})

/** 加载统计数据 */
async function loadStats(): Promise<void> {
  statsLoading.value = true
  try {
    const [ts, ds] = await Promise.all([getTierStats(), getDiskStats()])
    tierStats.value = ts
    diskStats.value = ds
  } catch {
    // 错误已由 axios 拦截器统一提示
  } finally {
    statsLoading.value = false
  }
}

onMounted(() => {
  loadStats()
})
</script>

<style scoped>
.home-view {
  padding: 24px;
}

.welcome-card {
  margin-bottom: 24px;
  max-width: 800px;
}

.welcome-text {
  font-size: 1.1rem;
  font-weight: 500;
  margin-bottom: 8px;
}

.welcome-desc {
  color: #606266;
  line-height: 1.6;
}

.stats-section {
  margin-top: 4px;
}

.stats-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.stats-title {
  font-size: 1rem;
  font-weight: 600;
  color: #303133;
}

.stat-card {
  text-align: center;
  padding: 8px 0;
}

.stat-card--hot :deep(.el-card__body) {
  background: linear-gradient(135deg, #fff1f0 0%, #fff 100%);
}

.stat-card--cold :deep(.el-card__body) {
  background: linear-gradient(135deg, #e8f4ff 0%, #fff 100%);
}

.stat-card--memory :deep(.el-card__body) {
  background: linear-gradient(135deg, #f0fff4 0%, #fff 100%);
}

.stat-card--disk :deep(.el-card__body) {
  background: linear-gradient(135deg, #fffbf0 0%, #fff 100%);
}

.stat-card__value {
  font-size: 2rem;
  font-weight: 700;
  color: #303133;
  margin-bottom: 4px;
}

.stat-card__label {
  font-size: 0.85rem;
  color: #606266;
}

.stat-card__sub {
  color: #909399;
  font-size: 0.78rem;
}
</style>

