<template>
  <el-container class="app-container">
    <!-- 顶部标题栏 -->
    <el-header class="app-header">
      <span class="app-title">AIR Memory 管理界面</span>
      <span v-if="appVersion" class="app-version">v{{ appVersion }}</span>
    </el-header>
    <el-container class="app-body">
      <!-- 侧边导航栏 -->
      <el-aside width="200px" class="app-aside">
        <el-menu
          :default-active="$route.path"
          router
          class="app-menu"
        >
          <el-menu-item index="/">
            <el-icon><House /></el-icon>
            <span>控制台</span>
          </el-menu-item>
          <el-menu-item index="/memories">
            <el-icon><DataLine /></el-icon>
            <span>记忆管理</span>
          </el-menu-item>
          <el-menu-item index="/logs">
            <el-icon><Document /></el-icon>
            <span>操作日志</span>
          </el-menu-item>
          <el-menu-item index="/feedback">
            <el-icon><Star /></el-icon>
            <span>反馈记录</span>
          </el-menu-item>
        </el-menu>
      </el-aside>
      <!-- 主内容区 -->
      <el-main class="app-main">
        <RouterView />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { House, DataLine, Document, Star } from '@element-plus/icons-vue'
import { getVersion } from './api/index'

const appVersion = ref<string>('')

onMounted(async () => {
  try {
    const data = await getVersion()
    appVersion.value = data.version
  } catch {
    // 版本号获取失败时静默处理，不影响主功能
  }
})
</script>

<style scoped>
.app-container {
  min-height: 100vh;
}

.app-header {
  background-color: #409eff;
  display: flex;
  align-items: center;
  padding: 0 20px;
}

.app-title {
  color: #ffffff;
  font-size: 1.2rem;
  font-weight: bold;
}

.app-version {
  color: rgba(255, 255, 255, 0.75);
  font-size: 0.8rem;
  margin-left: 10px;
}

.app-body {
  flex: 1;
}

.app-aside {
  background-color: #ffffff;
  border-right: 1px solid #e4e7ed;
  min-height: calc(100vh - 60px);
}

.app-menu {
  border-right: none;
  height: 100%;
}

.app-main {
  background-color: #f5f7fa;
  padding: 0;
}
</style>
