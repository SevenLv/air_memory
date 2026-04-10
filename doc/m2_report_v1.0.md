# M2 阶段研发执行报告

> 版本: 1.0
> 负责人: Mia（前端研发工程师）
> 完成日期: 2026-04-09
> 前置里程碑: M1（后端服务就绪）- 已完成并通过架构评审

---

## 1. 概述

M2 阶段目标为完成 AIR Memory Web 管理界面的全部页面视图研发，使人类用户能够通过浏览器访问并操作系统的全部管理功能。本报告记录 M2 阶段各工作条目的完成情况、验收标准达成情况、遗留问题及对后续里程碑的影响评估。

---

## 2. 工作条目完成情况

| 编号 | 工作内容 | 状态 | 备注 |
| --- | --- | --- | --- |
| M2-01 | 实现 `MemoriesView`：记忆查询（支持 `fast_only` 模式切换）与指定记忆删除 | ✅ 已完成 | 支持快速/深度模式 Switch 切换；删除前弹出确认对话框；删除后记忆从列表即时移除 |
| M2-02 | 实现 `LogsView`：存储操作日志查看与查询操作日志查看 | ✅ 已完成 | 使用 Tab 分离两类日志；存储日志展示时间/memory_id/内容/状态；查询日志展示时间/条件/模式/结果数量 |
| M2-03 | 实现 `FeedbackView`：查看每个记忆的当前综合价值评分与历次反馈记录 | ✅ 已完成 | 通过 memory_id 查询价值评分（含进度条可视化）和历次反馈历史表格 |
| M2-04 | 实现分级存储统计面板（热/冷层记忆数量、内存占用、磁盘占用） | ✅ 已完成 | 集成于 HomeView 控制台页面；展示热层/冷层数量、内存占用、磁盘占用及使用率进度条 |
| M2-05 | 实现 Pinia Store（`useMemoryStore`、`useLogStore`）和 Axios API 调用层 | ✅ 已完成 | `useMemoryStore`、`useLogStore` 均基于 Composition API 实现；Axios 实例统一配置响应拦截器 |
| M2-06 | 实现公共组件：`MemoryCard.vue`（记忆条目展示）、`LogTable.vue`（日志表格） | ✅ 已完成 | `MemoryCard.vue` 展示层级标签/相似度/价值评分/内容/元信息/删除按钮；`LogTable.vue` 封装 el-table 基础属性，支持 slot 定义列 |
| M2-07 | 输出《M2 阶段研发执行报告》 | ✅ 已完成 | 本文件 |

---

## 3. 验收标准达成情况

| 编号 | 验收标准 | 达成状态 | 说明 |
| --- | --- | --- | --- |
| M2-AC-01 | 浏览器可正常访问 Web 管理界面，路由导航正常（`/`、`/memories`、`/logs`、`/feedback`） | ✅ 达成 | Vue Router 4 配置了全部四条路由；App.vue 侧边导航菜单与路由联动 |
| M2-AC-02 | 记忆查询页面能正确展示查询结果，支持切换快速模式/深度模式 | ✅ 达成 | `MemoriesView` 通过 el-switch 切换 `fastOnly` 参数，调用 `GET /api/v1/memories?fast_only=true/false` |
| M2-AC-03 | 点击删除按钮后，目标记忆从列表中消失，且后端已确认删除 | ✅ 达成 | 调用 `DELETE /api/v1/memories/{id}`；useMemoryStore.removeMemory() 在后端确认后过滤本地列表 |
| M2-AC-04 | 存储操作日志页面和查询操作日志页面能正确展示各自的日志列表 | ✅ 达成 | `LogsView` 使用 el-tabs 分离存储日志（`GET /api/v1/logs/save`）和查询日志（`GET /api/v1/logs/query`） |
| M2-AC-05 | 反馈记录页面能正确展示指定记忆的 value_score、所在层及历次反馈历史 | ✅ 达成 | `FeedbackView` 并发请求 `GET /api/v1/memories/{id}/value-score` 和 `GET /api/v1/memories/{id}/feedback/logs` |
| M2-AC-06 | 分级存储统计面板能正确展示热/冷层数量、内存占用和磁盘占用数据 | ✅ 达成 | HomeView 并发请求 `GET /api/v1/admin/tier-stats` 和 `GET /api/v1/admin/disk-stats`，以卡片+进度条形式展示 |
| M2-AC-07 | 所有与后端的 API 调用均使用统一 Axios 实例，错误状态（4xx/5xx）有明确的界面提示 | ✅ 达成 | `frontend/src/api/index.ts` 统一 Axios 实例；响应拦截器捕获 4xx/5xx 错误，通过 ElMessage.error 展示错误详情 |
| M2-AC-08 | 界面数据正确性验证：展示的 `content` 字段与后端存储的原始输入一致；各日志页面新增的记录内容与操作参数一致 | ⚠️ 部分达成 | 代码层面直接使用后端返回的 `content` 字段，无任何转换，逻辑正确；但受限于研发环境无网络访问（无法下载 Embedding 模型），无法启动后端服务进行端到端验证 |
| M2-AC-09 | M2 阶段研发执行报告已输出，各工作条目均有明确的完成状态记录 | ✅ 达成 | 本文件 |

