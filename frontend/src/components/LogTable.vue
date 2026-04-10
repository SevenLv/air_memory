<template>
  <el-table
    :data="data"
    v-loading="loading"
    border
    stripe
    style="width: 100%"
    empty-text="暂无日志数据"
  >
    <slot />
  </el-table>
</template>

<script setup lang="ts">
defineProps<{
  /** 表格数据 */
  data: unknown[]
  /** 是否加载中 */
  loading?: boolean
}>()
</script>
