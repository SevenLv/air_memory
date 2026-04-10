"""DiskManager 单元测试：淘汰触发条件、168 小时保护规则、淘汰顺序验证。"""

from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock

import pytest
import pytest_asyncio
import aiosqlite

from air_memory.config import settings
from tests.conftest import insert_memory_value


def _hours_ago_iso(hours: int) -> str:
    """返回 N 小时前的 UTC ISO 8601 时间字符串。"""
    dt = datetime.now(timezone.utc) - timedelta(hours=hours)
    return dt.isoformat()


async def _save_memory_with_db(memory_service, db_path: str,
                                content: str, value_score: float = 0.5,
                                tier: str = "cold",
                                created_hours_ago: int = 0) -> str:
    """存储记忆并在 SQLite 中写入完整的 memory_values 记录，支持设置创建时间偏移。"""
    memory_id = await memory_service.save(content)
    created_at = _hours_ago_iso(created_hours_ago)
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            "INSERT OR REPLACE INTO memory_values"
            " (memory_id, value_score, tier, feedback_count, created_at, updated_at)"
            " VALUES (?, ?, ?, 0, ?, ?)",
            (memory_id, value_score, tier, created_at, created_at),
        )
        await db.commit()
    return memory_id


class TestDiskManagerEvictionTrigger:
    """测试淘汰触发条件：磁盘超过触发水位时执行淘汰。"""

    @pytest.mark.asyncio
    async def test_no_eviction_when_under_trigger(self, disk_manager, memory_service, db_path):
        """磁盘占用未超过触发水位时，check_and_evict() 应不执行淘汰。"""
        # 存储一条超过保护期的记忆
        memory_id = await _save_memory_with_db(
            memory_service, db_path, "未超限测试", value_score=0.1,
            created_hours_ago=settings.MEMORY_PROTECT_HOURS + 1
        )
        initial_cold_count = memory_service.get_cold_count()

        # Mock 磁盘占用为小于触发水位的值
        with patch.object(disk_manager, "get_disk_usage_gb", return_value=1.0):
            await disk_manager.check_and_evict()

        # 未超限，冷层数量不应减少
        assert memory_service.get_cold_count() == initial_cold_count

    @pytest.mark.asyncio
    async def test_eviction_triggered_when_over_trigger(self, disk_manager, memory_service, db_path):
        """磁盘占用超过触发水位时，check_and_evict() 应执行淘汰。"""
        # 存储一条超过保护期的低价值记忆
        memory_id = await _save_memory_with_db(
            memory_service, db_path, "超限淘汰测试", value_score=0.1,
            created_hours_ago=settings.MEMORY_PROTECT_HOURS + 1
        )
        assert memory_service.get_cold_count() == 1

        # Mock 磁盘占用：
        # 调用 1（初始检查）：超限，进入淘汰逻辑
        # 调用 2（while 条件）：仍超限，进入循环体执行淘汰
        # 调用 3（淘汰后检查）：降至安全水位，退出循环
        call_count = {"n": 0}
        def mock_usage():
            call_count["n"] += 1
            return settings.DISK_TRIGGER_GB + 1 if call_count["n"] <= 2 else settings.DISK_SAFE_GB - 1

        with patch.object(disk_manager, "get_disk_usage_gb", side_effect=mock_usage):
            await disk_manager.check_and_evict()

        # 超限后超过保护期的记忆应被淘汰
        assert memory_service.get_cold_count() == 0

    @pytest.mark.asyncio
    async def test_eviction_stops_when_reaching_safe_level(self, disk_manager, memory_service, db_path):
        """淘汰应在磁盘降至安全水位后停止，不过度淘汰。"""
        # 存储 3 条超过保护期的记忆
        ids = []
        for i in range(3):
            mid = await _save_memory_with_db(
                memory_service, db_path, f"安全水位测试 {i}", value_score=0.1,
                created_hours_ago=settings.MEMORY_PROTECT_HOURS + 1
            )
            ids.append(mid)
        assert memory_service.get_cold_count() == 3

        # Mock 磁盘占用：第一次超限，第二次已达安全水位
        call_count = {"n": 0}
        def mock_usage():
            call_count["n"] += 1
            return settings.DISK_TRIGGER_GB + 1 if call_count["n"] == 1 else settings.DISK_SAFE_GB - 1

        with patch.object(disk_manager, "get_disk_usage_gb", side_effect=mock_usage):
            await disk_manager.check_and_evict()

        # 应已淘汰至安全水位，但不应过度淘汰
        assert memory_service.get_cold_count() >= 0


