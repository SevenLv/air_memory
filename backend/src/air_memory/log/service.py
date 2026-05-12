"""操作日志服务模块，使用 aiosqlite 异步写入 SQLite。"""

import json
from datetime import datetime, timezone

import aiosqlite

from air_memory.config import settings
from air_memory.models.log import QueryLog, SaveLog


def _now_iso() -> str:
    """返回当前 UTC 时间的 ISO 8601 字符串。"""
    return datetime.now(timezone.utc).isoformat()


def _is_garbled(content: str) -> bool:
    """检测内容是否疑似乱码。"""
    if not content:
        return False
    length = len(content)
    if length < 2:
        return False
    question_count = content.count('?')
    question_ratio = question_count / length
    has_non_ascii = any(not c.isascii() for c in content)
    if not has_non_ascii and question_ratio > 0.5:
        return True
    if has_non_ascii and question_ratio > 0.3:
        return True
    return False


class LogService:
    """操作日志服务，负责记录存储和查询操作日志。"""

    async def log_save(self, content: str, memory_id: str) -> None:
        """异步写入存储操作日志。"""
        if content and _is_garbled(content):
            import logging as _log
            _log.getLogger(__name__).warning(
                "save_log 内容疑似乱码，memory_id=%s", memory_id,
            )
        async with aiosqlite.connect(settings.DB_PATH) as db:
            await db.execute(
                "INSERT INTO save_logs (memory_id, content, created_at, memory_deleted)"
                " VALUES (?, ?, ?, 0)",
                (memory_id, content, _now_iso()),
            )
            await db.commit()

    async def log_query(
        self, input_id: str, query: str, results: list
    ) -> None:
        """异步写入查询操作日志（含 input_id）。"""
        async with aiosqlite.connect(settings.DB_PATH) as db:
            await db.execute(
                "INSERT INTO query_logs (input_id, query, results, created_at)"
                " VALUES (?, ?, ?, ?)",
                (input_id, query, json.dumps(results, ensure_ascii=False), _now_iso()),
            )
            await db.commit()

    async def get_save_logs(self) -> list[SaveLog]:
        """查询所有存储操作日志（按 id 降序）。"""
        async with aiosqlite.connect(settings.DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT s.id, s.memory_id, s.content, s.created_at, s.memory_deleted,"
                " COALESCE(agg.total_score, NULL) AS total_association_score"
                " FROM save_logs s"
                " LEFT JOIN ("
                "   SELECT memory_id, SUM(association_score) AS total_score"
                "   FROM input_memory_links GROUP BY memory_id"
                " ) agg ON agg.memory_id = s.memory_id"
                " ORDER BY s.id DESC"
            ) as cursor:
                rows = await cursor.fetchall()
        return [
            SaveLog(
                id=row["id"],
                memory_id=row["memory_id"],
                content=row["content"],
                created_at=row["created_at"],
                memory_deleted=bool(row["memory_deleted"]),
                total_association_score=row["total_association_score"],
                is_garbled=_is_garbled(row["content"]),
            )
            for row in rows
        ]

    async def get_save_log(self, memory_id: str) -> SaveLog | None:
        """查询指定 memory_id 的最新一条存储日志。"""
        async with aiosqlite.connect(settings.DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT s.id, s.memory_id, s.content, s.created_at, s.memory_deleted,"
                " COALESCE(agg.total_score, NULL) AS total_association_score"
                " FROM save_logs s"
                " LEFT JOIN ("
                "   SELECT memory_id, SUM(association_score) AS total_score"
                "   FROM input_memory_links GROUP BY memory_id"
                " ) agg ON agg.memory_id = s.memory_id"
                " WHERE s.memory_id = ? ORDER BY s.id DESC LIMIT 1",
                (memory_id,),
            ) as cursor:
                row = await cursor.fetchone()
        if row is None:
            return None
        return SaveLog(
            id=row["id"],
            memory_id=row["memory_id"],
            content=row["content"],
            created_at=row["created_at"],
            memory_deleted=bool(row["memory_deleted"]),
            total_association_score=row["total_association_score"],
            is_garbled=_is_garbled(row["content"]),
        )

    async def get_query_logs(self) -> list[QueryLog]:
        """查询所有查询操作日志（按 id 降序）。"""
        async with aiosqlite.connect(settings.DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT id, input_id, query, results, created_at"
                " FROM query_logs ORDER BY id DESC"
            ) as cursor:
                rows = await cursor.fetchall()
        return [
            QueryLog(
                id=row["id"],
                input_id=row["input_id"],
                query=row["query"],
                results=row["results"],
                created_at=row["created_at"],
            )
            for row in rows
        ]
