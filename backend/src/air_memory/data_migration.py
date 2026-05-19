"""数据迁移管理器：负责执行 Schema 迁移，保证幂等性。"""

import logging
from datetime import datetime, timezone

import aiosqlite

from air_memory.config import settings

_logger = logging.getLogger(__name__)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class DataMigrationManager:
    """Schema 迁移管理器，使用 schema_migrations 表记录已执行的迁移。"""

    async def run_migrations(self) -> None:
        """按顺序执行所有待执行的迁移，幂等执行。失败时记录日志并 raise RuntimeError。"""
        try:
            await self._ensure_migrations_table()
            executed = await self._get_executed_migrations()

            migrations = [
                ("M001", self._m001_rename_memory_values),
                ("M002", self._m002_add_input_id_to_query_logs),
                ("M003", self._m003_add_input_id_to_feedback_logs),
                ("M004", self._m004_rebuild_query_logs_without_fast_only),
            ]

            for migration_id, migration_fn in migrations:
                if migration_id not in executed:
                    _logger.info("执行迁移 %s ...", migration_id)
                    await migration_fn()
                    await self._record_migration(migration_id)
                    _logger.info("迁移 %s 完成。", migration_id)
        except Exception as e:
            _logger.error("数据迁移失败：%s", e, exc_info=True)
            raise RuntimeError("数据迁移失败，请检查日志获取详细信息") from e

    async def _ensure_migrations_table(self) -> None:
        """确保 schema_migrations 表存在。"""
        async with aiosqlite.connect(settings.DB_PATH) as db:
            await db.execute(
                """CREATE TABLE IF NOT EXISTS schema_migrations (
                    migration_id TEXT PRIMARY KEY,
                    executed_at  TEXT NOT NULL
                )"""
            )
            await db.commit()

    async def _get_executed_migrations(self) -> set[str]:
        """获取已执行的迁移 ID 集合。"""
        async with aiosqlite.connect(settings.DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT migration_id FROM schema_migrations"
            ) as cursor:
                rows = await cursor.fetchall()
        return {row["migration_id"] for row in rows}

    async def _record_migration(self, migration_id: str) -> None:
        """记录已执行的迁移。"""
        async with aiosqlite.connect(settings.DB_PATH) as db:
            await db.execute(
                "INSERT OR IGNORE INTO schema_migrations (migration_id, executed_at) VALUES (?, ?)",
                (migration_id, _now_iso()),
            )
            await db.commit()

    async def _m001_rename_memory_values(self) -> None:
        """M001：将旧 memory_values 表重命名为 _legacy_memory_values（保留数据供回滚）。"""
        async with aiosqlite.connect(settings.DB_PATH) as db:
            # 检查 memory_values 表是否存在
            async with db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='memory_values'"
            ) as cursor:
                row = await cursor.fetchone()
            if row is not None:
                # 检查 _legacy_memory_values 是否已存在
                async with db.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='_legacy_memory_values'"
                ) as cursor:
                    legacy_row = await cursor.fetchone()
                if legacy_row is None:
                    await db.execute(
                        "ALTER TABLE memory_values RENAME TO _legacy_memory_values"
                    )
                    await db.commit()
                    _logger.info("M001：memory_values 已重命名为 _legacy_memory_values")
                else:
                    _logger.info("M001：_legacy_memory_values 已存在，跳过重命名")
            else:
                _logger.info("M001：memory_values 表不存在，跳过")

    async def _m002_add_input_id_to_query_logs(self) -> None:
        """M002：为 query_logs 新增 input_id 列（若不存在）。"""
        async with aiosqlite.connect(settings.DB_PATH) as db:
            async with db.execute("PRAGMA table_info(query_logs)") as cursor:
                cols = {row[1] for row in await cursor.fetchall()}
            if "input_id" not in cols:
                await db.execute(
                    "ALTER TABLE query_logs ADD COLUMN input_id TEXT"
                )
                await db.commit()
                _logger.info("M002：query_logs.input_id 列已新增")
            else:
                _logger.info("M002：query_logs.input_id 已存在，跳过")

    async def _m003_add_input_id_to_feedback_logs(self) -> None:
        """M003：为 feedback_logs 新增 input_id 列（若不存在）。"""
        async with aiosqlite.connect(settings.DB_PATH) as db:
            async with db.execute("PRAGMA table_info(feedback_logs)") as cursor:
                cols = {row[1] for row in await cursor.fetchall()}
            if "input_id" not in cols:
                await db.execute(
                    "ALTER TABLE feedback_logs ADD COLUMN input_id TEXT"
                )
                await db.commit()
                _logger.info("M003：feedback_logs.input_id 列已新增")
            else:
                _logger.info("M003：feedback_logs.input_id 已存在，跳过")

    async def _m004_rebuild_query_logs_without_fast_only(self) -> None:
        """M004：重建 query_logs，移除 legacy fast_only 列，统一为当前 schema。"""
        async with aiosqlite.connect(settings.DB_PATH) as db:
            async with db.execute("PRAGMA table_info(query_logs)") as cursor:
                col_rows = await cursor.fetchall()
            if not col_rows:
                _logger.info("M004：query_logs 表不存在，跳过")
                return

            cols = {row[1] for row in col_rows}
            if "fast_only" not in cols:
                _logger.info("M004：query_logs 无 fast_only 列，跳过")
                return

            await db.execute(
                """CREATE TABLE query_logs_new (
                    id         INTEGER PRIMARY KEY AUTOINCREMENT,
                    input_id   TEXT,
                    query      TEXT    NOT NULL,
                    results    TEXT    NOT NULL,
                    created_at TEXT    NOT NULL
                )"""
            )
            if "input_id" in cols:
                await db.execute(
                    "INSERT INTO query_logs_new (id, input_id, query, results, created_at)"
                    " SELECT id, input_id, query, results, created_at FROM query_logs"
                )
            else:
                await db.execute(
                    "INSERT INTO query_logs_new (id, input_id, query, results, created_at)"
                    " SELECT id, NULL, query, results, created_at FROM query_logs"
                )
            await db.execute("DROP TABLE query_logs")
            await db.execute("ALTER TABLE query_logs_new RENAME TO query_logs")
            await db.commit()
            _logger.info("M004：query_logs 已重建为最新 schema（移除 fast_only）")
