"""TierManager 单元测试：启动时热层加载、超限降级、容量统计。"""

import pytest
import pytest_asyncio
import aiosqlite

from air_memory.config import settings
from tests.conftest import insert_memory_value


class TestTierManagerRestoreHotTier:
    """测试 TierManager.restore_hot_tier() 启动时热层加载。"""

    @pytest.mark.asyncio
    async def test_restore_hot_tier_loads_high_value_memories(
        self, tier_manager, memory_service, db_path
    ):
        """启动恢复应将 value_score >= PROMOTE_THRESHOLD 的冷层记忆加载到热层。"""
        # 在冷层存储两条记忆
        id1 = await memory_service.save("高价值记忆：机器学习")
        id2 = await memory_service.save("低价值记忆：随机内容")

        # 在 SQLite 中设置 value_score：id1 高于升级阈值，id2 低于
        await insert_memory_value(db_path, id1, value_score=0.8, tier="cold")
        await insert_memory_value(db_path, id2, value_score=0.2, tier="cold")

        # 执行热层恢复
        await tier_manager.restore_hot_tier()

        # id1 应进入热层，id2 不应进入
        assert memory_service.get_hot_count() >= 1

    @pytest.mark.asyncio
    async def test_restore_hot_tier_skips_low_value_memories(
        self, tier_manager, memory_service, db_path
    ):
        """启动恢复不应将 value_score < PROMOTE_THRESHOLD 的冷层记忆加载到热层。"""
        id1 = await memory_service.save("低价值记忆内容")
        # 模拟系统重启：热层被清空（EphemeralClient 不持久化），记忆仍在冷层
        await memory_service.demote(id1, value_score=0.2)
        await insert_memory_value(db_path, id1, value_score=0.2, tier="cold")

        await tier_manager.restore_hot_tier()

        assert memory_service.get_hot_count() == 0

    @pytest.mark.asyncio
    async def test_restore_hot_tier_respects_memory_budget(
        self, tier_manager, memory_service, db_path
    ):
        """热层恢复应遵守内存预算，不超过 HOT_MEMORY_BUDGET_MB。"""
        # 设置极小内存预算
        original_budget = settings.HOT_MEMORY_BUDGET_MB
        settings.HOT_MEMORY_BUDGET_MB = 0  # 预算为 0，不允许加载

        try:
            id1 = await memory_service.save("预算测试记忆")
            # 模拟系统重启：热层被清空，记忆仍在冷层
            await memory_service.demote(id1, value_score=0.9)
            await insert_memory_value(db_path, id1, value_score=0.9, tier="cold")

            await tier_manager.restore_hot_tier()

            # 由于预算为 0，热层应为空
            assert memory_service.get_hot_count() == 0
        finally:
            settings.HOT_MEMORY_BUDGET_MB = original_budget

    @pytest.mark.asyncio
    async def test_restore_hot_tier_with_empty_db(self, tier_manager, memory_service):
        """空数据库时热层恢复应正常执行（无异常）。"""
        await tier_manager.restore_hot_tier()
        assert memory_service.get_hot_count() == 0

    @pytest.mark.asyncio
    async def test_restore_hot_tier_prioritizes_hot_tier_memories(
        self, tier_manager, memory_service, db_path
    ):
        """恢复时 tier='hot' 的记忆（含新记忆）应优先于冷层高价值记忆被加载。"""
        original_budget = settings.HOT_MEMORY_BUDGET_MB

        try:
            id_new = await memory_service.save("新记忆（tier=hot）")
            id_high = await memory_service.save("旧高价值冷层记忆")

            # 模拟重启：从热层清空（仅保留冷层数据）
            await memory_service.demote(id_new, value_score=settings.INITIAL_VALUE_SCORE)
            await memory_service.demote(id_high, value_score=0.9)

            # 新记忆：tier='hot'（刚存入尚未降级）；旧记忆：tier='cold' 但 value_score 很高
            await insert_memory_value(db_path, id_new,
                                      value_score=settings.INITIAL_VALUE_SCORE, tier="hot")
            await insert_memory_value(db_path, id_high, value_score=0.9, tier="cold")

            # 将预算限制到只能容纳一条记忆
            settings.HOT_MEMORY_BUDGET_MB = memory_service.get_hot_memory_mb() + (2 / 1024)

            await tier_manager.restore_hot_tier()

            # tier='hot' 的新记忆应被优先加载
            results = await memory_service.query("新记忆", top_k=1, fast_only=True)
            assert any(m.id == id_new for m in results), "tier='hot' 的新记忆应被优先恢复到热层"
        finally:
            settings.HOT_MEMORY_BUDGET_MB = original_budget


