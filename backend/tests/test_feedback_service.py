"""FeedbackService 单元测试：关联评分更新、Feedback 日志写入、迁移触发条件。"""

import asyncio
import uuid

import pytest
import aiosqlite

from air_memory.config import settings
from tests.conftest import insert_input_memory_link


class TestFeedbackServiceAssociationScore:
    """测试关联评分更新逻辑。"""

    @pytest.mark.asyncio
    async def test_positive_feedback_creates_association_score(
        self, feedback_service, memory_service, db_path
    ):
        """正向反馈应为 input_id+memory_id 创建关联评分（ASSOCIATION_SCORE_STEP）。"""
        memory_id = await memory_service.save("关联评分创建测试")
        input_id = str(uuid.uuid4())
        await feedback_service.submit(input_id, memory_id, valuable=True)
        total = await feedback_service._get_total_association_score(memory_id)
        assert total == pytest.approx(settings.ASSOCIATION_SCORE_STEP), (
            f"期望关联评分为 {settings.ASSOCIATION_SCORE_STEP}，实际 {total}"
        )

    @pytest.mark.asyncio
    async def test_positive_feedback_accumulates_score(
        self, feedback_service, memory_service, db_path
    ):
        """多次正向反馈应累计关联评分，无上限。"""
        memory_id = await memory_service.save("累计评分测试")
        input_id = str(uuid.uuid4())
        await feedback_service.submit(input_id, memory_id, valuable=True)
        await feedback_service.submit(input_id, memory_id, valuable=True)
        total = await feedback_service._get_total_association_score(memory_id)
        expected = settings.ASSOCIATION_SCORE_STEP * 2
        assert total == pytest.approx(expected), (
            f"两次正向反馈后评分应为 {expected}，实际 {total}"
        )

    @pytest.mark.asyncio
    async def test_negative_feedback_deletes_link_when_score_reaches_zero(
        self, feedback_service, memory_service, db_path
    ):
        """负向反馈使关联评分降至 0 时，应删除链接记录，总评分返回 0.0。"""
        memory_id = await memory_service.save("链接删除测试")
        input_id = str(uuid.uuid4())
        await feedback_service.submit(input_id, memory_id, valuable=True)   # score=1.0
        await feedback_service.submit(input_id, memory_id, valuable=False)  # score→0→删除
        total = await feedback_service._get_total_association_score(memory_id)
        assert total == pytest.approx(0.0), f"链接删除后总评分应为 0.0，实际 {total}"

    @pytest.mark.asyncio
    async def test_negative_feedback_on_no_link_does_nothing(
        self, feedback_service, memory_service, db_path
    ):
        """对无链接记录的记忆提交负向反馈应无异常，总评分仍为 0.0。"""
        memory_id = await memory_service.save("无链接负向反馈测试")
        input_id = str(uuid.uuid4())
        await feedback_service.submit(input_id, memory_id, valuable=False)
        total = await feedback_service._get_total_association_score(memory_id)
        assert total == pytest.approx(0.0)

    @pytest.mark.asyncio
    async def test_association_score_no_upper_bound(
        self, feedback_service, memory_service, db_path
    ):
        """关联评分无上限，多次正向反馈后评分应超过 1.0。(M3-AC-07)"""
        memory_id = await memory_service.save("无上限测试")
        input_id = str(uuid.uuid4())
        for _ in range(3):
            await feedback_service.submit(input_id, memory_id, valuable=True)
        total = await feedback_service._get_total_association_score(memory_id)
        assert total > 1.0, f"三次正向反馈后评分应超过 1.0，实际 {total}"

    @pytest.mark.asyncio
    async def test_get_total_association_score_returns_correct_data(
        self, feedback_service, memory_service, db_path
    ):
        """_get_total_association_score() 应返回多条链接的总关联评分之和。"""
        memory_id = await memory_service.save("评分查询测试")
        await insert_input_memory_link(db_path, "input-a", memory_id, association_score=0.7)
        await insert_input_memory_link(db_path, "input-b", memory_id, association_score=0.5)
        total = await feedback_service._get_total_association_score(memory_id)
        assert total == pytest.approx(1.2)

    @pytest.mark.asyncio
    async def test_get_total_association_score_returns_zero_for_nonexistent(
        self, feedback_service
    ):
        """不存在的 memory_id 查询总关联评分应返回 0.0。"""
        total = await feedback_service._get_total_association_score("nonexistent-id")
        assert total == pytest.approx(0.0)


