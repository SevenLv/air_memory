// https://vitejs.dev/config/
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  // base 默认为 '/'，生产构建使用相对路径，与 FastAPI StaticFiles 挂载兼容
  server: {
    // 开发模式代理：将 /api/v1 请求转发到后端服务（仅开发模式生效，不影响生产构建）
    proxy: {
      '/api': {
        target: 'http://localhost:8080',
        changeOrigin: true,
      },
    },
  },
  test: {
    // Vitest 测试环境配置
    environment: 'jsdom',
    include: ['tests/**/*.spec.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      include: ['src/**/*.{ts,vue}'],
      exclude: [
        'src/main.ts',
        'src/api/types.ts',      // TypeScript 接口定义，无可执行语句
        'src/router/index.ts',   // 路由配置，集成测试覆盖
        'src/App.vue',           // 应用根组件，集成测试覆盖
        'src/stores/index.ts',   // 仅 re-export，无业务逻辑
      ],
    },
  },
})
