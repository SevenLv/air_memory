"""管理 REST API 路由，提供分级存储和磁盘占用统计。"""

from fastapi import APIRouter, Request

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/tier-stats")
async def get_tier_stats(request: Request):
    """查询热层/冷层分级存储统计信息。"""
    tier_mgr = request.app.state.tier_manager
    return tier_mgr.get_hot_stats()


@router.get("/disk-stats")
async def get_disk_stats(request: Request):
    """查询磁盘占用统计信息。"""
    disk_mgr = request.app.state.disk_manager
    return disk_mgr.get_disk_stats()
