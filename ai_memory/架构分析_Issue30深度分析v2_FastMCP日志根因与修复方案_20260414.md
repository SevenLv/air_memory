# 架构分析_Issue30 深度分析 v2_FastMCP 日志根因与修复方案_20260414

## 标签

Issue#30, Windows, Edge, 浏览器激活, CMD, FlashWindowEx, FastMCP, configure_logging,
basicConfig, RichHandler, root logger, uvicorn, --no-access-log, MCP, 日志, mcp.server.lowlevel,
Processing request, stderr, 任务栏闪烁, logging, logging.getLogger, setLevel

## 问题背景

Issue #30: 在 Windows 上 Edge 浏览器访问 UI, 切换到别的程序时浏览器一直在激活自身.
v1.2.0 应用了 `--no-access-log` 修复, 但用户反馈 "更新到 1.2.0 后仍有此问题".

本文件是上次会话分析 (`架构分析_Issue30_Windows浏览器激活问题根因与修复方案_20260414.md`)
的深度跟进分析, 解释为何 `--no-access-log` 修复不彻底.

## 深度分析: --no-access-log 为何不够

### 1. --no-access-log 的真实作用范围

uvicorn 源码确认 (`uvicorn/config.py`):

```python
if self.access_log is False:
    logging.getLogger("uvicorn.access").handlers = []
    logging.getLogger("uvicorn.access").propagate = False
```

效果: 仅抑制 `uvicorn.access` logger 的输出. uvicorn 其他 logger (`uvicorn`, `uvicorn.error`)
及所有第三方库 logger 不受影响.

### 2. FastMCP.configure_logging() 对 root logger 的破坏性修改

**关键代码** (`mcp/server/fastmcp/utilities/logging.py`):

```python
def configure_logging(level="INFO"):
    handlers = [RichHandler(console=Console(stderr=True), rich_tracebacks=True)]
    logging.basicConfig(
        level=level,      # "INFO"
        format="%(message)s",
        handlers=handlers,
    )
```

**关键行为**: `logging.basicConfig()` 当 root logger 没有 handler 时, 会:
1. 向 root logger 添加 `RichHandler(stderr)`
2. 将 root logger 级别设为 INFO (20)

### 3. 致命时序: uvicorn 先配置日志, 再导入 app

经过代码追踪, uvicorn 启动顺序确认如下:

```
uvicorn CLI
  └── Config.__init__()
        └── configure_logging()      ← 步骤 1: uvicorn 设置 uvicorn.* loggers
              ← root logger 此时: 无 handler, level=WARNING(30)
  └── Config.load()                  ← 步骤 2: 导入 ASGI app
        └── import_from_string("air_memory.main:app")
              └── import air_memory.mcp.server
                    └── mcp = FastMCP("AIR_Memory")   ← 模块级实例化
                          └── configure_logging("INFO")
                                └── basicConfig(handlers=[RichHandler])
                                      ← root logger 此时: 无 handler
                                      ← basicConfig 生效! 添加 RichHandler
                                      ← root logger 变为: level=INFO(20), handler=[RichHandler]
```

**验证结果** (Python 复现):

```
After uvicorn configure_logging:
  Root handlers: []          ← 此时 root 无 handler
  Root level: 30 (WARNING)

After FastMCP instantiation:
  Root handlers: [<RichHandler (NOTSET)>]   ← RichHandler 被添加!
  Root level: 20 (INFO)                     ← 级别被改为 INFO!
  mcp.server.lowlevel.server INFO enabled: True   ← MCP INFO 日志会输出到控制台!
```

### 4. 周期性控制台输出来源

当 AI 客户端 (如 Claude Desktop) 连接到 AIR Memory MCP 服务时:

| 事件 | 日志来源 | 日志内容 | 级别 |
| --- | --- | --- | --- |
| MCP 会话建立 | `mcp.server.streamable_http_manager` | `Created new transport with session ID: xxx` | INFO |
| 每次工具调用 | `mcp.server.lowlevel.server` | `Processing request of type CallToolRequest` | INFO |
| 每次工具调用 | `mcp.server.lowlevel.server` | `Processing request of type ListToolsRequest` | INFO |
| 会话结束 | `mcp.server.streamable_http` | `Terminating session: xxx` | INFO |

每次 Claude Desktop 调用 `save_memory`/`query_memory`/`feedback_memory`:
→ `mcp.server.lowlevel.server` 输出 `"Processing request of type CallToolRequest"`
→ 通过 root logger 的 RichHandler → stderr → CMD 窗口控制台输出
→ Windows FlashWindowEx → CMD 任务栏橙色闪烁
→ 用户感知为 "浏览器在激活自身"

### 5. 为何纯浏览器场景下问题可能也存在

即使没有 AI 客户端, 启动时 root logger 上的 RichHandler 也会输出以下 INFO 日志:
- `StreamableHTTP session manager started` (启动时, 一次性)
- ChromaDB/sentence-transformers 的 INFO 启动日志 (一次性)

这些是一次性输出, 不会导致"持续激活". 实际用户场景中, 大概率同时运行了 Claude Desktop.

### 6. uvicorn 自身 logger 不受影响的原因

uvicorn dictConfig 配置:
```json
"uvicorn": {"handlers": ["default"], "level": "INFO", "propagate": false}
```

`propagate=False` 意味着 uvicorn.* 消息不会传播到 root logger.
uvicorn 的启动消息 ("Uvicorn running on...", "Application startup complete") 通过
uvicorn 自己的 StreamHandler(stderr) 输出, 与 root logger 的 RichHandler 完全独立.

