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
    async def test_save_increments_hot_count(self, memory_service):
        """存储记忆后热层计数应加 1（新记忆初始进入热层）。"""
        initial_count = memory_service.get_hot_count()
        await memory_service.save("热层初始计数测试")
        assert memory_service.get_hot_count() == initial_count + 1

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
    """测试 MemoryService.query() 深度查询模式（热层 + 冷层 + 关联记忆）。"""

    @pytest.mark.asyncio
    async def test_deep_query_returns_saved_memory(self, memory_service):
        """查询应能返回刚存储的记忆。"""
        content = "深度查询测试：Python 编程语言"
        memory_id = await memory_service.save(content)
        _, results = await memory_service.query("Python 编程", top_k=5)
        ids = [m.id for m in results]
        assert memory_id in ids, "查询应返回刚存储的记忆"

    @pytest.mark.asyncio
    async def test_deep_query_content_correct(self, memory_service):
        """查询返回记忆的 content 字段应与存储时完全一致。(M3-AC-09)"""
        content = "深度查询内容正确性测试：机器学习算法"
        memory_id = await memory_service.save(content)
        _, results = await memory_service.query("机器学习", top_k=5)
        target = next((m for m in results if m.id == memory_id), None)
        assert target is not None, "应能找到刚存储的记忆"
        assert target.content == content, (
            f"查询返回的 content 应与存储输入完全一致，期望={content!r}，实际={target.content!r}"
        )

    @pytest.mark.asyncio
    async def test_deep_query_returns_hot_tier(self, memory_service):
        """新记忆初始存入热层，查询返回的记忆 tier 应为 'hot'。"""
        content = "热层查询测试内容"
        memory_id = await memory_service.save(content)
        _, results = await memory_service.query("热层查询", top_k=5)
        target = next((m for m in results if m.id == memory_id), None)
        assert target is not None
        assert target.tier == "hot"

    @pytest.mark.asyncio
    async def test_deep_query_response_time_within_1000ms(self, memory_service):
        """查询响应时间应不超过 1000ms（测试环境宽松阈值）。(M3-AC-05)"""
        await memory_service.save("响应时间基准内容")
        start = time.perf_counter()
        await memory_service.query("响应时间测试", top_k=5)
        elapsed_ms = (time.perf_counter() - start) * 1000
        assert elapsed_ms < 1000, f"查询响应时间 {elapsed_ms:.1f}ms 超过 1000ms 阈值"

    @pytest.mark.asyncio
    async def test_deep_query_empty_when_no_data(self, memory_service):
        """空数据库中执行查询应返回空列表。"""
        _, results = await memory_service.query("任意查询", top_k=5)
        assert results == []

    @pytest.mark.asyncio
    async def test_deep_query_top_k_limit(self, memory_service):
        """查询返回结果数量不超过 top_k。"""
        for i in range(5):
            await memory_service.save(f"测试记忆内容 {i}")
        _, results = await memory_service.query("测试记忆", top_k=3)
        assert len(results) <= 3


# ---------------------------------------------------------------------------
# 查询返回 input_id 测试
# ---------------------------------------------------------------------------

class TestMemoryServiceQueryReturnInputId:
    """测试 MemoryService.query() 返回 (input_id, memories) 元组。"""

    @pytest.mark.asyncio
    async def test_query_returns_tuple_with_input_id(self, memory_service):
        """query() 应返回 (input_id, memories) 元组，input_id 为非空字符串。"""
        result = await memory_service.query("测试查询", top_k=5)
        assert isinstance(result, tuple) and len(result) == 2, "query() 应返回长度为 2 的元组"
        input_id, memories = result
        assert isinstance(input_id, str) and len(input_id) > 0, "input_id 应为非空字符串"

    @pytest.mark.asyncio
    async def test_query_input_id_is_unique_per_call(self, memory_service):
        """每次 query() 调用应生成不同的 input_id。"""
        input_id_1, _ = await memory_service.query("查询一", top_k=5)
        input_id_2, _ = await memory_service.query("查询二", top_k=5)
        assert input_id_1 != input_id_2, "每次查询应生成唯一的 input_id"

    @pytest.mark.asyncio
    async def test_query_returns_saved_memory_in_results(self, memory_service):
        """query() 返回的 memories 列表应包含刚存储的记忆。"""
        content = "新记忆查询测试内容"
        memory_id = await memory_service.save(content)
        _, memories = await memory_service.query("新记忆查询", top_k=5)
        ids = [m.id for m in memories]
        assert memory_id in ids, "新记忆应出现在查询结果中"

    @pytest.mark.asyncio
    async def test_query_response_time_within_1000ms(self, memory_service):
        """query() 响应时间应不超过 1000ms（测试环境宽松阈值）。(M3-AC-05)"""
        await memory_service.save("响应时间测试内容")
        start = time.perf_counter()
        await memory_service.query("响应时间", top_k=5)
        elapsed_ms = (time.perf_counter() - start) * 1000
        assert elapsed_ms < 1000, f"查询响应时间 {elapsed_ms:.1f}ms 超过 1000ms 阈值"


# ---------------------------------------------------------------------------
# 层间迁移测试
# ---------------------------------------------------------------------------

class TestMemoryServiceTierMigration:
    """测试 MemoryService 的 promote/demote/delete 层间迁移操作。"""

    @pytest.mark.asyncio
    async def test_promote_moves_to_hot(self, memory_service):
        """promote() 应将记忆加入热层（新记忆已在热层，upsert 后计数不变）。"""
        content = "升级迁移测试内容"
        memory_id = await memory_service.save(content)
        assert memory_service.get_hot_count() == 1  # 新记忆初始在热层

        await memory_service.promote(memory_id, value_score=0.8)
        assert memory_service.get_hot_count() == 1  # upsert，计数不变

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
        content = "内存估算测试"
        memory_id = await memory_service.save(content)
        assert memory_service.get_hot_memory_mb() > 0  # 新记忆在热层，内存 > 0
