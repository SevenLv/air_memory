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

    memory_id = await _memory_service.save(content)
    asyncio.create_task(_log_service.log_save(content, memory_id))
    return memory_id


@mcp.tool()
async def query_memory(
    query: str,
    top_k: int = 10,
) -> str:
    """查询相关记忆，统一执行溢出填充配额检索。

    Args:
        query: 查询文本。
        top_k: 返回最相关记忆的数量，默认 10，最大 10。

    Returns:
        JSON 字符串，包含 input_id 和记忆条目列表。示例结构：
        {"input_id": "...", "memories": [{"id": "...", "content": "记忆内容",
          "similarity": 0.95, "total_association_score": 2.0,
          "source": "hot", "tier": "hot", "created_at": "..."}]}
    """
    if _memory_service is None or _log_service is None:
        raise RuntimeError("MCP 服务尚未初始化，请稍后重试")

    input_id, memories = await _memory_service.query(query, top_k)
    results = [m.model_dump() for m in memories]
    asyncio.create_task(_log_service.log_query(input_id, query, results))
    return json.dumps({"input_id": input_id, "memories": results}, ensure_ascii=False)


@mcp.tool()
async def feedback_memory(input_id: str, memory_id: str, valuable: bool) -> dict:
    """对指定记忆提交价值反馈。

    Args:
        input_id: 触发本次反馈的查询 input_id（从 query_memory 返回结果中获取）。
        memory_id: 目标记忆的 ID。
        valuable: True 表示有价值，False 表示无价值。

    Returns:
        包含 memory_id 和 message 的字典。
    """
    if _feedback_service is None:
        raise RuntimeError("MCP 服务尚未初始化，请稍后重试")

    try:
        await _feedback_service.submit(input_id, memory_id, valuable)
    except ValueError as e:
        return {"error": str(e)}

    return {
        "memory_id": memory_id,
        "message": "ok",
    }