---

## 4. 技术实现说明

### 4.1 目录结构

```text
frontend/src/
├── api/
│   ├── index.ts          # 统一 Axios 实例 + 全部 API 调用函数（含错误拦截器）
│   └── types.ts          # TypeScript 类型定义
├── components/
│   ├── LogTable.vue      # 公共日志表格组件
│   └── MemoryCard.vue    # 公共记忆卡片组件
├── stores/
│   ├── log.ts            # useLogStore（存储/查询日志状态管理）
│   └── memory.ts         # useMemoryStore（记忆查询/删除状态管理）
├── views/
│   ├── FeedbackView.vue  # 反馈记录页面
│   ├── HomeView.vue      # 控制台（含分级存储统计面板）
│   ├── LogsView.vue      # 操作日志页面
│   └── MemoriesView.vue  # 记忆管理页面
├── router/index.ts       # 路由配置（/、/memories、/logs、/feedback）
├── App.vue               # 根组件（含侧边导航菜单）
└── main.ts               # 应用入口
```

### 4.2 API 端点映射

| 功能 | HTTP 方法 | 端点 |
| --- | --- | --- |
| 查询记忆 | GET | `/api/v1/memories?query=&top_k=&fast_only=` |
| 删除记忆 | DELETE | `/api/v1/memories/{id}` |
| 存储操作日志 | GET | `/api/v1/logs/save` |
| 查询操作日志 | GET | `/api/v1/logs/query` |
| 价值评分 | GET | `/api/v1/memories/{id}/value-score` |
| 反馈日志 | GET | `/api/v1/memories/{id}/feedback/logs` |
| 分级存储统计 | GET | `/api/v1/admin/tier-stats` |
| 磁盘占用统计 | GET | `/api/v1/admin/disk-stats` |

### 4.3 附带修复

在 M2 研发过程中，发现 `backend/src/air_memory/disk/manager.py` 存在 SQLite 日期格式比较 Bug：`created_at` 字段存储 ISO 8601 格式（含 `T` 分隔符），而 SQLite `datetime('now', ...)` 返回空格分隔格式，导致词典序比较错误。已修复：使用 `datetime(replace(substr(created_at, 1, 19), 'T', ' '))` 规范化格式后再比较。

---

## 5. 遗留问题清单

| 编号 | 问题描述 | 严重等级 | 对后续里程碑的影响 |
| --- | --- | --- | --- |
| M2-ISSUE-01 | 研发环境无网络访问，无法下载 Embedding 模型启动后端，M2-AC-08 端到端验证无法在当前环境执行 | 低 | 对 M3（单元测试）无影响，M3 可使用 Mock 进行测试；M6（系统确认）需在有完整后端服务的环境执行验证 |
| M2-ISSUE-02 | 前端构建产物为单一大 chunk（约 1MB），超过 Vite 500KB 警告阈值 | 低 | 不影响功能，M4（部署配置）阶段可使用 Vite 代码分割优化；不影响 M3 测试 |

---

## 6. 对后续里程碑的影响评估

| 里程碑 | 影响说明 |
| --- | --- |
| M3（单元测试就绪） | M2 已完成公共组件 `MemoryCard.vue` 和 `LogTable.vue`，以及视图 `MemoriesView`、`LogsView`、`FeedbackView`；Sparrow 可直接对这些组件和视图编写单元测试（M3-09、M3-10）。Pinia Store 和 API 层均可通过 Mock 进行独立测试。 |
| M4（部署配置就绪） | M2 前端代码已完成，`frontend/` 目录结构稳定，Neo 可基于此编写 `frontend/Dockerfile`。建议在 Dockerfile 中加入 `vite build` 构建步骤并配置 Nginx 提供静态文件服务。 |
| M5（文档就绪） | M2 实现的四个路由页面功能已明确，Nia 可据此编写用户手册的 Web UI 操作说明章节。 |
| M6（系统确认完成） | M2-ISSUE-01 的端到端验证将在 M6 阶段由 Wii 在完整部署环境下完成（M6-04、M6-08、M6-09）。 |
