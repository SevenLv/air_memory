<template>
  <div class="home-view">
    <el-card class="welcome-card">
      <template #header>
        <span>AIR Memory</span>
      </template>
      <p class="welcome-text">欢迎使用 AIR Memory 记忆管理系统</p>
      <p class="welcome-desc">本系统为 AI Agent 提供高效的记忆存储与查询服务。</p>
    </el-card>
  </div>
</template>

<script setup lang="ts">
// HomeView - 记忆查询页面占位
</script>

<style scoped>
.home-view {
  padding: 24px;
}

.welcome-card {
  max-width: 600px;
  margin: 0 auto;
}

.welcome-text {
  font-size: 1.1rem;
  font-weight: 500;
  margin-bottom: 8px;
}

.welcome-desc {
  color: #606266;
}
</style>
