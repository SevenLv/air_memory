"""TierManager 单元测试：启动时热层加载、超限降级、容量统计。"""

import pytest

from air_memory.config import settings
from tests.conftest import insert_input_memory_link


class TestTierManagerRestoreHotTier:
    """测试 TierManager.restore_hot_tier() 启动时热层加载。"""

    @pytest.mark.asyncio
    async def test_restore_hot_tier_loads_high_value_memories(
        self, tier_manager, memory_service, db_path
    ):
        """启动恢复应将 total_association_score > 0 的冷层记忆加载到热层。"""
        # 在冷层存储两条记忆
        id1 = await memory_service.save("高价值记忆：机器学习")
        id2 = await memory_service.save("低价值记忆：随机内容")

        # 为 id1 设置关联评分（total_association_score > 0），id2 不设置（score=0.0，无关联记录）
        await insert_input_memory_link(db_path, "input-restore-1", id1, association_score=0.8)

        # 执行热层恢复
        await tier_manager.restore_hot_tier()

        # id1 应进入热层，id2 不应进入
        assert memory_service.get_hot_count() >= 1

    @pytest.mark.asyncio
    async def test_restore_hot_tier_skips_low_value_memories(
        self, tier_manager, memory_service, db_path
    ):
        """启动恢复不应将 total_association_score < PROMOTE_THRESHOLD 的冷层记忆加载到热层。"""
        id1 = await memory_service.save("低价值记忆内容")
        # 模拟系统重启：热层被清空（EphemeralClient 不持久化），记忆仍在冷层
        await memory_service.demote(id1)
        # id1 无关联评分（score=0.0），低于 PROMOTE_THRESHOLD

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
            await memory_service.demote(id1)
            # 为 id1 设置高关联评分，使其满足恢复阈值（但预算为 0 不允许加载）
            await insert_input_memory_link(db_path, "input-budget", id1, association_score=0.9)

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
        """恢复时应优先加载 total_association_score 更高的记忆。"""
        original_budget = settings.HOT_MEMORY_BUDGET_MB

        try:
            id_low = await memory_service.save("低关联记忆")
            id_high = await memory_service.save("旧高价值冷层记忆")
            await insert_input_memory_link(db_path, "input-priority", id_high,
                                           association_score=0.9)

            # 将预算限制到只能容纳一条记忆
            settings.HOT_MEMORY_BUDGET_MB = (2 / 1024)

            await tier_manager.restore_hot_tier()

            # 高关联记忆应优先被加载，低关联（无关联）记忆不应进入热层
            assert await memory_service.is_hot(id_high), "高关联记忆应优先恢复到热层"
            assert not await memory_service.is_hot(id_low), "无关联记忆不应恢复到热层"
        finally:
            settings.HOT_MEMORY_BUDGET_MB = original_budget


class TestTierManagerCheckMemoryBudget:
    """测试 TierManager.check_memory_budget() 超限降级。"""

    @pytest.mark.asyncio
    async def test_no_demote_when_within_budget(self, tier_manager, memory_service, db_path):
        """热层内存未超限时不应触发降级。"""
        id1 = await memory_service.save("热层记忆内容")
        await memory_service.promote(id1)
        await insert_input_memory_link(db_path, "input-budget-check", id1, association_score=0.8)

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
            await memory_service.promote(id1)
            await insert_input_memory_link(db_path, "input-exceed", id1, association_score=0.8)

            assert memory_service.get_hot_count() == 1
            await tier_manager.check_memory_budget()
            # 超限后应将记忆降级
            assert memory_service.get_hot_count() == 0
        finally:
            settings.HOT_MEMORY_BUDGET_MB = original_budget

    @pytest.mark.asyncio
    async def test_demotes_lowest_score_before_high_score_memories(
        self, tier_manager, memory_service, db_path
    ):
        """超限驱逐时，关联评分低的记忆应先于关联评分高的记忆被驱逐。"""
        original_budget = settings.HOT_MEMORY_BUDGET_MB
        settings.HOT_MEMORY_BUDGET_MB = 0

        try:
            id_old = await memory_service.save("旧记忆，无高关联评分")
            id_new = await memory_service.save("新记忆，有高关联评分")
            await memory_service.promote(id_old)
            await memory_service.promote(id_new)
            # id_new 有高关联评分，应被保留；id_old 无评分（score=0），应被驱逐
            await insert_input_memory_link(db_path, "input-demote", id_new,
                                           association_score=0.9)

            assert memory_service.get_hot_count() == 2

            # 恢复一点预算以允许保留一条记忆
            settings.HOT_MEMORY_BUDGET_MB = memory_service.get_hot_memory_mb() / 2
            await tier_manager.check_memory_budget()

            # 低评分旧记忆应被驱逐，高评分新记忆应被保留
            assert not await memory_service.is_hot(id_old), "低评分旧记忆应已从热层驱逐"
            assert await memory_service.is_hot(id_new), "高评分新记忆应保留在热层"
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
        """存储记忆后，cold_count 增加，hot_count 不变（新记忆仅进入冷层）。"""
        await memory_service.save("统计测试记忆")
        stats = tier_manager.get_hot_stats()
        assert stats["cold_count"] == 1
        assert stats["hot_count"] == 0

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
