# AIR_Memory v1.2.8 发布说明

**发布日期**: 2026-04-15
**版本类型**: Patch Release

---

## 概述

v1.2.8 新增记忆管理 UI 功能，包括记忆列表分页浏览、按 ID/时间范围筛选以及记忆详情页，不含 Breaking Change，直接升级即可。

---

## 新增功能

### 记忆管理 UI 增强（`/memories`）

**背景**

原 `/memories` 页面仅提供语义查询功能，无法按管理视角浏览所有已存储的记忆。本次改版将其重构为管理列表视图，满足人类用户浏览、筛选和查看记忆详情的需求。

**新增功能**

- **默认列表**：进入页面后自动加载最近记忆，按提交时间倒序展示。
- **分页**：固定每页 20 条，通过分页器切换页码。
- **条件筛选**：支持按记忆 ID（完整或片段）和时间范围（开始/结束时间）组合筛选。
- **详情页**：点击列表项中的"查看详情"按钮，跳转至 `/memories/{memory_id}` 详情页，展示记忆 ID、原始数据、提交时间和当前价值评分。

**相关后端变更**

新增 REST API 接口，供详情页按 ID 精确查询单条记忆：

```
GET /api/v1/logs/save/{memory_id}
```

响应（HTTP 200）：

```json
{
  "memory_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "content": "用户偏好使用深色主题，字体大小设置为 16px",
  "created_at": "2026-04-10T08:00:00Z"
}
```

---

## 变更文件

| 文件 | 变更类型 | 说明 |
| --- | --- | --- |
| `backend/src/air_memory/main.py` | 版本更新 | 版本号更新至 1.2.8 |
| `backend/pyproject.toml` | 版本更新 | version `1.2.7` -> `1.2.8` |
| `frontend/package.json` | 版本更新 | version `1.2.7` -> `1.2.8` |
| `start.sh` | 版本更新 | 版本号 v1.2.7 -> v1.2.8 |
| `start.bat` | 版本更新 | 版本号 v1.2.7 -> v1.2.8 |
| `README.md` | 文档更新 | 版本号 v1.2.7 -> v1.2.8；更新目录结构图 |
| `backend/src/air_memory/api/logs.py` | 新增接口 | 新增 `GET /api/v1/logs/save/{memory_id}` 接口 |
| `frontend/src/views/MemoriesView.vue` | 功能重构 | 改为管理列表视图，支持分页与 ID/时间范围筛选 |
| `frontend/src/views/MemoryDetailView.vue` | 新增 | 记忆详情页，展示 ID、原始数据、提交时间和价值评分 |
| `frontend/src/router/index.ts` | 路由新增 | 新增 `/memories/:memoryId` 路由 |
| `frontend/dist/` | 构建更新 | 预构建前端静态文件（含新增页面） |
| `frontend/tests/MemoriesView.spec.ts` | 测试更新 | 适配新列表视图测试 |
| `frontend/tests/MemoryDetailView.spec.ts` | 测试新增 | 详情页单元测试 |
| `doc/user_guide.md` | 文档更新 | v1.6：2.3 节更新记忆管理 UI 使用说明 |
| `doc/release_notes_v1.2.8.md` | 新增 | 本文件 |

---

## 升级说明

前往 [GitHub Releases 页面](https://github.com/SevenLv/air_memory/releases/latest) 下载 v1.2.8 发布包，解压后将旧版本 `data/` 目录复制到新目录下，然后启动服务即可。

**macOS / Linux**：

```bash
unzip air_memory-v1.2.8.zip
cp -r old_dir/data air_memory-v1.2.8/
cd air_memory-v1.2.8
bash start.sh
```

**Windows**：

解压 `air_memory-v1.2.8.zip`，将旧版本 `data\` 目录复制到新目录下，双击 `start.bat` 或在 CMD 中执行：

```cmd
start.bat
```

升级不影响已有数据，`data/` 目录完整保留。
