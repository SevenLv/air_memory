"""记忆相关 REST API 路由。"""

import asyncio

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from air_memory.models.feedback import FeedbackLog, FeedbackLogsResponse
from air_memory.models.memory import (
    DeleteMemoryResponse,
    MemoryFeedbackRequest,
    MemoryFeedbackResponse,
    MemoryQueryResponse,
    MemorySaveRequest,
    MemorySaveResponse,
    MemoryValueScore,
)

router = APIRouter(prefix="/memories", tags=["memories"])


def _get_memory_service(request: Request):
    return request.app.state.memory_service


def _get_feedback_service(request: Request):
    return request.app.state.feedback_service


def _get_log_service(request: Request):
    return request.app.state.log_service


@router.post("", response_model=MemorySaveResponse, status_code=201)
async def save_memory(
    body: MemorySaveRequest,
    request: Request,
):
    """存储一条记忆，初始存入冷层，返回 memory_id。"""
    memory_svc = _get_memory_service(request)
    feedback_svc = _get_feedback_service(request)
    log_svc = _get_log_service(request)
    disk_mgr = request.app.state.disk_manager

    from datetime import datetime, timezone
    import aiosqlite
    from air_memory.config import settings

    memory_id = await memory_svc.save(body.content)
    now = datetime.now(timezone.utc).isoformat()

    # 写入 memory_values 初始记录（新记忆初始进入热层）
    async with aiosqlite.connect(settings.DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO memory_values"
            " (memory_id, value_score, tier, feedback_count, created_at, updated_at)"
            " VALUES (?, ?, 'hot', 0, ?, ?)",
            (memory_id, settings.INITIAL_VALUE_SCORE, now, now),
        )
        await db.commit()

    # 异步写入存储日志
    asyncio.create_task(log_svc.log_save(body.content, memory_id))
    # 异步触发磁盘检查
    asyncio.create_task(disk_mgr.check_and_evict())

    return MemorySaveResponse(memory_id=memory_id, tier="hot")


@router.get("", response_model=MemoryQueryResponse)
async def query_memories(
    request: Request,
    query: str = Query(..., min_length=1, description="查询文本"),
    top_k: int = Query(default=5, ge=1, le=100, description="返回条数"),
    fast_only: bool = Query(default=False, description="是否仅查询热层"),
):
    """查询相关记忆，支持快速（热层）和深度（热层+冷层）两种模式。"""
    memory_svc = _get_memory_service(request)
    log_svc = _get_log_service(request)

    memories = await memory_svc.query(query, top_k, fast_only)
    query_mode = "fast" if fast_only else "deep"

    # 异步写入查询日志
    results_for_log = [m.model_dump() for m in memories]
    asyncio.create_task(log_svc.log_query(query, results_for_log, fast_only))

    return MemoryQueryResponse(
        memories=memories,
        count=len(memories),
        query_mode=query_mode,
    )


@router.delete("/{memory_id}", response_model=DeleteMemoryResponse)
async def delete_memory(
    memory_id: str,
    request: Request,
):
    """从热层、冷层 ChromaDB 及 SQLite 关联表中删除指定记忆的所有数据。"""
    import aiosqlite
    from air_memory.config import settings

    memory_svc = _get_memory_service(request)

    # 删除 ChromaDB 数据
    await memory_svc.delete(memory_id)

    # 删除 SQLite 关联数据
    async with aiosqlite.connect(settings.DB_PATH) as db:
        await db.execute(
            "UPDATE save_logs SET memory_deleted = 1 WHERE memory_id = ?",
            (memory_id,),
        )
        await db.execute("DELETE FROM feedback_logs WHERE memory_id = ?", (memory_id,))
        await db.execute("DELETE FROM memory_values WHERE memory_id = ?", (memory_id,))
        await db.commit()

    return DeleteMemoryResponse()


@router.post("/{memory_id}/feedback", response_model=MemoryFeedbackResponse)
async def feedback_memory(
    memory_id: str,
    body: MemoryFeedbackRequest,
    request: Request,
):
    """提交记忆价值反馈，更新 value_score，触发层间迁移。"""
    feedback_svc = _get_feedback_service(request)

    try:
        value_score, tier = await feedback_svc.submit(memory_id, body.valuable)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return MemoryFeedbackResponse(
        memory_id=memory_id,
        value_score=value_score,
        tier=tier,
    )


@router.get("/{memory_id}/feedback/logs", response_model=FeedbackLogsResponse)
async def get_feedback_logs(
    memory_id: str,
    request: Request,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    """查询指定记忆的反馈历史。"""
    feedback_svc = _get_feedback_service(request)
    logs = await feedback_svc.get_feedback_logs(memory_id, page, page_size)
    return FeedbackLogsResponse(logs=logs, count=len(logs))


@router.get("/{memory_id}/value-score", response_model=MemoryValueScore)
async def get_value_score(
    memory_id: str,
    request: Request,
):
    """查询指定记忆当前价值评分。"""
    feedback_svc = _get_feedback_service(request)
    data = await feedback_svc.get_memory_value_score(memory_id)
    if data is None:
        raise HTTPException(status_code=404, detail=f"记忆不存在：{memory_id}")
    return MemoryValueScore(**data)
