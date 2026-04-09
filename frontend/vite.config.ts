// https://vitejs.dev/config/
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  test: {
    // Vitest test environment
    environment: 'jsdom',
    include: ['tests/**/*.spec.ts'],
  },
})