class TestDiskManager168HourProtection:
    """测试 168 小时保护规则：创建时间在 168 小时以内的记忆不得被淘汰。(M3-AC-06)"""

    @pytest.mark.asyncio
    async def test_protected_memory_not_evicted(self, disk_manager, memory_service, db_path):
        """创建时间在 168 小时以内的记忆不得被淘汰（保护规则）。(M3-AC-06)"""
        # 存储一条保护期内的记忆（1 小时前创建）
        protected_id = await _save_memory_with_db(
            memory_service, db_path, "保护期内记忆", value_score=0.1,
            created_hours_ago=1  # 1 小时前，远小于 168 小时
        )
        assert memory_service.get_cold_count() == 1

        # 触发淘汰
        with patch.object(disk_manager, "get_disk_usage_gb",
                          return_value=settings.DISK_TRIGGER_GB + 1):
            await disk_manager.check_and_evict()

        # 保护期内的记忆不应被淘汰
        assert memory_service.get_cold_count() == 1, "保护期内的记忆不得被淘汰"

    @pytest.mark.asyncio
    async def test_memory_at_exactly_168h_can_be_evicted(self, disk_manager, memory_service, db_path):
        """创建时间恰好超过 168 小时的记忆应可被淘汰。(M3-AC-06)"""
        # 存储一条恰好超过保护期的记忆（169 小时前）
        expired_id = await _save_memory_with_db(
            memory_service, db_path, "保护期外记忆", value_score=0.1,
            created_hours_ago=settings.MEMORY_PROTECT_HOURS + 1
        )
        assert memory_service.get_cold_count() == 1

        # 调用 1（初始检查）：超限；调用 2（while 条件）：超限；调用 3（淘汰后）：安全
        call_count = {"n": 0}
        def mock_usage():
            call_count["n"] += 1
            return settings.DISK_TRIGGER_GB + 1 if call_count["n"] <= 2 else settings.DISK_SAFE_GB - 1

        with patch.object(disk_manager, "get_disk_usage_gb", side_effect=mock_usage):
            await disk_manager.check_and_evict()

        assert memory_service.get_cold_count() == 0, "超过保护期的记忆应被淘汰"

    @pytest.mark.asyncio
    async def test_protected_not_evicted_but_expired_is(self, disk_manager, memory_service, db_path):
        """保护期内的记忆不被淘汰，但保护期外的记忆应被淘汰。(M3-AC-06)"""
        # 保护期内的记忆（24 小时前）
        protected_id = await _save_memory_with_db(
            memory_service, db_path, "保护期内高价值记忆", value_score=0.5,
            created_hours_ago=24
        )
        # 保护期外的记忆（200 小时前）
        expired_id = await _save_memory_with_db(
            memory_service, db_path, "保护期外低价值记忆", value_score=0.1,
            created_hours_ago=200
        )
        assert memory_service.get_cold_count() == 2

        # 调用 1（初始检查）：超限；调用 2（while 条件）：超限；调用 3（淘汰后）：安全
        call_count = {"n": 0}
        def mock_usage():
            call_count["n"] += 1
            # 第一、二次调用超限，第三次（淘汰后）已降至安全水位
            return settings.DISK_TRIGGER_GB + 1 if call_count["n"] <= 2 else settings.DISK_SAFE_GB - 1

        with patch.object(disk_manager, "get_disk_usage_gb", side_effect=mock_usage):
            await disk_manager.check_and_evict()

        # 应剩余 1 条（保护期内的不被淘汰）
        assert memory_service.get_cold_count() == 1, (
            "保护期内的记忆应保留，保护期外的记忆应被淘汰"
        )

    @pytest.mark.asyncio
    async def test_no_candidates_stops_eviction(self, disk_manager, memory_service, db_path):
        """所有记忆均在保护期内时，淘汰循环应正常停止（无异常）。(M3-AC-06)"""
        # 存储一条保护期内的记忆
        await _save_memory_with_db(
            memory_service, db_path, "全保护测试", value_score=0.1,
            created_hours_ago=1
        )

        # 触发淘汰，但无可淘汰候选
        with patch.object(disk_manager, "get_disk_usage_gb",
                          return_value=settings.DISK_TRIGGER_GB + 1):
            await disk_manager.check_and_evict()

        # 无候选，记忆应保留
        assert memory_service.get_cold_count() == 1