## 修复方案

### 方案: 在 main.py 所有导入完成后将 root logger 级别重置为 WARNING

**修改文件**: `backend/src/air_memory/main.py`

**修改位置**: 所有 import 语句之后、模块级其他代码之前

**修改内容**: 在现有 `_logger = logging.getLogger(__name__)` 行之后, 所有 from/import
完成后 (尤其是 `from air_memory.mcp.server import init_mcp_services, mcp` 之后),
添加以下代码:

```python
# 修复 Issue #30: 防止 FastMCP.configure_logging() 的 RichHandler 将 MCP INFO 日志
# 输出到控制台, 在 Windows 上触发 CMD 窗口 FlashWindowEx 导致任务栏持续闪烁.
#
# 原理: FastMCP("AIR_Memory") 在模块导入时调用 configure_logging("INFO"),
# 通过 logging.basicConfig() 在 root logger 上添加 RichHandler 并将级别设为 INFO.
# 此时 uvicorn 已完成自身的 configure_logging (设置 uvicorn.* loggers), 但尚未
# 导入 ASGI app, 因此 root logger 没有 handler, basicConfig 得以生效.
#
# 修复方式: 将 root logger 级别重置为 WARNING, 过滤掉 MCP 库的 INFO 日志输出.
# 效果验证:
#   - mcp.server.lowlevel.server INFO "Processing request..." -> 被过滤 (不输出)
#   - air_memory.* WARNING/ERROR -> 仍然输出 (级别 >= WARNING)
#   - uvicorn.* 所有日志 -> 不受影响 (propagate=False, 使用自己的 handler)
logging.getLogger().setLevel(logging.WARNING)
```

**效果验证** (Python 复现):

```
After fix - root level: 30 (WARNING)
mcp.server.lowlevel INFO enabled: False    ← MCP INFO 日志被过滤 ✓
air_memory.main WARNING enabled: True      ← 应用 WARNING 日志仍输出 ✓
air_memory.main ERROR enabled: True        ← 应用 ERROR 日志仍输出 ✓
uvicorn.error WARNING enabled: True        ← uvicorn WARNING 日志仍输出 ✓
```

### 修改示意 (main.py 相关片段)

```python
import asyncio
import logging
import os
import sys
from contextlib import asynccontextmanager

# ... (其他 import) ...

from air_memory.mcp.server import init_mcp_services, mcp    # FastMCP 在此导入时实例化

APP_VERSION = "1.2.x"

_logger = logging.getLogger(__name__)

# 修复 Issue #30: 将 root logger 级别重置为 WARNING
# (FastMCP 在上方模块导入时通过 basicConfig 将其设为了 INFO)
logging.getLogger().setLevel(logging.WARNING)

# Windows UTF-8 检查 (后面)
if sys.platform == "win32" and sys.flags.utf8_mode == 0:
    _logger.warning("Python UTF-8 模式未启用...")
```

**注意**: `logging.getLogger().setLevel(logging.WARNING)` 必须放在
`from air_memory.mcp.server import ...` 之后, 因为 FastMCP 在模块导入时执行.

## 相关源码位置

| 文件 | 关键行 | 说明 |
| --- | --- | --- |
| `uvicorn/config.py` | `~280: self.configure_logging()` | uvicorn 在 Config.__init__ 中配置日志 |
| `uvicorn/config.py` | `~224: self.loaded_app = import_from_string(self.app)` | uvicorn 在 Config.load 中导入 app |
| `uvicorn/server.py` | `~86: config.load()` | load() 在 _serve() 中被调用 (晚于 __init__) |
| `mcp/server/fastmcp/server.py` | `~96: configure_logging(self.settings.log_level)` | FastMCP.__init__ 调用 |
| `mcp/server/fastmcp/utilities/logging.py` | `configure_logging()` | 调用 basicConfig 添加 RichHandler |
| `mcp/server/lowlevel/server.py` | `~727: logger.info("Processing request...")` | 每次 MCP 工具调用输出 |
| `mcp/server/streamable_http_manager.py` | `~255: logger.info("Created new transport...")` | 每次 AI 客户端连接输出 |
| `backend/src/air_memory/mcp/server.py` | `mcp = FastMCP("AIR_Memory")` | 模块级实例化触发 configure_logging |
| `backend/src/air_memory/main.py` | (待修改) | 需添加 logging.getLogger().setLevel(WARNING) |

## 完整修复清单 (Issue #30)

| 修复项 | 状态 | 说明 |
| --- | --- | --- |
| start.bat `--no-access-log` | 已完成 (v1.2.0) | 抑制 HTTP 访问日志 |
| start.sh `--no-access-log` | 已完成 (v1.2.0) | 抑制 HTTP 访问日志 |
| main.py root logger 级别重置 | 待完成 | 抑制 MCP 库 INFO 日志, 本文核心修复 |

## 分析局限与说明

- 此问题仅在 Windows 上体现 (FlashWindowEx 是 Windows 专属 API)
- macOS/Linux 终端不会因控制台输出而 "激活自身"
- 纯浏览器场景 (无 AI 客户端) 的持续闪烁问题: 主要由 AI 客户端的 MCP 工具调用引发;
  若真正没有任何 AI 客户端, 则启动后无周期性控制台输出 (只有一次性启动日志)
- 修复后 uvicorn 的启动消息 (INFO 级别, 来自 uvicorn.error, propagate=False) 不受影响,
  用户仍可看到服务启动成功的提示
