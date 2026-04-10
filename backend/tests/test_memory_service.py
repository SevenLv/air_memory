"""MemoryService 单元测试：存储、快速查询、深度查询、层间迁移、响应时间断言。"""

import time

import pytest
import pytest_asyncio

from air_memory.config import settings


# ---------------------------------------------------------------------------
# 存储测试
# ---------------------------------------------------------------------------

class TestMemoryServiceSave:
    """测试 MemoryService.save() 方法。"""

    @pytest.mark.asyncio
    async def test_save_returns_valid_id(self, memory_service):
        """存储记忆应返回有效的 UUID 格式 memory_id。"""
        memory_id = await memory_service.save("测试记忆内容")
        assert isinstance(memory_id, str)
        assert len(memory_id) > 0

    @pytest.mark.asyncio
    async def test_save_increments_cold_count(self, memory_service):
        """存储记忆后冷层计数应加 1。"""
        initial_count = memory_service.get_cold_count()
        await memory_service.save("测试内容一")
        assert memory_service.get_cold_count() == initial_count + 1

    @pytest.mark.asyncio
    async def test_save_multiple_returns_unique_ids(self, memory_service):
        """多次存储应返回不同的 memory_id。"""
        id1 = await memory_service.save("内容一")
        id2 = await memory_service.save("内容二")
        assert id1 != id2

    @pytest.mark.asyncio
    async def test_save_response_time_within_1000ms(self, memory_service):
        """存储操作响应时间应不超过 1000ms（测试环境宽松阈值）。(M3-AC-05)"""
        start = time.perf_counter()
        await memory_service.save("响应时间测试内容")
        elapsed_ms = (time.perf_counter() - start) * 1000
        assert elapsed_ms < 1000, f"存储响应时间 {elapsed_ms:.1f}ms 超过 1000ms 阈值"


# ---------------------------------------------------------------------------
# 深度查询测试（热层 + 冷层）
# ---------------------------------------------------------------------------

class TestMemoryServiceDeepQuery:
    """测试 MemoryService.query() 深度查询模式（fast_only=False）。"""

    @pytest.mark.asyncio
    async def test_deep_query_returns_saved_memory(self, memory_service):
        """深度查询应能返回刚存储的冷层记忆。"""
        content = "深度查询测试：Python 编程语言"
        memory_id = await memory_service.save(content)
        results = await memory_service.query("Python 编程", top_k=5, fast_only=False)
        ids = [m.id for m in results]
        assert memory_id in ids, "深度查询应返回刚存储的记忆"

    @pytest.mark.asyncio
    async def test_deep_query_content_correct(self, memory_service):
        """深度查询返回记忆的 content 字段应与存储时完全一致。(M3-AC-09)"""
        content = "深度查询内容正确性测试：机器学习算法"
        memory_id = await memory_service.save(content)
        results = await memory_service.query("机器学习", top_k=5, fast_only=False)
        target = next((m for m in results if m.id == memory_id), None)
        assert target is not None, "应能找到刚存储的记忆"
        assert target.content == content, (
            f"查询返回的 content 应与存储输入完全一致，期望={content!r}，实际={target.content!r}"
        )

    @pytest.mark.asyncio
    async def test_deep_query_returns_cold_tier(self, memory_service):
        """初始存储在冷层，深度查询返回的记忆 tier 应为 'cold'。"""
        content = "冷层查询测试内容"
        memory_id = await memory_service.save(content)
        results = await memory_service.query("冷层查询", top_k=5, fast_only=False)
        target = next((m for m in results if m.id == memory_id), None)
        assert target is not None
        assert target.tier == "cold"

    @pytest.mark.asyncio
    async def test_deep_query_response_time_within_1000ms(self, memory_service):
        """深度查询响应时间应不超过 1000ms（测试环境宽松阈值）。(M3-AC-05)"""
        await memory_service.save("响应时间基准内容")
        start = time.perf_counter()
        await memory_service.query("响应时间测试", top_k=5, fast_only=False)
        elapsed_ms = (time.perf_counter() - start) * 1000
        assert elapsed_ms < 1000, f"深度查询响应时间 {elapsed_ms:.1f}ms 超过 1000ms 阈值"

    @pytest.mark.asyncio
    async def test_deep_query_empty_when_no_data(self, memory_service):
        """空数据库中执行深度查询应返回空列表。"""
        results = await memory_service.query("任意查询", top_k=5, fast_only=False)
        assert results == []

    @pytest.mark.asyncio
    async def test_deep_query_top_k_limit(self, memory_service):
        """深度查询返回结果数量不超过 top_k。"""
        for i in range(5):
            await memory_service.save(f"测试记忆内容 {i}")
        results = await memory_service.query("测试记忆", top_k=3, fast_only=False)
        assert len(results) <= 3


# ---------------------------------------------------------------------------
# 快速查询测试（仅热层）
# ---------------------------------------------------------------------------

