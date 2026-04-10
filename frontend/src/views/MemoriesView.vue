<template>
  <div class="memories-view">
    <el-card class="search-card">
      <template #header>
        <span class="card-title">记忆查询</span>
      </template>
      <el-form :model="form" inline @submit.prevent="handleSearch">
        <el-form-item label="查询文本">
          <el-input
            v-model="form.query"
            placeholder="请输入查询内容"
            clearable
            style="width: 320px"
          />
        </el-form-item>
        <el-form-item label="返回条数">
          <el-input-number v-model="form.topK" :min="1" :max="100" />
        </el-form-item>
        <el-form-item label="查询模式">
          <el-switch
            v-model="form.fastOnly"
            active-text="快速模式"
            inactive-text="深度模式"
            active-color="#67c23a"
            inactive-color="#409eff"
          />
        </el-form-item>
        <el-form-item>
          <el-button
            type="primary"
            :loading="memoryStore.loading"
            native-type="submit"
            :icon="Search"
          >
            查询
          </el-button>
        </el-form-item>
      </el-form>
      <div v-if="hasSearched" class="search-meta">
        <el-tag size="small" type="success">
          共找到 {{ memoryStore.count }} 条记忆
        </el-tag>
        <el-tag size="small" :type="memoryStore.queryMode === 'fast' ? 'warning' : 'primary'">
          {{ memoryStore.queryMode === 'fast' ? '快速模式（仅热层）' : '深度模式（热层 + 冷层）' }}
        </el-tag>
      </div>
    </el-card>

    <div v-if="memoryStore.loading" class="loading-tip">
      <el-skeleton :rows="3" animated />
    </div>

    <div v-else-if="hasSearched && memoryStore.memories.length === 0" class="empty-tip">
      <el-empty description="未找到相关记忆" />
    </div>

    <div v-else class="memory-list">
      <MemoryCard
        v-for="memory in memoryStore.memories"
        :key="memory.id"
        :memory="memory"
        @delete="handleDelete"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import { useMemoryStore } from '../stores/memory'
import MemoryCard from '../components/MemoryCard.vue'

const memoryStore = useMemoryStore()

const form = reactive({
  query: '',
  topK: 5,
  fastOnly: false,
})

const hasSearched = ref(false)

/** 执行查询 */
async function handleSearch(): Promise<void> {
  if (!form.query.trim()) {
    ElMessage.warning('请输入查询文本')
    return
  }
  hasSearched.value = true
  await memoryStore.fetchMemories(form.query.trim(), form.topK, form.fastOnly)
}

/** 删除记忆 */
async function handleDelete(memoryId: string): Promise<void> {
  await memoryStore.removeMemory(memoryId)
  ElMessage.success('记忆已删除')
}
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
</style>
