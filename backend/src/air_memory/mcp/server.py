"""MCP Server 模块，使用 mcp Python SDK 暴露记忆存储、查询和反馈工具。"""

import asyncio
import json
from typing import TYPE_CHECKING

from mcp.server.fastmcp import FastMCP

if TYPE_CHECKING:
    from air_memory.feedback.service import FeedbackService
    from air_memory.log.service import LogService
    from air_memory.memory.service import MemoryService

# 模块级服务引用，由 main.py lifespan 初始化后注入
_memory_service: "MemoryService | None" = None
_feedback_service: "FeedbackService | None" = None
_log_service: "LogService | None" = None

mcp = FastMCP("AIR_Memory")


def init_mcp_services(
    memory_svc: "MemoryService",
    feedback_svc: "FeedbackService",
    log_svc: "LogService",
) -> None:
    """注入服务依赖（由 main.py 在 lifespan 启动阶段调用）。"""
    global _memory_service, _feedback_service, _log_service
    _memory_service = memory_svc
    _feedback_service = feedback_svc
    _log_service = log_svc


@mcp.tool()
async def save_memory(content: str) -> str:
    """存储一条记忆，返回 memory_id。

    Args:
        content: 记忆内容文本。

    Returns:
        memory_id 字符串。
    """
    if _memory_service is None or _log_service is None:
        raise RuntimeError("MCP 服务尚未初始化，请稍后重试")

    import aiosqlite
    from datetime import datetime, timezone
    from air_memory.config import settings

    memory_id = await _memory_service.save(content)
    now = datetime.now(timezone.utc).isoformat()

    async with aiosqlite.connect(settings.DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO memory_values"
            " (memory_id, value_score, tier, feedback_count, created_at, updated_at)"
            " VALUES (?, ?, 'hot', 0, ?, ?)",  # 记忆已写入热层，tier 应为 hot
            (memory_id, settings.INITIAL_VALUE_SCORE, now, now),
        )
        await db.commit()

    asyncio.create_task(_log_service.log_save(content, memory_id))
    return memory_id


@mcp.tool()
async def query_memory(
    query: str,
    top_k: int = 5,
    fast_only: bool = False,
) -> str:
    """查询相关记忆。

    Args:
        query: 查询文本。
        top_k: 返回最相关记忆的数量，默认 5。
        fast_only: 为 True 时仅检索热层（≤ 100ms），为 False 时同时检索热层和冷层。

    Returns:
        JSON 字符串，包含记忆条目列表，每条包含 id, content, similarity, value_score, tier, created_at。
    """
    if _memory_service is None or _log_service is None:
        raise RuntimeError("MCP 服务尚未初始化，请稍后重试")

    memories = await _memory_service.query(query, top_k, fast_only)
    results = [m.model_dump() for m in memories]
    asyncio.create_task(_log_service.log_query(query, results, fast_only))
    # 返回整体 JSON 字符串，避免 MCP SDK 将 list[dict] 拆分为多个 TextContent 块
    # ensure_ascii=False 确保中文字符直接输出，而非 \uXXXX 转义
    return json.dumps(results, ensure_ascii=False)


@mcp.tool()
async def feedback_memory(memory_id: str, valuable: bool) -> dict:
    """对指定记忆提交价值反馈。

    Args:
        memory_id: 目标记忆的 ID。
        valuable: True 表示有价值，False 表示无价值。

    Returns:
        包含 memory_id, value_score, tier 的字典。
    """
    if _feedback_service is None:
        raise RuntimeError("MCP 服务尚未初始化，请稍后重试")

    try:
        value_score, tier = await _feedback_service.submit(memory_id, valuable)
    except ValueError as e:
        return {"error": str(e)}

    return {
        "memory_id": memory_id,
        "value_score": value_score,
        "tier": tier,
        "message": "ok",
    }
