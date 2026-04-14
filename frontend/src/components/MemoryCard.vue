<template>
  <el-card class="memory-card" shadow="hover">
    <div class="memory-card__header">
      <el-tag :type="tierTagType" size="small">{{ tierLabel }}</el-tag>
      <el-tag type="info" size="small">
        相似度: {{ (memory.similarity * 100).toFixed(1) }}%
      </el-tag>
      <el-tag type="warning" size="small">
        价值评分: {{ memory.value_score.toFixed(2) }}
      </el-tag>
      <span class="memory-card__spacer" />
      <el-popconfirm
        title="确认删除该记忆？此操作不可恢复。"
        confirm-button-text="删除"
        cancel-button-text="取消"
        confirm-button-type="danger"
        @confirm="emit('delete', memory.id)"
      >
        <template #reference>
          <el-button type="danger" size="small" :icon="Delete" circle />
        </template>
      </el-popconfirm>
    </div>
    <div class="memory-card__content">{{ memory.content }}</div>
    <div class="memory-card__footer">
      <span class="memory-card__meta">ID: {{ memory.id }}</span>
      <span class="memory-card__meta">创建时间: {{ formatLocalTime(memory.created_at) }}</span>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Delete } from '@element-plus/icons-vue'
import { formatLocalTime } from '../utils/time'
import type { Memory } from '../api/types'
import { formatLocalTime } from '../utils/time'

const props = defineProps<{ memory: Memory }>()

const emit = defineEmits<{
  (e: 'delete', id: string): void
}>()

/** 根据层级返回标签颜色类型 */
const tierTagType = computed(() =>
  props.memory.tier === 'hot' ? ('danger' as const) : ('info' as const),
)

/** 层级中文标签 */
const tierLabel = computed(() => (props.memory.tier === 'hot' ? '热层' : '冷层'))
</script>

<style scoped>
.memory-card {
  margin-bottom: 12px;
}

.memory-card__header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
  flex-wrap: wrap;
}

.memory-card__spacer {
  flex: 1;
}

.memory-card__content {
  font-size: 0.95rem;
  line-height: 1.6;
  color: #303133;
  margin-bottom: 10px;
  white-space: pre-wrap;
  word-break: break-word;
}

.memory-card__footer {
  display: flex;
  gap: 16px;
  font-size: 0.78rem;
  color: #909399;
  flex-wrap: wrap;
}
</style>
