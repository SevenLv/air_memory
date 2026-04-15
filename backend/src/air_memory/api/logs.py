"""日志查询 REST API 路由。"""

from fastapi import APIRouter, HTTPException, Query, Request

from air_memory.models.feedback import FeedbackLogsWithTotalResponse
from air_memory.models.log import QueryLogsResponse, SaveLog, SaveLogsResponse

router = APIRouter(prefix="/logs", tags=["logs"])


@router.get("/save", response_model=SaveLogsResponse)
async def get_save_logs(request: Request):
    """查询所有存储操作日志。"""
    log_svc = request.app.state.log_service
    logs = await log_svc.get_save_logs()
    return SaveLogsResponse(logs=logs, count=len(logs))


@router.get("/save/{memory_id}", response_model=SaveLog)
async def get_save_log(memory_id: str, request: Request):
    """查询指定记忆的最新存储日志。"""
    log_svc = request.app.state.log_service
    log = await log_svc.get_save_log(memory_id)
    if log is None:
        raise HTTPException(status_code=404, detail=f"记忆不存在：{memory_id}")
    return log


@router.get("/query", response_model=QueryLogsResponse)
async def get_query_logs(request: Request):
    """查询所有查询操作日志。"""
    log_svc = request.app.state.log_service
    logs = await log_svc.get_query_logs()
    return QueryLogsResponse(logs=logs, count=len(logs))


@router.get("/feedback", response_model=FeedbackLogsWithTotalResponse)
async def get_feedback_logs(
    request: Request,
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页条数"),
    memory_id: str | None = Query(default=None, description="记忆 ID 过滤"),
    start_time: str | None = Query(default=None, description="开始时间（ISO 8601）"),
    end_time: str | None = Query(default=None, description="结束时间（ISO 8601）"),
):
    """查询反馈记录列表，支持时间段、记忆 ID 过滤和分页。"""
    feedback_svc = request.app.state.feedback_service
    logs, total = await feedback_svc.get_all_feedback_logs(
        page=page,
        page_size=page_size,
        memory_id=memory_id,
        start_time=start_time,
        end_time=end_time,
    )
    return FeedbackLogsWithTotalResponse(logs=logs, count=len(logs), total=total)
