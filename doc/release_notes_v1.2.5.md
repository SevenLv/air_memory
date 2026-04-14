# AIR_Memory v1.2.5 发布说明

**发布日期**: 2026-04-14
**版本类型**: Patch Release

---

## 概述

v1.2.5 为 Bug 修复版本，修复了 v1.2.4 中"存储操作日志"乱码检测失效的问题（Issue #45）。v1.2.4 虽引入了乱码徽章功能，但检测逻辑存在漏洞，导致 CP1252 编码损坏产生的纯 ASCII 问号（`????`）无法被识别，乱码徽章始终不显示，UI 上直接裸露展示乱码内容。本版本完整修复了该问题。不包含 Breaking Change，直接升级即可。

---

## 修复问题

### 存储操作日志乱码徽章不显示

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

## 变更文件

| 文件 | 变更类型 | 说明 |
| --- | --- | --- |
| `backend/src/air_memory/log/service.py` | 修复 | 提取 `_is_garbled()` 函数，修复纯 ASCII 问号检测漏洞；`get_save_logs()` 动态计算并赋值 `is_garbled` |
| `backend/src/air_memory/models/log.py` | 新增字段 | `SaveLog` 新增 `is_garbled: bool = False` |
| `backend/src/air_memory/main.py` | 版本更新 | `APP_VERSION` 升至 `1.2.5` |
| `backend/pyproject.toml` | 版本更新 | version `1.2.4` -> `1.2.5` |
| `frontend/src/api/types.ts` | 新增字段 | `SaveLog` 接口新增 `is_garbled: boolean` |
| `frontend/src/views/LogsView.vue` | 修复 | `isGarbled()` 重构：优先信任服务端 `is_garbled`，修复客户端兜底检测逻辑 |
| `frontend/package.json` | 版本更新 | version `1.2.4` -> `1.2.5` |
| `frontend/dist/` | 重新构建 | 同步最新前端代码 |
| `start.bat` | 版本更新 | Banner 版本号 v1.2.4 -> v1.2.5 |
| `start.sh` | 版本更新 | Banner 版本号 v1.2.4 -> v1.2.5 |
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