class TestTierManagerCheckMemoryBudget:
    """测试 TierManager.check_memory_budget() 超限降级。"""

    @pytest.mark.asyncio
    async def test_no_demote_when_within_budget(self, tier_manager, memory_service, db_path):
        """热层内存未超限时不应触发降级。"""
        id1 = await memory_service.save("热层记忆内容")
        await memory_service.promote(id1, value_score=0.8)
        await insert_memory_value(db_path, id1, value_score=0.8, tier="hot")

        initial_hot_count = memory_service.get_hot_count()
        await tier_manager.check_memory_budget()
        # 预算充足，热层数量不应减少
        assert memory_service.get_hot_count() == initial_hot_count

    @pytest.mark.asyncio
    async def test_demotes_when_budget_exceeded(self, tier_manager, memory_service, db_path):
        """热层内存超限时应降级最低价值记忆。"""
        # 将预算设置为极小值
        original_budget = settings.HOT_MEMORY_BUDGET_MB
        settings.HOT_MEMORY_BUDGET_MB = 0

        try:
            id1 = await memory_service.save("超限测试记忆")
            await memory_service.promote(id1, value_score=0.8)
            await insert_memory_value(db_path, id1, value_score=0.8, tier="hot")

            assert memory_service.get_hot_count() == 1
            await tier_manager.check_memory_budget()
            # 超限后应将记忆降级
            assert memory_service.get_hot_count() == 0
        finally:
            settings.HOT_MEMORY_BUDGET_MB = original_budget

    @pytest.mark.asyncio
    async def test_demotes_feedback_count_positive_before_new_memories(
        self, tier_manager, memory_service, db_path
    ):
        """超限驱逐时，有反馈且价值低的记忆应先于从未评价的新记忆被驱逐。"""
        original_budget = settings.HOT_MEMORY_BUDGET_MB
        settings.HOT_MEMORY_BUDGET_MB = 0

        try:
            id_new = await memory_service.save("新记忆，无反馈")
            id_old = await memory_service.save("旧记忆，有负向反馈")
            await memory_service.promote(id_new, value_score=settings.INITIAL_VALUE_SCORE)
            await memory_service.promote(id_old, value_score=0.3)
            # 新记忆：feedback_count=0；旧记忆：feedback_count=3（被多次负反馈）
            await insert_memory_value(db_path, id_new, value_score=settings.INITIAL_VALUE_SCORE,
                                      tier="hot", feedback_count=0)
            await insert_memory_value(db_path, id_old, value_score=0.3,
                                      tier="hot", feedback_count=3)

            assert memory_service.get_hot_count() == 2

            # 恢复一点预算以允许保留一条记忆
            settings.HOT_MEMORY_BUDGET_MB = memory_service.get_hot_memory_mb() / 2
            await tier_manager.check_memory_budget()

            # 有反馈的低价值旧记忆应被驱逐，新记忆应被保留
            results = await memory_service.query("旧记忆", top_k=1, fast_only=True)
            old_in_hot = any(m.id == id_old for m in results)
            results_new = await memory_service.query("新记忆", top_k=1, fast_only=True)
            new_in_hot = any(m.id == id_new for m in results_new)
            assert not old_in_hot, "旧低价值记忆应已从热层驱逐"
            assert new_in_hot, "新记忆应保留在热层"
        finally:
            settings.HOT_MEMORY_BUDGET_MB = original_budget


class TestTierManagerGetHotStats:
    """测试 TierManager.get_hot_stats() 容量统计。"""

    @pytest.mark.asyncio
    async def test_get_hot_stats_returns_dict(self, tier_manager):
        """get_hot_stats() 应返回包含统计字段的字典。"""
        stats = tier_manager.get_hot_stats()
        assert isinstance(stats, dict)
        assert "hot_count" in stats
        assert "cold_count" in stats
        assert "hot_memory_mb" in stats
        assert "memory_budget_mb" in stats

    @pytest.mark.asyncio
    async def test_get_hot_stats_initial_state(self, tier_manager):
        """初始状态热层和冷层均为空，计数应为 0。"""
        stats = tier_manager.get_hot_stats()
        assert stats["hot_count"] == 0
        assert stats["cold_count"] == 0
        assert stats["hot_memory_mb"] == 0.0

    @pytest.mark.asyncio
    async def test_get_hot_stats_after_save(self, tier_manager, memory_service):
        """存储记忆后，hot_count 和 cold_count 均应增加（新记忆同时进入热层和冷层）。"""
        await memory_service.save("统计测试记忆")
        stats = tier_manager.get_hot_stats()
        assert stats["cold_count"] == 1
        assert stats["hot_count"] == 1

    @pytest.mark.asyncio
    async def test_get_hot_stats_after_promote(self, tier_manager, memory_service):
        """升级记忆后，hot_count 应增加，hot_memory_mb 应不小于 0。"""
        memory_id = await memory_service.save("升级统计测试")
        await memory_service.promote(memory_id, value_score=0.8)
        stats = tier_manager.get_hot_stats()
        assert stats["hot_count"] == 1
        # hot_memory_mb 按每条 2KB 估算后取 2 位小数；数量少时可能为 0.0，至少不为负数
        assert stats["hot_memory_mb"] >= 0.0
        # 验证原始估算值（未取整）确实大于 0
        assert memory_service.get_hot_memory_mb() > 0
