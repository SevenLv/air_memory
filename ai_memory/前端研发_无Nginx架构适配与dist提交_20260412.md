# 前端研发 - 无 Nginx 架构适配与 dist 提交

## 标签

前端, Mia, Vite, 架构适配, 静态文件, dist, server.proxy, gitignore, 无 Nginx, FastAPI, 同源

## 任务概述

系统架构从 Docker 部署改为 Python 本机直接运行，FastAPI 统一在端口 8080 提供 API 和前端静态文件。需适配前端配置并将构建产物纳入版本控制。

## 关键结论

- `frontend/src/api/index.ts` 中 `baseURL: '/api/v1'` 已是相对路径，与同源架构天然兼容，**无需修改**
- `vite.config.ts` 中 `base` 未设置（默认 `/`），生产构建路径正确，**无需修改**
- 需要添加 `server.proxy` 开发代理（仅开发模式），将 `/api` 转发到 `http://localhost:8080`
- `frontend/.gitignore` 需注释掉 `dist/`，使构建产物可被 git 追踪
- 构建产物提交后，用户可直接运行 FastAPI，无需安装 Node.js

## 变更文件清单

| 文件 | 变更内容 |
| --- | --- |
| `frontend/vite.config.ts` | 新增 `server.proxy` 配置，开发模式将 `/api` 代理到 `http://localhost:8080` |
| `frontend/.gitignore` | 注释掉 `dist/` 排除规则 |
| `frontend/dist/index.html` | 构建产物 - HTML 入口（0.40 kB） |
| `frontend/dist/assets/index-*.css` | 构建产物 - Element Plus + 自定义样式（355.49 kB） |
| `frontend/dist/assets/index-*.js` | 构建产物 - 主 JS 包（1,069.04 kB） |

## 最短路径（快速复现）

1. `frontend/vite.config.ts`：在 `plugins` 后添加 `server.proxy` 配置（见下方代码）
2. `frontend/.gitignore`：将 `dist/` 改为注释
3. `cd frontend && npm ci && npm run test`（确认 77 个测试通过）
4. `npm run build`（TypeScript 类型检查 + Vite 生产构建）
5. `git add frontend/.gitignore frontend/vite.config.ts frontend/dist/`
6. `git commit`

## server.proxy 配置模板

```typescript
server: {
  // 开发模式代理：将 /api/v1 请求转发到后端服务（仅开发模式生效，不影响生产构建）
  proxy: {
    '/api': {
      target: 'http://localhost:8080',
      changeOrigin: true,
    },
  },
},
```

## 测试结果

- 77 个前端单元测试全部通过（7 个测试文件）
- TypeScript 类型检查通过（vue-tsc --noEmit）
- Vite 生产构建成功（8.19s）
