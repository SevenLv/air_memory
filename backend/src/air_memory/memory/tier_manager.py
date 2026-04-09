"""分级存储管理器，负责热层内存预算和启动时恢复热层。"""

import aiosqlite

from air_memory.config import settings


class TierManager:
    """管理热层内存预算，启动时从 SQLite 按 value_score 批量加载热层。"""

    def __init__(self, memory_service: "MemoryService") -> None:  # noqa: F821
        from air_memory.memory.service import MemoryService  # 延迟导入避免循环
        self._memory_service: MemoryService = memory_service

    async def restore_hot_tier(self) -> None:
        """启动时从 SQLite 读取 value_score，按分值排序将高价值记忆批量加载至热层。"""
        async with aiosqlite.connect(settings.DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT memory_id, value_score FROM memory_values"
                " WHERE tier = 'hot' OR value_score >= ?"
                " ORDER BY value_score DESC",
                (settings.PROMOTE_THRESHOLD,),
            ) as cursor:
                rows = await cursor.fetchall()

        for row in rows:
            # 检查热层内存预算
            if self._memory_service.get_hot_memory_mb() >= settings.HOT_MEMORY_BUDGET_MB:
                break
            await self._memory_service.promote(row["memory_id"], row["value_score"])

    async def check_memory_budget(self) -> None:
        """检查热层内存预算，超出时将最低价值记忆降级至冷层。"""
        from air_memory.memory.service import MemoryService  # noqa: F401

        if self._memory_service.get_hot_memory_mb() <= settings.HOT_MEMORY_BUDGET_MB:
            return

        # 从 SQLite 获取热层中价值最低的记忆
        async with aiosqlite.connect(settings.DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT memory_id, value_score FROM memory_values"
                " WHERE tier = 'hot' ORDER BY value_score ASC"
            ) as cursor:
                rows = await cursor.fetchall()

        for row in rows:
            if self._memory_service.get_hot_memory_mb() <= settings.HOT_MEMORY_BUDGET_MB:
                break
            await self._memory_service.demote(row["memory_id"], row["value_score"])
            # 更新 SQLite 中的 tier 字段
            async with aiosqlite.connect(settings.DB_PATH) as db:
                from datetime import datetime, timezone
                await db.execute(
                    "UPDATE memory_values SET tier = 'cold', updated_at = ? WHERE memory_id = ?",
                    (datetime.now(timezone.utc).isoformat(), row["memory_id"]),
                )
                await db.commit()

    def get_hot_stats(self) -> dict:
        """返回热层统计信息。"""
        return {
            "hot_count": self._memory_service.get_hot_count(),
            "cold_count": self._memory_service.get_cold_count(),
            "hot_memory_mb": round(self._memory_service.get_hot_memory_mb(), 2),
            "memory_budget_mb": settings.HOT_MEMORY_BUDGET_MB,
        }
