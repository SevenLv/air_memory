"""磁盘容量管理模块，监控冷层磁盘占用并自动淘汰低价值最旧数据。"""

import os
from datetime import datetime, timezone

import aiosqlite

from air_memory.config import settings


def _now_iso() -> str:
    """返回当前 UTC 时间的 ISO 8601 字符串。"""
    return datetime.now(timezone.utc).isoformat()


class DiskManager:
    """磁盘容量管理器，监控冷层 ChromaDB 和 SQLite 磁盘占用，触发淘汰策略。"""

    def __init__(self, memory_service: "MemoryService") -> None:  # noqa: F821
        from air_memory.memory.service import MemoryService  # 延迟导入避免循环
        self._memory_service: MemoryService = memory_service

    def get_disk_usage_gb(self) -> float:
        """计算冷层 ChromaDB 数据目录及 SQLite 文件的当前磁盘占用（GB）。"""
        total_bytes = 0

        # 冷层 ChromaDB 数据目录
        if os.path.exists(settings.CHROMA_COLD_PATH):
            for dirpath, _, filenames in os.walk(settings.CHROMA_COLD_PATH):
                for filename in filenames:
                    fp = os.path.join(dirpath, filename)
                    try:
                        total_bytes += os.path.getsize(fp)
                    except OSError:
                        pass

        # SQLite 数据库文件
        if os.path.exists(settings.DB_PATH):
            try:
                total_bytes += os.path.getsize(settings.DB_PATH)
            except OSError:
                pass

        return total_bytes / (1024 ** 3)

    def get_disk_stats(self) -> dict:
        """返回磁盘占用统计信息。"""
        return {
            "disk_used_gb": round(self.get_disk_usage_gb(), 4),
            "disk_budget_gb": settings.DISK_MAX_GB,
            "disk_trigger_gb": settings.DISK_TRIGGER_GB,
            "disk_safe_gb": settings.DISK_SAFE_GB,
        }

    async def check_and_evict(self) -> None:
        """检查磁盘占用，若超过触发水位则淘汰低价值最旧数据，直至降至安全水位以下。"""
        if self.get_disk_usage_gb() <= settings.DISK_TRIGGER_GB:
            return

        while self.get_disk_usage_gb() > settings.DISK_SAFE_GB:
            # 从 SQLite 获取候选淘汰记忆（排除 168 小时内的记忆）
            candidates = await self._get_evict_candidates(batch_size=10)
            if not candidates:
                # 无可淘汰记忆（保护规则生效）
                break

            for memory_id in candidates:
                await self._evict(memory_id)

            if self.get_disk_usage_gb() <= settings.DISK_SAFE_GB:
                break

    async def _get_evict_candidates(self, batch_size: int = 10) -> list[str]:
        """获取满足淘汰条件的记忆 ID 列表。

        条件：创建时间超过 MEMORY_PROTECT_HOURS，按 value_score ASC, created_at ASC 排序。

        注意：created_at 由 _now_iso() 写入，格式为 ISO 8601（如 2026-04-08T10:30:00.123456+00:00）；
        而 SQLite 的 datetime('now', ...) 返回格式为 2026-04-08 10:30:00（空格分隔，无微秒）。
        两种格式在第 10 个字符处发生差异（'T' vs ' '），SQLite 按词典序比较时 'T' > ' '，
        导致同日期边界的记忆被错误保护，无法被淘汰。

        修复方案：使用 substr(created_at, 1, 19) 截取前 19 位去掉微秒和时区，
        再用 replace(..., 'T', ' ') 将 'T' 替换为空格，最终用 datetime() 包裹确保
        SQLite 以 datetime 语义进行比较，从而与 datetime('now', ?) 格式完全一致。
        """
        async with aiosqlite.connect(settings.DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT memory_id FROM memory_values"
                " WHERE datetime(replace(substr(created_at, 1, 19), 'T', ' ')) < datetime('now', ?)"
                " ORDER BY value_score ASC, created_at ASC LIMIT ?",
                (f"-{settings.MEMORY_PROTECT_HOURS} hours", batch_size),
            ) as cursor:
                rows = await cursor.fetchall()
        return [row["memory_id"] for row in rows]

    async def _evict(self, memory_id: str) -> None:
        """从冷层 ChromaDB 和 SQLite 相关表中删除指定记忆的所有数据。"""
        # 从冷层 ChromaDB 删除
        from air_memory.memory.service import MemoryService  # noqa: F401
        await self._memory_service.delete(memory_id)

        now = _now_iso()
        async with aiosqlite.connect(settings.DB_PATH) as db:
            # 标记 save_logs 为已删除（保留日志记录完整性）
            await db.execute(
                "UPDATE save_logs SET memory_deleted = 1 WHERE memory_id = ?",
                (memory_id,),
            )
            # 删除反馈日志
            await db.execute(
                "DELETE FROM feedback_logs WHERE memory_id = ?",
                (memory_id,),
            )
            # 删除价值评分记录
            await db.execute(
                "DELETE FROM memory_values WHERE memory_id = ?",
                (memory_id,),
            )
            await db.commit()
