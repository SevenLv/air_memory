# AIR_Memory v1.2.5 发布说明

**发布日期**: 2026-04-14
**版本类型**: Patch Release

---

## 概述

v1.2.5 包含 3 项 Bug 修复。主要变更为：彻底修复 Windows 浏览器持续激活问题（Issue #46）、修复存储操作日志在 F12 中显示为 Unicode 转义序列的问题（Issue #47）、以及修复 UI 时间字段显示 UTC 而非本地时间的问题（Issue #45）。不包含 Breaking Change，直接升级即可。

---

## 修复问题

### 1. Windows 浏览器始终激活自身（Issue #46）

**问题描述**

Windows 10 上通过 VS Code 终端启动 start.bat 后，在 Microsoft Edge 中打开 Web 界面：
1. 在任务栏点击浏览器图标无法实现最小化，最小化后立即还原；
2. 切换到其他窗口时，浏览器任务栏图标持续闪烁。

**根因分析**

v1.2.4 的修复（对 12 个第三方库单独设置 WARNING 级别）未能覆盖以下两个日志泄漏点：

1. **uvicorn 自身的 INFO 日志**：start.bat/start.sh 的 uvicorn 启动命令包含 `--no-access-log` 但缺少 `--log-level warning`，uvicorn 的 `uvicorn.error` logger 仍会在 MCP SSE 长连接断开重连时输出 `INFO` 级消息，这是**周期性**输出的根源。

2. **anyio 库日志未抑制**：`anyio` 是 uvicorn/Starlette 的异步底层库，会在连接关闭、任务取消等场景输出 INFO 日志，但 v1.2.4 的抑制列表中未包含该库。

每次有内容写入 Windows 控制台（包括 VS Code 的 ConPTY），Windows 可能对关联进程调用 `FlashWindowEx`，由于 VS Code 和 Edge 同属 Chromium 内核体系，这导致用户感知为浏览器窗口闪烁/无法最小化。

**修复方案**

1. `start.bat` 和 `start.sh`：uvicorn 启动命令增加 `--log-level warning` 参数，将 uvicorn 自身的日志输出级别限制为 WARNING 及以上。

2. `backend/src/air_memory/main.py`：在第三方库日志抑制列表中补充 `anyio`、`anyio._backends._asyncio`、`anyio._backends._trio` 三个模块。

---

### 2. 存储操作日志在 F12 中显示 Unicode 转义序列（Issue #47）

**问题描述**

在浏览器 F12 开发者工具的 Network 面板中查看"存储操作日志"的后台响应，中文内容显示为 `\u4e2d\u6587` 形式的 Unicode 转义序列，而"查询操作日志"中可正常显示中文。

**根因分析**

FastAPI 默认使用 Python 标准库 `json` 模块序列化响应，其 `ensure_ascii=True` 默认值会将所有非 ASCII 字符（包括中文）转换为 `\uXXXX` 形式的转义序列。虽然浏览器能正确解析为中文并在 UI 中显示，但在 F12 原始响应视图中显示为转义序列，造成"乱码"的感知。

**修复方案**

1. `backend/requirements.txt` 和 `backend/pyproject.toml`：添加 `orjson>=3.9` 依赖（Rust 实现的高性能 JSON 库，FastAPI 官方推荐）。

2. `backend/src/air_memory/main.py`：在 FastAPI 实例化时设置 `default_response_class=ORJSONResponse`。`orjson` 默认 `ensure_ascii=False`，所有 API 响应将直接输出真实 UTF-8 中文字符。

---

### 3. UI 时间字段显示 UTC 而非本地时间（Issue #45）

**问题描述**

Web 管理界面中所有时间字段（存储操作日志创建时间、查询操作日志创建时间、反馈记录创建时间、记忆卡片创建时间）显示的是 UTC ISO 8601 格式（如 `2025-01-15T08:30:00.123456+00:00`），而非用户本地时间。

**根因分析**

后端以 UTC 时区存储所有时间戳（符合最佳实践），但前端直接将时间字符串绑定到 `<el-table-column prop="created_at">` 或模板中，未做任何时区转换，导致显示原始 UTC 时间。

**修复方案**

1. 新建 `frontend/src/utils/time.ts`：提供 `formatLocalTime(isoString)` 工具函数，使用 `Date.toLocaleString()` 将 ISO 8601 UTC 时间字符串转换为用户浏览器所在时区的本地时间，包含空值和解析异常的兜底处理。

2. 在以下四处应用 `formatLocalTime()`：
   - `frontend/src/views/LogsView.vue`：存储操作日志的"时间"列
   - `frontend/src/views/LogsView.vue`：查询操作日志的"时间"列
   - `frontend/src/views/FeedbackView.vue`：反馈记录列表的"时间"列
   - `frontend/src/components/MemoryCard.vue`："创建时间"字段

---

## 变更文件

| 文件 | 变更类型 | 说明 |
| --- | --- | --- |
| `backend/src/air_memory/main.py` | 修复 | 版本号更新至 1.2.5；anyio 相关模块加入日志抑制列表；添加 ORJSONResponse 默认响应类 |
| `backend/requirements.txt` | 依赖更新 | 添加 `orjson>=3.9` |
| `backend/pyproject.toml` | 版本更新 | version `1.2.4` -> `1.2.5`；添加 orjson 依赖 |
| `start.bat` | 修复 | uvicorn 命令添加 `--log-level warning`；Banner 版本号 v1.2.4 -> v1.2.5 |
| `start.sh` | 修复 | uvicorn 命令添加 `--log-level warning`；Banner 版本号 v1.2.4 -> v1.2.5 |
| `frontend/src/utils/time.ts` | 新增 | `formatLocalTime()` 时间本地化工具函数 |
| `frontend/src/views/LogsView.vue` | 修复 | 存储日志和查询日志时间列改为本地时间显示 |
| `frontend/src/views/FeedbackView.vue` | 修复 | 反馈记录时间列改为本地时间显示 |
| `frontend/src/components/MemoryCard.vue` | 修复 | 记忆卡片创建时间改为本地时间显示 |
| `doc/release_notes_v1.2.5.md` | 新增 | 本文件 |

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
