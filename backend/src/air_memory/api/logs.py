"""日志查询 REST API 路由。"""

from fastapi import APIRouter, Request

from air_memory.models.log import QueryLogsResponse, SaveLogsResponse

router = APIRouter(prefix="/logs", tags=["logs"])


@router.get("/save", response_model=SaveLogsResponse)
async def get_save_logs(request: Request):
    """查询所有存储操作日志。"""
    log_svc = request.app.state.log_service
    logs = await log_svc.get_save_logs()
    return SaveLogsResponse(logs=logs, count=len(logs))


@router.get("/query", response_model=QueryLogsResponse)
async def get_query_logs(request: Request):
    """查询所有查询操作日志。"""
    log_svc = request.app.state.log_service
    logs = await log_svc.get_query_logs()
    return QueryLogsResponse(logs=logs, count=len(logs))
