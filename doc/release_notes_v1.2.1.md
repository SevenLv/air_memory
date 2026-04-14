# AIR_Memory v1.2.1 发布说明

**发布日期**: 2026-04-14
**版本类型**: Patch Release

---

## 概述

v1.2.1 完整修复了 Issue #30 (Windows 上浏览器在切换到别的程序时不断激活). v1.2.0 已应用
`--no-access-log` 抑制 HTTP 访问日志, 但 FastMCP 库在模块导入时通过 `basicConfig()` 将
root logger 级别设为 INFO 并添加 RichHandler, 导致 MCP 每次工具调用仍有 INFO 日志写入
stderr, 持续引发 CMD 窗口 FlashWindowEx 任务栏闪烁. 本次发布修复该问题. 不包含 Breaking
Change, 直接升级即可.

---

## 修复问题

### Windows 上浏览器在切换到别的程序时不断激活 (Issue #30, 追加修复)

**问题描述**

v1.2.0 应用了 `--no-access-log` 后, 用户反馈问题仍然存在.

**根因分析 (深度)**

uvicorn 启动时序导致 root logger 被 FastMCP 污染:

1. uvicorn 的 `Config.__init__()` 先执行 `configure_logging()`, 此时仅配置 `uvicorn.*`
   系列 logger, root logger 无 handler, 级别为 WARNING.
2. uvicorn 的 `Config.load()` 之后才导入 ASGI app (`air_memory.main:app`).
3. 导入触发 `air_memory.mcp.server` 模块执行, 其模块级语句 `mcp = FastMCP("AIR_Memory")`
   调用 `configure_logging("INFO")`, 通过 `logging.basicConfig()` 在 root logger 上
   添加 `RichHandler(stderr)` 并将级别改为 INFO.
4. 此时 root logger 已有 handler, 因此 `mcp.server.*` 的每条 INFO 日志 (如 AI 客户端每次
   调用工具时输出的 `"Processing request of type CallToolRequest"`) 均通过 RichHandler
   写入 stderr.
5. CMD 控制台窗口收到输出 -> Windows 调用 `FlashWindowEx(FLASHW_TRAY)` ->
   任务栏按钮橙色闪烁 -> 用户感知为"浏览器在激活自身".

`--no-access-log` 仅抑制 `uvicorn.access` logger, 无法阻止 root logger 上 RichHandler
输出的 MCP INFO 日志, 因此 v1.2.0 的修复不彻底.

**修复方案**

在 `backend/src/air_memory/main.py` 的所有 import 语句完成后, 将 root logger 级别重置为
WARNING:

```python
logging.getLogger().setLevel(logging.WARNING)
```

此调用放在 `from air_memory.mcp.server import init_mcp_services, mcp` 之后, 即 FastMCP
模块已被导入并执行了 `basicConfig()` 之后, 将 root logger 级别从 INFO(20) 恢复为
WARNING(30). 效果:

- `mcp.server.*` INFO 日志 (如每次工具调用的 `Processing request...`) -> 被过滤, 不输出
- `air_memory.*` WARNING/ERROR 日志 -> 仍正常输出 (级别 >= WARNING)
- `uvicorn.*` 所有日志 -> 不受影响 (`propagate=False`, 使用独立 handler)

---

## 变更文件

| 文件 | 变更类型 | 说明 |
| --- | --- | --- |
| `backend/src/air_memory/main.py` | 修复 | 所有 import 后添加 `logging.getLogger().setLevel(logging.WARNING)` 重置 root logger 级别; 版本号更新为 `1.2.1` |
| `backend/pyproject.toml` | 版本更新 | version `1.2.0` -> `1.2.1` |
| `start.bat` | 版本更新 | Banner 版本号 v1.2.0 -> v1.2.1 |
| `start.sh` | 版本更新 | Banner 版本号 v1.2.0 -> v1.2.1 |

---

## 升级说明

直接拉取最新代码并重新启动即可:

```bash
git pull
```

**macOS / Linux**:

```bash
bash start.sh
```

**Windows**:

```cmd
start.bat
```

升级不影响已有数据, `data/` 目录完整保留.
