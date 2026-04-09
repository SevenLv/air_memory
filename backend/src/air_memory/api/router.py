"""API 路由注册模块。"""

from fastapi import APIRouter

from air_memory.api.admin import router as admin_router
from air_memory.api.logs import router as logs_router
from air_memory.api.memory import router as memory_router

router = APIRouter(prefix="/api/v1")

router.include_router(memory_router)
router.include_router(logs_router)
router.include_router(admin_router)
