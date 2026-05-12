"""磁盘容量管理模块，监控冷层磁盘占用并自动淘汰低关联评分最旧数据。"""

import asyncio
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

        if os.path.exists(settings.CHROMA_COLD_PATH):
            for dirpath, _, filenames in os.walk(settings.CHROMA_COLD_PATH):
                for filename in filenames:
                    fp = os.path.join(dirpath, filename)
                    try:
                        total_bytes += os.path.getsize(fp)
                    except OSError:
                        pass

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
        """检查磁盘占用，若超过触发水位则淘汰低关联评分最旧数据，直至降至安全水位以下。"""
        if self.get_disk_usage_gb() <= settings.DISK_TRIGGER_GB:
            return

        while self.get_disk_usage_gb() > settings.DISK_SAFE_GB:
            candidates = await self._get_evict_candidates(batch_size=10)
            if not candidates:
                break

            for memory_id in candidates:
                await self._evict(memory_id)

            if self.get_disk_usage_gb() <= settings.DISK_SAFE_GB:
                break

    async def _get_evict_candidates(self, batch_size: int = 10) -> list[str]:
        """获取满足淘汰条件的记忆 ID 列表。

        条件：创建时间超过 MEMORY_PROTECT_HOURS，按 total_association_score ASC, created_at ASC 排序。
        注意：从 ChromaDB 冷层获取所有 ID + 元数据，再与 SQLite 关联评分关联。
        """
        # 从冷层获取所有记忆 ID 和元数据
        cold_ids = await asyncio.to_thread(self._memory_service.get_all_cold_ids)
        if not cold_ids:
            return []

        metadatas = await asyncio.to_thread(
            self._memory_service.get_cold_metadata, cold_ids
        )

        # 筛选超过保护时长的记忆
        protect_threshold_hours = settings.MEMORY_PROTECT_HOURS
        now = datetime.now(timezone.utc)
        candidates_with_meta = []
        for mid, meta in zip(cold_ids, metadatas):
            meta = meta or {}
            created_at_str = str(meta.get("created_at", ""))
            if not created_at_str:
                continue
            try:
                # 解析 ISO 8601 格式时间戳（支持时区偏移，如 +00:00 或 +08:00）
                created_dt = datetime.fromisoformat(created_at_str)
                # 若无时区信息，假设为 UTC
                if created_dt.tzinfo is None:
                    created_dt = created_dt.replace(tzinfo=timezone.utc)
                age_hours = (now - created_dt).total_seconds() / 3600
                if age_hours >= protect_threshold_hours:
                    candidates_with_meta.append((mid, created_at_str))
            except (ValueError, TypeError):
                continue

        if not candidates_with_meta:
            return []

        candidate_ids = [mid for mid, _ in candidates_with_meta]
        # 获取关联评分
        if candidate_ids:
            placeholders = ",".join("?" * len(candidate_ids))
            async with aiosqlite.connect(settings.DB_PATH) as db:
                async with db.execute(
                    f"SELECT memory_id, COALESCE(SUM(association_score), 0) AS total_score"
                    f" FROM input_memory_links WHERE memory_id IN ({placeholders})"
                    f" GROUP BY memory_id",
                    candidate_ids,
                ) as cursor:
                    score_rows = await cursor.fetchall()
            scores = {row[0]: float(row[1]) for row in score_rows}
        else:
            scores = {}

        # 按 total_association_score ASC, created_at ASC 排序
        candidates_with_meta.sort(
            key=lambda x: (scores.get(x[0], 0.0), x[1])
        )

        return [mid for mid, _ in candidates_with_meta[:batch_size]]

    async def _evict(self, memory_id: str) -> None:
        """从冷层 ChromaDB 和 SQLite 相关表中删除指定记忆的所有数据。"""
        await self._memory_service.delete(memory_id)

        async with aiosqlite.connect(settings.DB_PATH) as db:
            await db.execute(
                "UPDATE save_logs SET memory_deleted = 1 WHERE memory_id = ?",
                (memory_id,),
            )
            await db.execute(
                "DELETE FROM feedback_logs WHERE memory_id = ?",
                (memory_id,),
            )
            await db.execute(
                "DELETE FROM input_memory_links WHERE memory_id = ?",
                (memory_id,),
            )
            await db.commit()
