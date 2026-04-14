# AIR_Memory v1.2.5 发布说明

**发布日期**: 2026-04-14
**版本类型**: Patch Release

---

## 概述

v1.2.5 包含 4 项 Bug 修复。主要变更为：修复存储操作日志乱码徽章检测失效问题（v1.2.4 引入的乱码徽章功能实际失效）、彻底修复 Windows 浏览器持续激活问题（Issue #46）、修复存储操作日志在 F12 中显示为 Unicode 转义序列的问题（Issue #47）、以及修复 UI 时间字段显示 UTC 而非本地时间的问题（Issue #45）。不包含 Breaking Change，直接升级即可。

---

## 修复问题

### 1. 存储操作日志乱码徽章不显示

**问题描述**

v1.2.4 为存储操作日志新增了乱码内容检测和"乱码"徽章显示功能，但实际使用时徽章从不出现，乱码内容（大量问号）直接裸露显示在"原始内容"列中。从浏览器 F12 可确认后台响应数据本身已携带乱码，查询操作日志则正常显示中文。

**根因分析**

v1.2.4 的前端 `isGarbled()` 函数以"内容中是否含非 ASCII 字符"作为检测前置条件：

```typescript
// v1.2.4 旧逻辑（有误）
const nonAscii = [...content].filter(c => c.charCodeAt(0) > 127)
if (nonAscii.length > 0) {
  // 才检测问号占比...
}
```

然而 Windows CP1252 编码失败的产物 `????` 是纯 ASCII 问号，不含任何非 ASCII 字符，导致检测逻辑被完全绕过，乱码徽章永远不会显示。后端 `log/service.py` 的 `isGarbled()` 存在相同的逻辑漏洞。

**修复方案**

1. **后端**（`log/service.py`）：提取独立函数 `_is_garbled()`，修复检测逻辑，移除"必须含非 ASCII"的前置条件，增加"纯 ASCII 问号占比 > 50%"场景。每次读取存储日志时动态计算并写入 `SaveLog.is_garbled` 字段。

2. **后端**（`models/log.py`）：`SaveLog` 模型新增 `is_garbled: bool` 字段，由服务层动态赋值，不持久化到数据库。

3. **前端**（`LogsView.vue`）：`isGarbled()` 函数重构为优先信任服务端返回的 `row.is_garbled`（权威结果），同步修复客户端兜底检测逻辑，覆盖纯 ASCII 问号场景。

4. **前端**（`types.ts`）：`SaveLog` 接口新增 `is_garbled: boolean` 字段。

**修复效果**

CP1252 损坏产生的 `????` 内容现可被正确识别为乱码，"原始内容"列显示橙色"乱码"徽章，鼠标悬停提示"此记录内容疑似因编码问题损坏（历史遗留），新版本新增的记忆不受影响"，乱码文本以灰色斜体渲染。

---

### 2. Windows 浏览器始终激活自身（Issue #46）

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

### 3. 存储操作日志在 F12 中显示 Unicode 转义序列（Issue #47）

**问题描述**

在浏览器 F12 开发者工具的 Network 面板中查看"存储操作日志"的后台响应，中文内容显示为 `\u4e2d\u6587` 形式的 Unicode 转义序列，而"查询操作日志"中可正常显示中文。

**根因分析**

FastAPI 默认使用 Python 标准库 `json` 模块序列化响应，其 `ensure_ascii=True` 默认值会将所有非 ASCII 字符（包括中文）转换为 `\uXXXX` 形式的转义序列。虽然浏览器能正确解析为中文并在 UI 中显示，但在 F12 原始响应视图中显示为转义序列，造成"乱码"的感知。

**修复方案**

1. `backend/requirements.txt` 和 `backend/pyproject.toml`：添加 `orjson>=3.9` 依赖（Rust 实现的高性能 JSON 库，FastAPI 官方推荐）。

2. `backend/src/air_memory/main.py`：在 FastAPI 实例化时设置 `default_response_class=ORJSONResponse`。`orjson` 默认 `ensure_ascii=False`，所有 API 响应将直接输出真实 UTF-8 中文字符。

---

### 4. UI 时间字段显示 UTC 而非本地时间（Issue #45）

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
| `backend/src/air_memory/log/service.py` | 修复 | 提取 `_is_garbled()` 函数，修复纯 ASCII 问号检测漏洞；`get_save_logs()` 动态计算并赋值 `is_garbled` |
| `backend/src/air_memory/models/log.py` | 新增字段 | `SaveLog` 新增 `is_garbled: bool = False` |
| `backend/src/air_memory/main.py` | 修复 | 版本号更新至 1.2.5；anyio 相关模块加入日志抑制列表；添加 ORJSONResponse 默认响应类 |
| `backend/requirements.txt` | 依赖更新 | 添加 `orjson>=3.9` |
| `backend/pyproject.toml` | 版本更新 | version `1.2.4` -> `1.2.5`；添加 orjson 依赖 |
| `start.bat` | 修复 | uvicorn 命令添加 `--log-level warning`；Banner 版本号 v1.2.4 -> v1.2.5 |
| `start.sh` | 修复 | uvicorn 命令添加 `--log-level warning`；Banner 版本号 v1.2.4 -> v1.2.5 |
| `frontend/src/api/types.ts` | 新增字段 | `SaveLog` 接口新增 `is_garbled: boolean` |
| `frontend/src/utils/time.ts` | 新增 | `formatLocalTime()` 时间本地化工具函数 |
| `frontend/src/views/LogsView.vue` | 修复 | `isGarbled()` 重构：优先信任服务端 `is_garbled`，修复客户端兜底检测逻辑；时间列改为本地时间显示 |
| `frontend/src/views/FeedbackView.vue` | 修复 | 反馈记录时间列改为本地时间显示 |
| `frontend/src/components/MemoryCard.vue` | 修复 | 记忆卡片创建时间改为本地时间显示 |
| `frontend/dist/` | 重新构建 | 同步最新前端代码 |
| `doc/user_guide.md` | 文档更新 | 2.4 节修正乱码徽章说明，补充修复版本信息 |
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

升级不影响已有数据，`data/` 目录完整保留。历史乱码数据（`????`）本身无法恢复，但本版本修复后这些记录将正确显示"乱码"徽章，不再裸露展示问号内容。
