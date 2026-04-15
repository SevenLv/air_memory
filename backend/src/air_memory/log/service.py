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
    """检测内容是否疑似乱码（CP1252 问号损坏或其他编码损坏）。

    场景一：纯 ???? 模式（CP1252 编码失败，中文 → 纯 ASCII 问号）
      - 内容全为 ASCII，但问号占比 > 50%，且长度 >= 2
    场景二：混合模式（含非 ASCII 字符，且问号占比 > 30%）
    """
    if not content:
        return False
    length = len(content)
    if length < 2:
        return False
    question_count = content.count('?')
    question_ratio = question_count / length
    # 场景一：纯 ASCII 问号（CP1252 损坏）
    has_non_ascii = any(not c.isascii() for c in content)
    if not has_non_ascii and question_ratio > 0.5:
        return True
    # 场景二：混合乱码（含非 ASCII 且高问号占比）
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
                "save_log 内容疑似乱码（问号比例过高），"
                "请确认 start 脚本中 PYTHONUTF8=1 已正确生效。memory_id=%s",
                memory_id,
            )
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
                is_garbled=_is_garbled(row["content"]),
            )
            for row in rows
        ]

    async def get_save_log(self, memory_id: str) -> SaveLog | None:
        """查询指定 memory_id 的最新一条存储日志。"""
        async with aiosqlite.connect(settings.DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT id, memory_id, content, created_at, memory_deleted"
                " FROM save_logs WHERE memory_id = ? ORDER BY id DESC LIMIT 1",
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
            is_garbled=_is_garbled(row["content"]),
        )

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
