"""价值反馈服务模块，更新关联评分并触发层间迁移。"""

import asyncio
from datetime import datetime, timezone

import aiosqlite

from air_memory.config import settings
from air_memory.models.feedback import FeedbackLog
from air_memory.models.input import InputDetail, InputInfo, InputMemoryLink


def _now_iso() -> str:
    """返回当前 UTC 时间的 ISO 8601 字符串。"""
    return datetime.now(timezone.utc).isoformat()


class FeedbackService:
    """价值反馈服务，负责关联评分更新、日志写入和层间迁移触发。"""

    def __init__(self, memory_service: "MemoryService") -> None:  # noqa: F821
        from air_memory.memory.service import MemoryService  # 延迟导入避免循环
        self._memory_service: MemoryService = memory_service

    async def submit(self, input_id: str, memory_id: str, valuable: bool) -> None:
        """提交反馈，更新 input_memory_links 关联评分，写入日志，触发层间迁移。"""
        now = _now_iso()
        step = settings.ASSOCIATION_SCORE_STEP

        async with aiosqlite.connect(settings.DB_PATH) as db:
            db.row_factory = aiosqlite.Row

            if valuable:
                # 建立/增加关联分
                async with db.execute(
                    "SELECT association_score FROM input_memory_links"
                    " WHERE input_id = ? AND memory_id = ?",
                    (input_id, memory_id),
                ) as cursor:
                    row = await cursor.fetchone()

                if row is None:
                    await db.execute(
                        "INSERT INTO input_memory_links"
                        " (input_id, memory_id, association_score, created_at, updated_at)"
                        " VALUES (?, ?, ?, ?, ?)",
                        (input_id, memory_id, step, now, now),
                    )
                else:
                    new_score = float(row["association_score"]) + step
                    await db.execute(
                        "UPDATE input_memory_links SET association_score = ?, updated_at = ?"
                        " WHERE input_id = ? AND memory_id = ?",
                        (new_score, now, input_id, memory_id),
                    )
            else:
                # 减少关联分，降至 0 时删除记录
                async with db.execute(
                    "SELECT association_score FROM input_memory_links"
                    " WHERE input_id = ? AND memory_id = ?",
                    (input_id, memory_id),
                ) as cursor:
                    row = await cursor.fetchone()

                if row is not None:
                    new_score = float(row["association_score"]) - step
                    if new_score <= 0:
                        await db.execute(
                            "DELETE FROM input_memory_links"
                            " WHERE input_id = ? AND memory_id = ?",
                            (input_id, memory_id),
                        )
                    else:
                        await db.execute(
                            "UPDATE input_memory_links SET association_score = ?, updated_at = ?"
                            " WHERE input_id = ? AND memory_id = ?",
                            (new_score, now, input_id, memory_id),
                        )

            # 写入 feedback_logs（含 input_id）
            await db.execute(
                "INSERT INTO feedback_logs (input_id, memory_id, valuable, created_at)"
                " VALUES (?, ?, ?, ?)",
                (input_id, memory_id, int(valuable), now),
            )
            await db.commit()

        # 重新计算 total_association_score 并触发层间迁移
        total_score = await self._get_total_association_score(memory_id)
        await self._maybe_migrate(memory_id, total_score)

    async def get_feedback_logs(
        self, memory_id: str, page: int = 1, page_size: int = 20
    ) -> list[FeedbackLog]:
        """查询指定记忆的反馈历史。"""
        offset = (page - 1) * page_size
        async with aiosqlite.connect(settings.DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT id, input_id, memory_id, valuable, created_at FROM feedback_logs"
                " WHERE memory_id = ? ORDER BY id DESC LIMIT ? OFFSET ?",
                (memory_id, page_size, offset),
            ) as cursor:
                rows = await cursor.fetchall()
        return [
            FeedbackLog(
                id=row["id"],
                input_id=row["input_id"],
                memory_id=row["memory_id"],
                valuable=bool(row["valuable"]),
                created_at=row["created_at"],
            )
            for row in rows
        ]

    async def get_all_feedback_logs(
        self,
        page: int = 1,
        page_size: int = 20,
        memory_id: str | None = None,
        input_id: str | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
    ) -> tuple[list[FeedbackLog], int]:
        """查询所有反馈记录（支持时间段、记忆 ID、input_id 过滤和分页）。"""
        offset = (page - 1) * page_size

        conditions = []
        params: list = []
        if memory_id:
            conditions.append("memory_id = ?")
            params.append(memory_id)
        if input_id:
            conditions.append("input_id = ?")
            params.append(input_id)
        if start_time:
            conditions.append("created_at >= ?")
            params.append(start_time)
        if end_time:
            conditions.append("created_at <= ?")
            params.append(end_time)

        where_clause = ("WHERE " + " AND ".join(conditions)) if conditions else ""

        async with aiosqlite.connect(settings.DB_PATH) as db:
            db.row_factory = aiosqlite.Row

            count_sql = f"SELECT COUNT(*) as total FROM feedback_logs {where_clause}"
            async with db.execute(count_sql, params) as cursor:
                row = await cursor.fetchone()
            total = row["total"] if row else 0

            data_sql = (
                f"SELECT id, input_id, memory_id, valuable, created_at FROM feedback_logs"
                f" {where_clause} ORDER BY id DESC LIMIT ? OFFSET ?"
            )
            data_params = params + [page_size, offset]
            async with db.execute(data_sql, data_params) as cursor:
                rows = await cursor.fetchall()

        logs = [
            FeedbackLog(
                id=row["id"],
                input_id=row["input_id"],
                memory_id=row["memory_id"],
                valuable=bool(row["valuable"]),
                created_at=row["created_at"],
            )
            for row in rows
        ]
        return logs, total

    async def list_inputs(
        self,
        page: int = 1,
        page_size: int = 20,
        start_time: str | None = None,
        end_time: str | None = None,
    ) -> tuple[list[InputInfo], int]:
        """分页查询 input_infos。"""
        offset = (page - 1) * page_size
        conditions = []
        params: list = []
        if start_time:
            conditions.append("created_at >= ?")
            params.append(start_time)
        if end_time:
            conditions.append("created_at <= ?")
            params.append(end_time)
        where_clause = ("WHERE " + " AND ".join(conditions)) if conditions else ""

        async with aiosqlite.connect(settings.DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                f"SELECT COUNT(*) as total FROM input_infos {where_clause}", params
            ) as cursor:
                row = await cursor.fetchone()
            total = row["total"] if row else 0

            async with db.execute(
                f"SELECT input_id, query, created_at FROM input_infos {where_clause}"
                f" ORDER BY created_at DESC LIMIT ? OFFSET ?",
                params + [page_size, offset],
            ) as cursor:
                rows = await cursor.fetchall()

        inputs = [
            InputInfo(
                input_id=row["input_id"],
                query=row["query"],
                created_at=row["created_at"],
            )
            for row in rows
        ]
        return inputs, total

    async def get_input_detail(self, input_id: str) -> InputDetail | None:
        """查询输入详情（含关联记忆及其评分）。"""
        async with aiosqlite.connect(settings.DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT input_id, query, created_at FROM input_infos WHERE input_id = ?",
                (input_id,),
            ) as cursor:
                info_row = await cursor.fetchone()

            if info_row is None:
                return None

            async with db.execute(
                "SELECT iml.memory_id, iml.association_score,"
                " COALESCE(agg.total_score, 0) AS total_association_score"
                " FROM input_memory_links iml"
                " LEFT JOIN ("
                "   SELECT memory_id, SUM(association_score) AS total_score"
                "   FROM input_memory_links GROUP BY memory_id"
                " ) agg ON iml.memory_id = agg.memory_id"
                " WHERE iml.input_id = ?"
                " ORDER BY iml.association_score DESC",
                (input_id,),
            ) as cursor:
                link_rows = await cursor.fetchall()

        memories = [
            InputMemoryLink(
                memory_id=row["memory_id"],
                association_score=float(row["association_score"]),
                total_association_score=float(row["total_association_score"]),
            )
            for row in link_rows
        ]

        return InputDetail(
            input_id=info_row["input_id"],
            query=info_row["query"],
            created_at=info_row["created_at"],
            memories=memories,
        )

    # ------------------------------------------------------------------
    # 私有辅助方法
    # ------------------------------------------------------------------

    async def _get_total_association_score(self, memory_id: str) -> float:
        """计算指定记忆的 total_association_score。"""
        async with aiosqlite.connect(settings.DB_PATH) as db:
            async with db.execute(
                "SELECT COALESCE(SUM(association_score), 0) AS total"
                " FROM input_memory_links WHERE memory_id = ?",
                (memory_id,),
            ) as cursor:
                row = await cursor.fetchone()
        return float(row[0]) if row else 0.0

    async def _maybe_migrate(self, memory_id: str, total_score: float) -> None:
        """根据 total_association_score 决定是否触发层间迁移。"""
        is_hot = await self._memory_service.is_hot(memory_id)
        if total_score >= settings.PROMOTE_THRESHOLD and not is_hot:
            asyncio.create_task(self._promote(memory_id))
        elif total_score < settings.DEMOTE_THRESHOLD and is_hot:
            asyncio.create_task(self._demote(memory_id))

    async def _promote(self, memory_id: str) -> None:
        """异步将记忆从冷层升级至热层。"""
        await self._memory_service.promote(memory_id)

    async def _demote(self, memory_id: str) -> None:
        """异步将记忆从热层降级至冷层。"""
        await self._memory_service.demote(memory_id)
