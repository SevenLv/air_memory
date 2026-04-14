# AIR_Memory v1.2.4 发布说明

**发布日期**: 2026-04-14
**版本类型**: Minor Release

---

## 概述

v1.2.4 包含 3 项 Bug 修复和 1 项新功能。主要变更为：修复 UI 版本号显示错误（Issue #42）、为历史乱码存储记录添加可视化标记（Issue #37）、进一步抑制 Windows 第三方库日志输出以减少浏览器激活问题（Issue #30），以及新增反馈记录列表功能（Issue #43）。不包含 Breaking Change，直接升级即可。

---

## 修复问题

### 1. UI 版本号显示错误（Issue #42）

**问题描述**

v1.2.3 发布后，Web 管理界面 Header 右侧仍显示版本号 `1.2.2`，与实际版本不符。

**根因分析**

后端 `main.py` 中的 `APP_VERSION` 常量、`pyproject.toml`、`package.json` 等版本号字段在上一次发版时未全部同步更新，导致前端通过 `GET /api/v1/version` 接口获取到的版本号滞后一个版本。

**修复方案**

统一更新以下文件中的版本号至 `1.2.4`：`backend/src/air_memory/main.py`、`backend/pyproject.toml`、`frontend/package.json`、`start.bat`、`start.sh`。

---

### 2. 历史存储记录乱码内容标记（Issue #37）

**问题描述**

v1.2.0 之前（数据库编码问题修复前），AI Agent 通过 MCP 存储的部分记忆内容以 `?` 字符写入数据库，在操作日志页面的"存储日志"列表中显示为大量问号（乱码），影响阅读体验。问题已在 v1.2.0 修复根因，但历史损坏数据无法复原。

**修复方案**

前端 `LogsView.vue` 新增 `isGarbled()` 检测逻辑：当存储内容中问号比例超过 30% 时，在"原始内容"列前方显示橙色"乱码"徽章，鼠标悬停提示"此记录内容疑似因编码问题损坏（历史遗留），新版本新增的记忆不受影响"，乱码文本以灰色斜体渲染以示区分。

---

### 3. Windows 浏览器切换时持续激活（Issue #30，追加修复）

**问题描述**

在 Windows 上通过 Microsoft Edge 访问 Web 界面，切换到其他程序后浏览器窗口会反复激活（任务栏闪烁）。此问题自 v1.2.0 起历经多次修复，但 v1.2.3 版本仍未彻底解决。

**根因分析**

v1.2.1 已将 root logger 级别重置为 WARNING，可阻止 FastMCP 自身的 INFO 日志写入 stderr。但 `chromadb`、`sentence_transformers`、`httpx`、`mcp` 等第三方库在各自模块初始化时直接在子 logger 上添加了 `StreamHandler`（不依赖 root logger 传播），因此仍有日志持续写入 stderr，触发 CMD 窗口闪烁。

**修复方案**

在 `backend/src/air_memory/main.py` 的 import 阶段完成后，对 12 个已知存在 stderr 噪声输出的第三方库子 logger 显式设置级别为 `WARNING`，从根本上阻断这些库的 INFO 日志写入 stderr。

---

## 新功能

### 反馈记录列表（Issue #43）

**新增内容**

在 Web 管理界面 `/feedback` 页面新增完整的反馈记录列表功能，整合现有的价值评分查询，并扩展了时间段筛选和分页能力。

**前端变更（`FeedbackView.vue` 重构）**

- 查询条件面板：支持按记忆 ID 过滤（可选），以及通过日期时间范围选择器按时间段筛选
- 综合价值评分面板：仅在指定记忆 ID 查询时显示，与反馈列表联动
- 反馈记录列表：页面加载时自动展示全部记录，底部提供 `el-pagination` 分页控件（默认每页 20 条，可选 10 / 20 / 50 / 100）
- 新增"重置"按钮，一键清空所有筛选条件并恢复初始状态

**后端变更**

新增 REST API：

```
GET /api/v1/logs/feedback
```

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `page` | integer | 页码，默认 1 |
| `page_size` | integer | 每页条数，默认 20，上限 100 |
| `memory_id` | string | 按记忆 ID 过滤（可选） |
| `start_time` | string | 开始时间，ISO 8601（可选） |
| `end_time` | string | 结束时间，ISO 8601（可选） |

响应包含 `logs`（当前页记录）、`count`（当前页条数）、`total`（符合条件总条数）。

---

## 变更文件

| 文件 | 变更类型 | 说明 |
| --- | --- | --- |
| `backend/src/air_memory/main.py` | 修复 | 版本号更新至 1.2.4；添加 12 个第三方库的 WARNING 级别设置 |
| `backend/pyproject.toml` | 版本更新 | version `1.2.3` -> `1.2.4` |
| `backend/src/air_memory/api/logs.py` | 新增 | 新增 `GET /api/v1/logs/feedback` 路由 |
| `backend/src/air_memory/feedback/service.py` | 新增 | 新增 `get_all_feedback_logs()` 方法，支持分页和过滤 |
| `backend/src/air_memory/models/feedback.py` | 新增 | 新增 `FeedbackLogsWithTotalResponse` 响应模型 |
| `backend/src/air_memory/log/service.py` | 修复 | 存储日志服务添加乱码内容防御性检测 |
| `frontend/package.json` | 版本更新 | version `1.2.3` -> `1.2.4` |
| `frontend/src/views/FeedbackView.vue` | 重构 | 反馈记录列表、时间段查询、分页功能 |
| `frontend/src/views/LogsView.vue` | 新增 | 乱码内容检测及徽章显示 |
| `frontend/src/api/index.ts` | 新增 | 新增 `getAllFeedbackLogs()` API 调用方法 |
| `frontend/src/api/types.ts` | 新增 | 新增 `FeedbackLogsWithTotalResponse` 类型定义 |
| `start.bat` | 版本更新 | Banner 版本号 v1.2.3 -> v1.2.4 |
| `start.sh` | 版本更新 | Banner 版本号 v1.2.3 -> v1.2.4 |
| `doc/user_guide.md` | 文档更新 | 2.4 节补充乱码徽章说明；重写 2.5 节反馈记录列表；3.2.3 节补充新接口 |
| `doc/release_notes_v1.2.4.md` | 新增 | 本文件 |

---

## 升级说明

直接拉取最新代码并重新启动即可：

```bash
git pull
```

**macOS / Linux**：

```bash
bash start.sh
```

**Windows**：

```cmd
start.bat
```

升级不影响已有数据，`data/` 目录完整保留。
