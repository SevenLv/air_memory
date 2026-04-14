# 编码问题 - Issue #32 Windows 中文乱码为问号修复

## 标签

编码, UTF-8, PYTHONUTF8, Windows, 中文乱码, 问号, MCP, query_memory, start.bat, start.sh, CP1252, ANSI

## 问题描述

Windows 上通过 MCP `save_memory` 存储中文记忆后，Web UI 和 AI `query_memory` 返回的内容显示为大量问号 `?`。

## 根因分析结论

### 主要根因：`PYTHONUTF8=1` 缺失

`chcp 65001` 与 `PYTHONUTF8=1` 的区别：

- `chcp 65001`：仅修改 Windows 控制台的 OEM 代码页，影响 CMD 窗口显示，**不影响** Python 的 `locale.getpreferredencoding()`
- `PYTHONUTF8=1`：强制 Python 使用 UTF-8，影响 `locale.getpreferredencoding()`、`open()` 默认编码、第三方库的文件 I/O

在非 CJK Windows（如 CP1252 西欧代码页）上，`PYTHONUTF8=1` 缺失时：

```python
'你好世界'.encode('cp1252', errors='replace')  # → b'????' (每个汉字 = 一个 ?)
```

产生"大量问号"现象。

### 次要根因：MCP `query_memory` 返回 `list[dict]`

MCP SDK `_convert_to_content()` 对 `list` 递归处理，将每个 dict 拆分为独立 TextContent 块，部分 AI 客户端只读第一块。

### 已排除根因

| 假设 | 结论 |
| --- | --- |
| FastAPI JSONResponse `ensure_ascii=True` | Starlette 1.x 固定使用 `ensure_ascii=False` + UTF-8，**不是根因** |
| aiosqlite 编码问题 | sqlite3 TEXT 列始终 UTF-8，与 locale 无关，**不是根因** |
| MCP SDK `model_dump_json` 转义 | pydantic v2 输出原始汉字，无 `\uXXXX`，**不是根因** |
| ChromaDB 存储编码 | ChromaDB >= 0.6 使用 SQLite 存储文档（二进制），**不是根因** |

## 修复内容

### 1. start.bat（必要修复）

在 uvicorn 启动前（PORT 设置后）添加：

```bat
if not defined PYTHONUTF8 set "PYTHONUTF8=1"
if not defined PYTHONIOENCODING set "PYTHONIOENCODING=utf-8"
```

### 2. start.sh（防御性修复）

```bash
export PYTHONUTF8="${PYTHONUTF8:-1}"
export PYTHONIOENCODING="${PYTHONIOENCODING:-utf-8}"
```

### 3. mcp/server.py

`query_memory` 返回类型从 `list[dict]` 改为 `str`：

```python
import json
return json.dumps(results, ensure_ascii=False)
```

### 4. main.py

- 模块级 `logging` 初始化（整理重复 import）
- Windows 启动检查 `sys.flags.utf8_mode`，未开启时输出警告

## 验证方法

在 Windows 上重现：在 start.bat 中**不设** `PYTHONUTF8=1`，存储中文记忆，查询时返回 `????`。设置后问号消失。

## 最短修复路径

1. 在 start.bat 的 `if not defined PORT` 之后加：`if not defined PYTHONUTF8 set "PYTHONUTF8=1"`
2. 在 `backend/src/air_memory/mcp/server.py` 修改 `query_memory` 返回 `json.dumps(results, ensure_ascii=False)`

## 引用规则

- ai_rules/README.md v0.1
- ai_rules/task_rules/basic_rules.md v未标注
- ai_rules/perm_rules/basic_rules.md v0.1
- ai_rules/memory_rules/basic_rules.md v0.1