class TestMemoryServiceFastQuery:
    """测试 MemoryService.query() 快速查询模式（fast_only=True）。"""

    @pytest.mark.asyncio
    async def test_fast_query_empty_when_cold_only(self, memory_service):
        """刚存入冷层的记忆不应出现在快速查询结果中（热层为空）。"""
        await memory_service.save("快速查询测试内容")
        results = await memory_service.query("快速查询", top_k=5, fast_only=True)
        assert results == [], "新存入冷层的记忆不应出现在热层快速查询中"

    @pytest.mark.asyncio
    async def test_fast_query_content_correct_after_promote(self, memory_service):
        """升级到热层后，快速查询返回的 content 字段应与存储输入完全一致。(M3-AC-09)"""
        content = "快速查询内容正确性测试：自然语言处理"
        memory_id = await memory_service.save(content)
        # 将记忆升级到热层
        await memory_service.promote(memory_id, value_score=0.8)
        results = await memory_service.query("自然语言处理", top_k=5, fast_only=True)
        target = next((m for m in results if m.id == memory_id), None)
        assert target is not None, "升级后应能在热层找到该记忆"
        assert target.content == content, (
            f"快速查询返回 content 应与存储输入一致，期望={content!r}，实际={target.content!r}"
        )

    @pytest.mark.asyncio
    async def test_fast_query_returns_hot_tier(self, memory_service):
        """快速查询返回的记忆 tier 应为 'hot'。"""
        content = "热层快速查询记忆"
        memory_id = await memory_service.save(content)
        await memory_service.promote(memory_id, value_score=0.8)
        results = await memory_service.query("热层快速查询", top_k=5, fast_only=True)
        target = next((m for m in results if m.id == memory_id), None)
        assert target is not None
        assert target.tier == "hot"

    @pytest.mark.asyncio
    async def test_fast_query_response_time_within_1000ms(self, memory_service):
        """快速查询响应时间应不超过 1000ms（测试环境宽松阈值）。(M3-AC-05)"""
        content = "快速查询响应时间测试"
        memory_id = await memory_service.save(content)
        await memory_service.promote(memory_id, value_score=0.8)
        start = time.perf_counter()
        await memory_service.query("响应时间", top_k=5, fast_only=True)
        elapsed_ms = (time.perf_counter() - start) * 1000
        assert elapsed_ms < 1000, f"快速查询响应时间 {elapsed_ms:.1f}ms 超过 1000ms 阈值"


# ---------------------------------------------------------------------------
# 层间迁移测试
# ---------------------------------------------------------------------------

class TestMemoryServiceTierMigration:
    """测试 MemoryService 的 promote/demote/delete 层间迁移操作。"""

    @pytest.mark.asyncio
    async def test_promote_moves_to_hot(self, memory_service):
        """promote() 应将记忆加入热层。"""
        content = "升级迁移测试内容"
        memory_id = await memory_service.save(content)
        assert memory_service.get_hot_count() == 0

        await memory_service.promote(memory_id, value_score=0.8)
        assert memory_service.get_hot_count() == 1

    @pytest.mark.asyncio
    async def test_demote_removes_from_hot(self, memory_service):
        """demote() 应将记忆从热层移除。"""
        content = "降级迁移测试内容"
        memory_id = await memory_service.save(content)
        await memory_service.promote(memory_id, value_score=0.8)
        assert memory_service.get_hot_count() == 1

        await memory_service.demote(memory_id, value_score=0.2)
        assert memory_service.get_hot_count() == 0

    @pytest.mark.asyncio
    async def test_delete_removes_from_both_tiers(self, memory_service):
        """delete() 应从热层和冷层同时删除指定记忆。"""
        content = "删除测试内容"
        memory_id = await memory_service.save(content)
        await memory_service.promote(memory_id, value_score=0.8)
        assert memory_service.get_cold_count() == 1
        assert memory_service.get_hot_count() == 1

        await memory_service.delete(memory_id)
        assert memory_service.get_cold_count() == 0
        assert memory_service.get_hot_count() == 0

    @pytest.mark.asyncio
    async def test_load_hot_from_cold(self, memory_service):
        """load_hot_from_cold() 应从冷层加载指定记忆到热层。"""
        content = "启动恢复热层测试"
        memory_id = await memory_service.save(content)
        await memory_service.load_hot_from_cold(memory_id, value_score=0.7)
        assert memory_service.get_hot_count() == 1

    @pytest.mark.asyncio
    async def test_promote_nonexistent_memory(self, memory_service):
        """对不存在的 memory_id 执行 promote() 应不抛出异常。"""
        await memory_service.promote("nonexistent-id", value_score=0.8)
        assert memory_service.get_hot_count() == 0

    @pytest.mark.asyncio
    async def test_get_hot_memory_mb(self, memory_service):
        """热层内存估算应随记忆数量增加而增大。"""
        assert memory_service.get_hot_memory_mb() == 0.0
        content = "内存估算测试"
        memory_id = await memory_service.save(content)
        await memory_service.promote(memory_id, value_score=0.8)
        assert memory_service.get_hot_memory_mb() > 0
