"""价值反馈服务模块，更新记忆价值评分并触发层间迁移。"""

import asyncio
from datetime import datetime, timezone

import aiosqlite

from air_memory.config import settings
from air_memory.models.feedback import FeedbackLog


def _now_iso() -> str:
    """返回当前 UTC 时间的 ISO 8601 字符串。"""
    return datetime.now(timezone.utc).isoformat()


class FeedbackService:
    """价值反馈服务，负责价值评分更新、Feedback 日志写入和层间迁移触发。"""

    def __init__(self, memory_service: "MemoryService") -> None:  # noqa: F821
        from air_memory.memory.service import MemoryService  # 延迟导入避免循环
        self._memory_service: MemoryService = memory_service

    async def submit(self, memory_id: str, valuable: bool) -> tuple[float, str]:
        """提交反馈，更新 value_score，写入 Feedback 日志，触发层间迁移。

        返回 (value_score, tier)。
        """
        now = _now_iso()

        async with aiosqlite.connect(settings.DB_PATH) as db:
            db.row_factory = aiosqlite.Row

            # 读取当前记忆状态
            async with db.execute(
                "SELECT value_score, tier, feedback_count FROM memory_values WHERE memory_id = ?",
                (memory_id,),
            ) as cursor:
                row = await cursor.fetchone()

        if row is None:
            raise ValueError(f"记忆不存在：{memory_id}")

        old_score: float = row["value_score"]
        current_tier: str = row["tier"]
        feedback_count: int = row["feedback_count"]

        # 更新价值分
        step = settings.FEEDBACK_STEP if valuable else -settings.FEEDBACK_STEP
        new_score = round(min(1.0, max(0.0, old_score + step)), 4)
        new_count = feedback_count + 1

        async with aiosqlite.connect(settings.DB_PATH) as db:
            await db.execute(
                "UPDATE memory_values SET value_score = ?, feedback_count = ?, updated_at = ?"
                " WHERE memory_id = ?",
                (new_score, new_count, now, memory_id),
            )
            await db.execute(
                "INSERT INTO feedback_logs (memory_id, valuable, created_at) VALUES (?, ?, ?)",
                (memory_id, int(valuable), now),
            )
            await db.commit()

        # 判断层间迁移（异步后台执行）
        new_tier = current_tier
        if new_score >= settings.PROMOTE_THRESHOLD and current_tier == "cold":
            asyncio.create_task(self._promote(memory_id, new_score))
            new_tier = "hot"
        elif new_score < settings.DEMOTE_THRESHOLD and current_tier == "hot":
            asyncio.create_task(self._demote(memory_id, new_score))
            new_tier = "cold"

        return new_score, new_tier

    async def get_feedback_logs(
        self, memory_id: str, page: int = 1, page_size: int = 20
    ) -> list[FeedbackLog]:
        """查询指定记忆的反馈历史。"""
        offset = (page - 1) * page_size
        async with aiosqlite.connect(settings.DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT id, memory_id, valuable, created_at FROM feedback_logs"
                " WHERE memory_id = ? ORDER BY id DESC LIMIT ? OFFSET ?",
                (memory_id, page_size, offset),
            ) as cursor:
                rows = await cursor.fetchall()
        return [
            FeedbackLog(
                id=row["id"],
                memory_id=row["memory_id"],
                valuable=bool(row["valuable"]),
                created_at=row["created_at"],
            )
            for row in rows
        ]

    async def get_memory_value_score(self, memory_id: str) -> dict | None:
        """查询指定记忆当前综合价值评分。"""
        async with aiosqlite.connect(settings.DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT memory_id, value_score, tier, feedback_count FROM memory_values"
                " WHERE memory_id = ?",
                (memory_id,),
            ) as cursor:
                row = await cursor.fetchone()
        if row is None:
            return None
        return {
            "memory_id": row["memory_id"],
            "value_score": row["value_score"],
            "tier": row["tier"],
            "feedback_count": row["feedback_count"],
        }

    # ------------------------------------------------------------------
    # 私有辅助方法
    # ------------------------------------------------------------------

    async def _promote(self, memory_id: str, value_score: float) -> None:
        """异步将记忆从冷层升级至热层。"""
        await self._memory_service.promote(memory_id, value_score)
        async with aiosqlite.connect(settings.DB_PATH) as db:
            await db.execute(
                "UPDATE memory_values SET tier = 'hot', updated_at = ? WHERE memory_id = ?",
                (_now_iso(), memory_id),
            )
            await db.commit()

    async def _demote(self, memory_id: str, value_score: float) -> None:
        """异步将记忆从热层降级至冷层。"""
        await self._memory_service.demote(memory_id, value_score)
        async with aiosqlite.connect(settings.DB_PATH) as db:
            await db.execute(
                "UPDATE memory_values SET tier = 'cold', updated_at = ? WHERE memory_id = ?",
                (_now_iso(), memory_id),
            )
            await db.commit()
