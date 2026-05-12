"""分级存储管理器，负责热层内存预算和启动时恢复热层。"""

import asyncio

import aiosqlite

from air_memory.config import settings


def _in_placeholders(ids: list) -> str:
    """生成 SQL IN 子句所需的参数占位符字符串（如 '?,?,?'）。

    占位符只包含 '?' 字符，不含任何用户数据，配合参数化查询使用，安全无注入风险。
    """
    return ",".join("?" * len(ids))


class TierManager:
    """管理热层内存预算，启动时从 ChromaDB + SQLite 按 total_association_score 加载热层。"""

    def __init__(self, memory_service: "MemoryService") -> None:  # noqa: F821
        from air_memory.memory.service import MemoryService  # 延迟导入避免循环
        self._memory_service: MemoryService = memory_service

    async def restore_hot_tier(self) -> None:
        """启动时从冷层恢复热层：按 total_association_score 降序加载，不超过内存预算。"""
        # 获取冷层所有记忆 ID
        cold_ids = await asyncio.to_thread(self._memory_service.get_all_cold_ids)
        if not cold_ids:
            return

        # 从 SQLite 获取每个记忆的 total_association_score
        scores = await self._get_scores_for_ids(cold_ids)

        # 获取冷层元数据（tier 字段用于优先排序）
        metadatas = await asyncio.to_thread(
            self._memory_service.get_cold_metadata, cold_ids
        )
        meta_map = {mid: (meta or {}) for mid, meta in zip(cold_ids, metadatas)}

        # 排序：先按 tier='hot' 优先（关机前在热层），再按 total_association_score DESC
        def sort_key(mid: str):
            meta = meta_map.get(mid, {})
            tier_priority = 0 if meta.get("tier") == "hot" else 1
            score = scores.get(mid, 0.0)
            return (tier_priority, -score)

        sorted_ids = sorted(cold_ids, key=sort_key)

        for memory_id in sorted_ids:
            if self._memory_service.get_hot_memory_mb() >= settings.HOT_MEMORY_BUDGET_MB:
                break
            await self._memory_service.promote(memory_id)

    async def check_memory_budget(self) -> None:
        """检查热层内存预算，超出时将最低关联评分记忆降级至冷层。"""
        if self._memory_service.get_hot_memory_mb() <= settings.HOT_MEMORY_BUDGET_MB:
            return

        # 获取热层所有记忆 ID
        hot_ids = await asyncio.to_thread(self._memory_service.get_all_hot_ids)
        if not hot_ids:
            return

        # 获取每个记忆的 total_association_score
        scores = await self._get_scores_for_ids(hot_ids)

        # 驱逐顺序：total_association_score 低的优先驱逐（分数相同时按 ID 稳定排序）
        sorted_ids = sorted(hot_ids, key=lambda mid: (scores.get(mid, 0.0), mid))

        for memory_id in sorted_ids:
            if self._memory_service.get_hot_memory_mb() <= settings.HOT_MEMORY_BUDGET_MB:
                break
            await self._memory_service.demote(memory_id)

    def get_hot_stats(self) -> dict:
        """返回热层统计信息。"""
        return {
            "hot_count": self._memory_service.get_hot_count(),
            "cold_count": self._memory_service.get_cold_count(),
            "hot_memory_mb": round(self._memory_service.get_hot_memory_mb(), 2),
            "memory_budget_mb": settings.HOT_MEMORY_BUDGET_MB,
        }

    # ------------------------------------------------------------------
    # 私有辅助方法
    # ------------------------------------------------------------------

    async def _get_scores_for_ids(self, memory_ids: list[str]) -> dict[str, float]:
        """批量查询 total_association_score。"""
        if not memory_ids:
            return {}
        ph = _in_placeholders(memory_ids)
        async with aiosqlite.connect(settings.DB_PATH) as db:
            async with db.execute(
                f"SELECT memory_id, COALESCE(SUM(association_score), 0) AS total_score"
                f" FROM input_memory_links WHERE memory_id IN ({ph})"
                f" GROUP BY memory_id",
                memory_ids,
            ) as cursor:
                rows = await cursor.fetchall()
        result = {mid: 0.0 for mid in memory_ids}
        for row in rows:
            result[row[0]] = float(row[1])
        return result