class TestFeedbackServiceLogWriting:
    """测试 Feedback 日志写入功能。(M3-AC-10)"""

    @pytest.mark.asyncio
    async def test_feedback_log_written_on_submit(self, feedback_service, memory_service, db_path):
        """提交反馈后，feedback_logs 表应写入一条对应记录。(M3-AC-10)"""
        memory_id = await memory_service.save("日志写入测试")
        input_id = str(uuid.uuid4())
        await feedback_service.submit(input_id, memory_id, valuable=True)

        async with aiosqlite.connect(db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM feedback_logs WHERE memory_id = ?", (memory_id,)
            ) as cursor:
                rows = await cursor.fetchall()

        assert len(rows) == 1, "应写入一条 feedback_logs 记录"

    @pytest.mark.asyncio
    async def test_feedback_log_fields_correct(self, feedback_service, memory_service, db_path):
        """Feedback 日志字段应与操作输入一致：memory_id、valuable、created_at。(M3-AC-10)"""
        memory_id = await memory_service.save("字段正确性测试")
        input_id = str(uuid.uuid4())
        await feedback_service.submit(input_id, memory_id, valuable=True)

        async with aiosqlite.connect(db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT memory_id, valuable, created_at FROM feedback_logs WHERE memory_id = ?",
                (memory_id,)
            ) as cursor:
                row = await cursor.fetchone()

        assert row is not None
        assert row["memory_id"] == memory_id, "memory_id 字段应与输入一致"
        assert bool(row["valuable"]) is True, "valuable 字段应与输入一致"
        assert row["created_at"] is not None and len(row["created_at"]) > 0, "created_at 不应为空"

    @pytest.mark.asyncio
    async def test_multiple_feedbacks_write_multiple_logs(self, feedback_service, memory_service, db_path):
        """多次提交反馈应写入多条日志记录。"""
        memory_id = await memory_service.save("多次反馈测试")
        input_id = str(uuid.uuid4())
        await feedback_service.submit(input_id, memory_id, valuable=True)
        await feedback_service.submit(input_id, memory_id, valuable=False)

        async with aiosqlite.connect(db_path) as db:
            async with db.execute(
                "SELECT COUNT(*) FROM feedback_logs WHERE memory_id = ?", (memory_id,)
            ) as cursor:
                count = (await cursor.fetchone())[0]

        assert count == 2

    @pytest.mark.asyncio
    async def test_get_feedback_logs_returns_history(self, feedback_service, memory_service, db_path):
        """get_feedback_logs() 应返回指定记忆的反馈历史。"""
        memory_id = await memory_service.save("反馈历史查询测试")
        input_id = str(uuid.uuid4())
        await feedback_service.submit(input_id, memory_id, valuable=True)
        logs = await feedback_service.get_feedback_logs(memory_id)
        assert len(logs) == 1
        assert logs[0].memory_id == memory_id
        assert logs[0].valuable is True


class TestFeedbackServiceMigrationTrigger:
    """测试层间迁移触发条件。"""

    @pytest.mark.asyncio
    async def test_promote_triggered_when_positive_feedback_for_cold_memory(
        self, feedback_service, memory_service, db_path
    ):
        """对冷层记忆提交正向反馈（建立关联）时，应触发升级。"""
        # 保存记忆后默认在冷层（total_score=0）
        memory_id = await memory_service.save("升级触发测试")
        assert not await memory_service.is_hot(memory_id), "记忆应已降级至冷层"

        # 提交正向反馈：建立关联（total_score>0）→ 触发升级
        input_id = str(uuid.uuid4())
        await feedback_service.submit(input_id, memory_id, valuable=True)
        # 等待 asyncio.create_task 中的 promote 协程执行完成
        await asyncio.sleep(0.1)

        assert await memory_service.is_hot(memory_id), "建立关联后应被升级至热层"

    @pytest.mark.asyncio
    async def test_demote_triggered_when_score_falls_to_zero(
        self, feedback_service, memory_service, db_path
    ):
        """热层记忆的关联评分降至 0（无关联）时，应触发降级。"""
        # 保存记忆（初始在冷层），先手动升入热层并预设关联链接
        memory_id = await memory_service.save("降级触发测试")
        assert not await memory_service.is_hot(memory_id), "新记忆应在冷层"

        input_id = str(uuid.uuid4())
        await insert_input_memory_link(db_path, input_id, memory_id, association_score=1.0)
        await memory_service.promote(memory_id)
        assert await memory_service.is_hot(memory_id), "预置后记忆应在热层"

        # 提交负向反馈：score 1.0 - 1.0 = 0 → 链接删除 → total=0（无关联）→ 触发降级
        await feedback_service.submit(input_id, memory_id, valuable=False)
        # 等待 asyncio.create_task 中的 demote 协程执行完成
        await asyncio.sleep(0.1)

        assert not await memory_service.is_hot(memory_id), "关联评分降至 0 后应被降级至冷层"

    @pytest.mark.asyncio
    async def test_no_migration_when_hot_memory_gets_positive_feedback(
        self, feedback_service, memory_service, db_path
    ):
        """对已在热层的记忆提交正向反馈，不应触发额外的升级操作（记忆保持在热层）。"""
        memory_id = await memory_service.save("无迁移测试")
        assert not await memory_service.is_hot(memory_id), "新记忆应在冷层"

        # 先建立关联并升入热层，构造“已在热层”的前置条件
        input_id = str(uuid.uuid4())
        await insert_input_memory_link(db_path, input_id, memory_id, association_score=1.0)
        await memory_service.promote(memory_id)
        assert await memory_service.is_hot(memory_id), "记忆应已在热层"

        # 再次提交正向反馈：已在热层时不应发生错误迁移
        await feedback_service.submit(input_id, memory_id, valuable=True)
        await asyncio.sleep(0.1)

        # 记忆应仍在热层，不应被错误迁移
        assert await memory_service.is_hot(memory_id), "已在热层的记忆应保持在热层"
