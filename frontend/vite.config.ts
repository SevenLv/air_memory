// https://vitejs.dev/config/
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
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
