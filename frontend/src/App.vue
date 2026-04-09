<template>
  <el-container class="app-container">
    <el-header class="app-header">
      <span class="app-title">AIR Memory</span>
    </el-header>
    <el-main class="app-main">
      <RouterView />
    </el-main>
  </el-container>
</template>

<script setup lang="ts">
// Root application component
</script>

<style scoped>
.app-container {
  min-height: 100vh;
}

.app-header {
  background-color: #409eff;
  display: flex;
  align-items: center;
}

.app-title {
  color: #ffffff;
  font-size: 1.25rem;
  font-weight: bold;
}

.app-main {
  background-color: #f5f7fa;
}
</style>