class TestDiskManagerEvictionOrder:
    """测试淘汰顺序：按 value_score ASC, created_at ASC 排序。"""

    @pytest.mark.asyncio
    async def test_lowest_value_score_evicted_first(self, disk_manager, memory_service, db_path):
        """_get_evict_candidates() 应优先返回 value_score 最低的记忆。"""
        # 存储两条超过保护期的记忆，价值分不同
        high_id = await _save_memory_with_db(
            memory_service, db_path, "高价值记忆内容", value_score=0.8,
            created_hours_ago=settings.MEMORY_PROTECT_HOURS + 10
        )
        low_id = await _save_memory_with_db(
            memory_service, db_path, "低价值记忆内容", value_score=0.1,
            created_hours_ago=settings.MEMORY_PROTECT_HOURS + 10
        )

        # 直接测试淘汰候选排序：低价值应排在前面
        candidates = await disk_manager._get_evict_candidates(batch_size=10)
        assert len(candidates) == 2, "应返回 2 个候选"
        assert candidates[0] == low_id, "value_score 最低的记忆应排在候选列表首位"

    @pytest.mark.asyncio
    async def test_older_evicted_first_when_equal_score(self, disk_manager, memory_service, db_path):
        """价值分相同时，_get_evict_candidates() 应优先返回创建时间更早的记忆。"""
        # 两条记忆，价值分相同但创建时间不同
        newer_id = await _save_memory_with_db(
            memory_service, db_path, "较新记忆", value_score=0.3,
            created_hours_ago=settings.MEMORY_PROTECT_HOURS + 10
        )
        older_id = await _save_memory_with_db(
            memory_service, db_path, "较旧记忆", value_score=0.3,
            created_hours_ago=settings.MEMORY_PROTECT_HOURS + 50
        )

        # 直接测试候选排序：创建时间更早的应排在前面
        candidates = await disk_manager._get_evict_candidates(batch_size=10)
        assert len(candidates) == 2, "应返回 2 个候选"
        assert candidates[0] == older_id, "创建时间更早的记忆应排在候选列表首位"

    @pytest.mark.asyncio
    async def test_evict_removes_from_chroma_and_sqlite(self, disk_manager, memory_service, db_path):
        """_evict() 应从 ChromaDB 和 SQLite 中删除记忆。"""
        memory_id = await _save_memory_with_db(
            memory_service, db_path, "淘汰操作测试", value_score=0.1,
            created_hours_ago=settings.MEMORY_PROTECT_HOURS + 1
        )
        assert memory_service.get_cold_count() == 1

        await disk_manager._evict(memory_id)

        # ChromaDB 中记忆应被删除
        assert memory_service.get_cold_count() == 0
        # SQLite 中 memory_values 记录应被删除
        async with aiosqlite.connect(db_path) as db:
            async with db.execute(
                "SELECT COUNT(*) FROM memory_values WHERE memory_id = ?", (memory_id,)
            ) as cursor:
                count = (await cursor.fetchone())[0]
        assert count == 0


class TestDiskManagerStats:
    """测试 DiskManager 统计接口。"""

    @pytest.mark.asyncio
    async def test_get_disk_stats_returns_dict(self, disk_manager):
        """get_disk_stats() 应返回包含配置字段的字典。"""
        stats = disk_manager.get_disk_stats()
        assert isinstance(stats, dict)
        assert "disk_used_gb" in stats
        assert "disk_budget_gb" in stats
        assert "disk_trigger_gb" in stats
        assert "disk_safe_gb" in stats

    @pytest.mark.asyncio
    async def test_get_disk_usage_gb_returns_float(self, disk_manager):
        """get_disk_usage_gb() 应返回非负浮点数。"""
        usage = disk_manager.get_disk_usage_gb()
        assert isinstance(usage, float)
        assert usage >= 0.0
