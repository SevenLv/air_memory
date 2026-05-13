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
    """存储一条记忆，初始存入热层和冷层，返回 memory_id。"""
    memory_svc = _get_memory_service(request)
    log_svc = _get_log_service(request)
    disk_mgr = request.app.state.disk_manager

    memory_id = await memory_svc.save(body.content)

    # 异步写入存储日志
    asyncio.create_task(log_svc.log_save(body.content, memory_id))
    # 异步触发磁盘检查
    asyncio.create_task(disk_mgr.check_and_evict())

    return MemorySaveResponse(memory_id=memory_id, tier="hot")


@router.get("", response_model=MemoryQueryResponse)
async def query_memories(
    request: Request,
    query: str = Query(..., min_length=1, description="查询文本"),
    top_k: int = Query(default=10, ge=1, le=10, description="返回条数（最大10）"),
):
    """查询相关记忆，统一执行溢出填充配额检索。"""
    memory_svc = _get_memory_service(request)
    log_svc = _get_log_service(request)

    input_id, memories = await memory_svc.query(query, top_k)

    # 异步写入查询日志
    results_for_log = [m.model_dump() for m in memories]
    asyncio.create_task(log_svc.log_query(input_id, query, results_for_log))

    return MemoryQueryResponse(
        input_id=input_id,
        memories=memories,
        count=len(memories),
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
        await db.execute(
            "DELETE FROM feedback_logs WHERE memory_id = ?",
            (memory_id,),
        )
        await db.execute(
            "DELETE FROM input_memory_links WHERE memory_id = ?",
            (memory_id,),
        )
        await db.commit()

    return DeleteMemoryResponse()


@router.post("/{memory_id}/feedback", response_model=MemoryFeedbackResponse)
async def feedback_memory(
    memory_id: str,
    body: MemoryFeedbackRequest,
    request: Request,
):
    """提交记忆价值反馈，更新关联评分，触发层间迁移。"""
    feedback_svc = _get_feedback_service(request)

    try:
        await feedback_svc.submit(body.input_id, memory_id, body.valuable)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return MemoryFeedbackResponse(memory_id=memory_id)


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
