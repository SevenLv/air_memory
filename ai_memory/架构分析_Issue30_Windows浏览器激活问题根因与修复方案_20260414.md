# 架构分析_Issue30_Windows浏览器激活问题根因与修复方案_20260414

## 标签

Issue#30, Windows, Edge, 浏览器激活, uvicorn, access-log, CMD, 任务栏闪烁, FlashWindowEx,
sse_starlette, SSE, ping, MCP, start.bat, start.sh, --no-access-log, Windows专属行为

## 问题描述

Issue #30: 在 Windows 上浏览器 (Edge) 访问 UI, 当切换到别的程序时, 浏览器一直在激活自身.

## 排查结论

**前端代码本身无任何可导致浏览器激活的机制**: 未发现 window.focus()/setInterval 轮询/
Notification API/Service Worker/WebSocket/document.title 动态修改等.

## 根因分析

### 主要根因: uvicorn access log 写入 CMD 窗口触发 Windows FlashWindowEx

因果链:
1. start.bat 在 CMD 窗口中运行 uvicorn, 未配置 --no-access-log
2. 浏览器发出 HTTP 请求 -> uvicorn 写 access log 到 stderr -> CMD 窗口控制台输出
3. Windows 检测到后台 console 窗口收到新输出
4. Windows 调用 FlashWindowEx(FLASHW_TRAY) 使 CMD 任务栏按钮橙色闪烁
5. 用户将 AIR Memory 相关窗口的闪烁感知为 "浏览器在激活自身"

关键代码位置: start.bat 第 111 行, start.sh 第 157~161 行

### 次要根因: sse_starlette SSE Ping 机制加剧 CMD 窗口写入频率

- MCP Server 使用 mcp.streamable_http_app() 内部依赖 sse_starlette.EventSourceResponse
- DEFAULT_PING_INTERVAL = 15 秒, 每 15 秒向 SSE 连接发送 ping
- SSE ping 本身不产生新 access log 行, 但 SSE 连接建立/重建时产生
- AI 客户端 (Claude Desktop 等) 断线重连会增加 access log 写入频率

### 平台特异性说明

此问题仅在 Windows 上出现, macOS/Linux 不受影响, 因为 FlashWindowEx 是 Windows 专属 API.
这与 Issue 描述 "在 Windows 上" 完全吻合.

## 修复方案

### 推荐: 在 start.bat 和 start.sh 的 uvicorn 命令中添加 --no-access-log

start.bat 第 111 行修改:
```bat
uvicorn air_memory.main:app --host 127.0.0.1 --port !PORT! --app-dir backend\src --no-access-log
```

start.sh 第 157~161 行修改:
```bash
exec uvicorn air_memory.main:app \
    --host 127.0.0.1 \
    --port "$PORT" \
    --app-dir backend/src \
    --no-access-log
```

效果: 消除每次 HTTP 请求的控制台输出, 从根本上消除 CMD 窗口任务栏闪烁.
服务启动日志和 WARNING/ERROR 级别日志仍保留.

### 可选补充: --log-level warning

若需进一步减少日志, 可加 --log-level warning, 但会隐藏服务启动成功的 INFO 消息.
