"""FastAPI 应用入口，包含 lifespan 初始化、CORS 配置和路由注册。

默认服务端口：8080（由启动脚本通过 uvicorn 命令行参数指定）。
"""

import asyncio
import logging
import os
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sentence_transformers import SentenceTransformer
from starlette.exceptions import HTTPException as StarletteHTTPException

from air_memory.api.router import router
from air_memory.config import settings
from air_memory.db import init_db
from air_memory.disk.manager import DiskManager
from air_memory.feedback.service import FeedbackService
from air_memory.log.service import LogService
from air_memory.mcp.server import init_mcp_services, mcp
from air_memory.memory.service import MemoryService
from air_memory.memory.tier_manager import TierManager

APP_VERSION = "1.2.1"

_logger = logging.getLogger(__name__)

# 修复 Issue #30: 将 root logger 级别重置为 WARNING，防止 MCP 库的 INFO 日志
# 在 Windows 上引发 CMD 控制台输出，触发 FlashWindowEx 导致任务栏持续闪烁。
#
# 原理：FastMCP("AIR_Memory") 在上方模块导入时调用 configure_logging("INFO")，
# 通过 logging.basicConfig() 在 root logger 上添加 RichHandler 并将级别设为 INFO。
# 此时 uvicorn 已完成自身 configure_logging（配置 uvicorn.* loggers），但尚未
# 导入 ASGI app，root logger 没有 handler，basicConfig 得以生效。
# 结果：mcp.server.* 的 INFO 日志（如每次工具调用的 "Processing request..."）
# 通过 root logger 的 RichHandler 写入 stderr，CMD 窗口收到输出后
# Windows 调用 FlashWindowEx(FLASHW_TRAY) 使任务栏橙色闪烁。
#
# 修复效果：
#   - mcp.server.* INFO 日志 -> 被过滤，不输出到控制台
#   - air_memory.* WARNING/ERROR -> 仍正常输出
#   - uvicorn.* 所有日志 -> 不受影响（propagate=False，使用独立 handler）
logging.getLogger().setLevel(logging.WARNING)

# Windows 平台启动时检查 UTF-8 模式，避免中文因 ANSI 代码页被损坏为问号
# PYTHONUTF8=1 或 python -X utf8 可激活 UTF-8 模式（sys.flags.utf8_mode == 1）
if sys.platform == "win32" and sys.flags.utf8_mode == 0:
    _logger.warning(
        "Python UTF-8 模式未启用（PYTHONUTF8=1 未设置）。\n"
        "在非 CJK Windows（如 CP1252 代码页）上，中文内容可能因 locale 编码被损坏为问号。\n"
        "请在 start.bat 中确认 'set PYTHONUTF8=1' 已生效。"
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理：启动时初始化所有服务，关闭时取消后台任务。"""
    # 确保数据目录存在
    os.makedirs(os.path.dirname(settings.DB_PATH) or ".", exist_ok=True)
    os.makedirs(settings.CHROMA_COLD_PATH, exist_ok=True)

    # 初始化 SQLite 数据库
    await init_db()

    # 预热 Embedding 模型（阻塞操作，在线程中执行）
    model = await asyncio.to_thread(SentenceTransformer, settings.EMBEDDING_MODEL)

    # 初始化各服务
    memory_svc = MemoryService(model)
    feedback_svc = FeedbackService(memory_svc)
    log_svc = LogService()
    tier_mgr = TierManager(memory_svc)
    disk_mgr = DiskManager(memory_svc)

    # 注入 MCP Server 服务依赖
    init_mcp_services(memory_svc, feedback_svc, log_svc)

    # 挂载服务到 app.state
    app.state.memory_service = memory_svc
    app.state.feedback_service = feedback_svc
    app.state.log_service = log_svc
    app.state.tier_manager = tier_mgr
    app.state.disk_manager = disk_mgr

    # 恢复热层记忆
    await tier_mgr.restore_hot_tier()

    # 启动磁盘定期检查后台任务
    disk_task = asyncio.create_task(_disk_check_loop(disk_mgr))

    yield

    # 关闭时取消后台任务
    disk_task.cancel()
    try:
        await disk_task
    except asyncio.CancelledError:
        pass


async def _disk_check_loop(disk_mgr: DiskManager) -> None:
    """磁盘占用定期检查循环，每隔 DISK_CHECK_INTERVAL_S 秒执行一次。"""
    while True:
        await asyncio.sleep(settings.DISK_CHECK_INTERVAL_S)
        try:
            await disk_mgr.check_and_evict()
        except Exception as e:
            _logger.error("磁盘淘汰检查异常：%s", e)


app = FastAPI(
    title="AIR_Memory",
    version=APP_VERSION,
    description="AIR_Memory 后端服务 - 为 AI Agent 提供记忆存储和查询能力",
    lifespan=lifespan,
)

# CORS 配置：允许前端访问，支持通过 CORS_ORIGINS 环境变量自定义来源（逗号分隔）
CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:8080,http://127.0.0.1:8080",
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册 REST API 路由
app.include_router(router)

# 挂载 MCP Server（Streamable HTTP 传输）
app.mount("/mcp", mcp.streamable_http_app())


@app.get("/health", tags=["system"])
async def health_check() -> dict:
    """健康检查接口。"""
    return {"status": "ok"}


@app.get("/api/v1/version", tags=["system"])
async def get_version() -> dict:
    """获取系统版本号。"""
    return {"version": APP_VERSION}


# 前端静态文件服务：从环境变量获取构建产物目录，默认 frontend/dist（相对于工作目录）
# 注意：StaticFiles 挂载必须放在所有 API 路由注册之后，否则会覆盖 API 路由
STATIC_DIR = os.getenv("STATIC_DIR", "frontend/dist")

if os.path.isdir(STATIC_DIR):
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")


@app.exception_handler(StarletteHTTPException)
async def spa_fallback_handler(request, exc):
    """SPA 路由回退处理器：对 404 错误，如果不是 API 路径，则返回 index.html，
    以支持 Vue Router history 模式。API 路径和 MCP 路径仍返回标准 JSON 错误响应。
    """
    if exc.status_code == 404:
        path = request.url.path
        # /api/ 和 /mcp 路径返回标准 404 JSON 响应
        if not path.startswith("/api/") and not path.startswith("/mcp"):
            if STATIC_DIR and os.path.isdir(STATIC_DIR):
                index_path = os.path.join(STATIC_DIR, "index.html")
                if os.path.isfile(index_path):
                    return FileResponse(index_path)
    # 其他情况返回标准 HTTP 错误响应
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )
