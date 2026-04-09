"""操作日志服务模块，使用 aiosqlite 异步写入 SQLite。"""

import json
from datetime import datetime, timezone

import aiosqlite

from air_memory.config import settings
from air_memory.models.log import QueryLog, SaveLog


def _now_iso() -> str:
    """返回当前 UTC 时间的 ISO 8601 字符串。"""
    return datetime.now(timezone.utc).isoformat()


class LogService:
    """操作日志服务，负责记录存储和查询操作日志。"""

    async def log_save(self, content: str, memory_id: str) -> None:
        """异步写入存储操作日志。"""
        async with aiosqlite.connect(settings.DB_PATH) as db:
            await db.execute(
                "INSERT INTO save_logs (memory_id, content, created_at, memory_deleted)"
                " VALUES (?, ?, ?, 0)",
                (memory_id, content, _now_iso()),
            )
            await db.commit()

    async def log_query(
        self, query: str, results: list, fast_only: bool
    ) -> None:
        """异步写入查询操作日志。"""
        async with aiosqlite.connect(settings.DB_PATH) as db:
            await db.execute(
                "INSERT INTO query_logs (query, results, fast_only, created_at)"
                " VALUES (?, ?, ?, ?)",
                (query, json.dumps(results, ensure_ascii=False), int(fast_only), _now_iso()),
            )
            await db.commit()

    async def get_save_logs(self) -> list[SaveLog]:
        """查询所有存储操作日志（按 id 降序）。"""
        async with aiosqlite.connect(settings.DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT id, memory_id, content, created_at, memory_deleted"
                " FROM save_logs ORDER BY id DESC"
            ) as cursor:
                rows = await cursor.fetchall()
        return [
            SaveLog(
                id=row["id"],
                memory_id=row["memory_id"],
                content=row["content"],
                created_at=row["created_at"],
                memory_deleted=bool(row["memory_deleted"]),
            )
            for row in rows
        ]

    async def get_query_logs(self) -> list[QueryLog]:
        """查询所有查询操作日志（按 id 降序）。"""
        async with aiosqlite.connect(settings.DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT id, query, results, fast_only, created_at"
                " FROM query_logs ORDER BY id DESC"
            ) as cursor:
                rows = await cursor.fetchall()
        return [
            QueryLog(
                id=row["id"],
                query=row["query"],
                results=row["results"],
                fast_only=bool(row["fast_only"]),
                created_at=row["created_at"],
            )
            for row in rows
        ]
