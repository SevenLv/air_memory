"""FeedbackService 单元测试：价值分更新边界、Feedback 日志写入、迁移触发条件。"""

import pytest
import pytest_asyncio
import aiosqlite

from air_memory.config import settings
from tests.conftest import insert_memory_value


async def _save_memory_with_db(memory_service, db_path: str,
                                content: str, value_score: float = 0.5,
                                tier: str = "cold") -> str:
    """存储记忆并在 SQLite 写入 memory_values 记录，模拟完整存储流程。"""
    from datetime import datetime, timezone
    memory_id = await memory_service.save(content)
    now = datetime.now(timezone.utc).isoformat()
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            "INSERT OR REPLACE INTO memory_values"
            " (memory_id, value_score, tier, feedback_count, created_at, updated_at)"
            " VALUES (?, ?, ?, 0, ?, ?)",
            (memory_id, value_score, tier, now, now),
        )
        await db.commit()
    return memory_id


class TestFeedbackServiceValueScore:
    """测试价值分更新逻辑。"""

    @pytest.mark.asyncio
    async def test_positive_feedback_increases_score(self, feedback_service, memory_service, db_path):
        """正向反馈应使价值分增加 FEEDBACK_STEP。"""
        memory_id = await _save_memory_with_db(memory_service, db_path, "正向反馈测试", value_score=0.5)
        new_score, _ = await feedback_service.submit(memory_id, valuable=True)
        expected = round(0.5 + settings.FEEDBACK_STEP, 4)
        assert new_score == expected, f"期望 {expected}，实际 {new_score}"

    @pytest.mark.asyncio
    async def test_negative_feedback_decreases_score(self, feedback_service, memory_service, db_path):
        """负向反馈应使价值分减少 FEEDBACK_STEP。"""
        memory_id = await _save_memory_with_db(memory_service, db_path, "负向反馈测试", value_score=0.5)
        new_score, _ = await feedback_service.submit(memory_id, valuable=False)
        expected = round(0.5 - settings.FEEDBACK_STEP, 4)
        assert new_score == expected, f"期望 {expected}，实际 {new_score}"

    @pytest.mark.asyncio
    async def test_value_score_upper_bound_is_1_0(self, feedback_service, memory_service, db_path):
        """价值分不得超过 1.0 上限（边界值测试）。(M3-AC-07)"""
        # 从 0.95 出发，加 0.1 理论上会超过 1.0，应被截断到 1.0
        memory_id = await _save_memory_with_db(memory_service, db_path, "上限边界测试", value_score=0.95)
        new_score, _ = await feedback_service.submit(memory_id, valuable=True)
        assert new_score == 1.0, f"价值分上限应为 1.0，实际 {new_score}"

    @pytest.mark.asyncio
    async def test_value_score_lower_bound_is_0_0(self, feedback_service, memory_service, db_path):
        """价值分不得低于 0.0 下限（边界值测试）。(M3-AC-07)"""
        # 从 0.05 出发，减 0.1 理论上会低于 0.0，应被截断到 0.0
        memory_id = await _save_memory_with_db(memory_service, db_path, "下限边界测试", value_score=0.05)
        new_score, _ = await feedback_service.submit(memory_id, valuable=False)
        assert new_score == 0.0, f"价值分下限应为 0.0，实际 {new_score}"

    @pytest.mark.asyncio
    async def test_value_score_exactly_at_1_0_stays(self, feedback_service, memory_service, db_path):
        """价值分已为 1.0 时，正向反馈后仍应为 1.0。(M3-AC-07)"""
        memory_id = await _save_memory_with_db(memory_service, db_path, "上限保持测试", value_score=1.0)
        new_score, _ = await feedback_service.submit(memory_id, valuable=True)
        assert new_score == 1.0

    @pytest.mark.asyncio
    async def test_value_score_exactly_at_0_0_stays(self, feedback_service, memory_service, db_path):
        """价值分已为 0.0 时，负向反馈后仍应为 0.0。(M3-AC-07)"""
        memory_id = await _save_memory_with_db(memory_service, db_path, "下限保持测试", value_score=0.0)
        new_score, _ = await feedback_service.submit(memory_id, valuable=False)
        assert new_score == 0.0

    @pytest.mark.asyncio
    async def test_submit_returns_tier(self, feedback_service, memory_service, db_path):
        """submit() 应返回当前 tier 字符串。"""
        memory_id = await _save_memory_with_db(memory_service, db_path, "层级返回测试")
        _, tier = await feedback_service.submit(memory_id, valuable=True)
        assert tier in ("hot", "cold")

    @pytest.mark.asyncio
    async def test_submit_nonexistent_memory_raises(self, feedback_service):
        """对不存在的 memory_id 提交反馈应抛出 ValueError。"""
        with pytest.raises(ValueError, match="记忆不存在"):
            await feedback_service.submit("nonexistent-id", valuable=True)


class TestFeedbackServiceLogWriting:
    """测试 Feedback 日志写入功能。(M3-AC-10)"""

    @pytest.mark.asyncio
    async def test_feedback_log_written_on_submit(self, feedback_service, memory_service, db_path):
        """提交反馈后，feedback_logs 表应写入一条对应记录。(M3-AC-10)"""
        memory_id = await _save_memory_with_db(memory_service, db_path, "日志写入测试")
        await feedback_service.submit(memory_id, valuable=True)

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
        memory_id = await _save_memory_with_db(memory_service, db_path, "字段正确性测试")
        await feedback_service.submit(memory_id, valuable=True)

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
        memory_id = await _save_memory_with_db(memory_service, db_path, "多次反馈测试")
        await feedback_service.submit(memory_id, valuable=True)
        await feedback_service.submit(memory_id, valuable=False)

        async with aiosqlite.connect(db_path) as db:
            async with db.execute(
                "SELECT COUNT(*) FROM feedback_logs WHERE memory_id = ?", (memory_id,)
            ) as cursor:
                count = (await cursor.fetchone())[0]

        assert count == 2

    @pytest.mark.asyncio
    async def test_get_feedback_logs_returns_history(self, feedback_service, memory_service, db_path):
        """get_feedback_logs() 应返回指定记忆的反馈历史。"""
        memory_id = await _save_memory_with_db(memory_service, db_path, "反馈历史查询测试")
        await feedback_service.submit(memory_id, valuable=True)
        logs = await feedback_service.get_feedback_logs(memory_id)
        assert len(logs) == 1
        assert logs[0].memory_id == memory_id
        assert logs[0].valuable is True


class TestFeedbackServiceMigrationTrigger:
    """测试层间迁移触发条件。"""

    @pytest.mark.asyncio
    async def test_promote_triggered_when_score_reaches_threshold(
        self, feedback_service, memory_service, db_path
    ):
        """价值分达到 PROMOTE_THRESHOLD 时（冷层），应触发升级（tier 返回 'hot'）。"""
        # 设置价值分略低于升级阈值，一次正向反馈后超过
        score = settings.PROMOTE_THRESHOLD - settings.FEEDBACK_STEP
        memory_id = await _save_memory_with_db(
            memory_service, db_path, "升级触发测试", value_score=score, tier="cold"
        )
        _, tier = await feedback_service.submit(memory_id, valuable=True)
        assert tier == "hot", f"价值分达到升级阈值后 tier 应为 'hot'，实际 {tier}"

    @pytest.mark.asyncio
    async def test_demote_triggered_when_score_falls_below_threshold(
        self, feedback_service, memory_service, db_path
    ):
        """价值分低于 DEMOTE_THRESHOLD 时（热层），应触发降级（tier 返回 'cold'）。"""
        # 初始分值恰好等于降级阈值（在热层），一次负向反馈后低于阈值
        # 例如：DEMOTE_THRESHOLD=0.3，FEEDBACK_STEP=0.1 → 0.3 - 0.1 = 0.2 < 0.3
        score = settings.DEMOTE_THRESHOLD
        memory_id = await _save_memory_with_db(
            memory_service, db_path, "降级触发测试", value_score=score, tier="hot"
        )
        # 将记忆放入热层
        await memory_service.promote(memory_id, value_score=score)
        _, tier = await feedback_service.submit(memory_id, valuable=False)
        assert tier == "cold", f"价值分低于降级阈值后 tier 应为 'cold'，实际 {tier}"

    @pytest.mark.asyncio
    async def test_no_migration_when_score_stays_within_range(
        self, feedback_service, memory_service, db_path
    ):
        """价值分在阈值范围内变动时不应触发迁移。"""
        # 从低于升级阈值的分值出发，一次正向反馈后仍低于升级阈值，不触发升级
        # PROMOTE_THRESHOLD=0.6，FEEDBACK_STEP=0.1 → 从 0.4 变为 0.5 < 0.6
        score = settings.PROMOTE_THRESHOLD - settings.FEEDBACK_STEP * 2
        memory_id = await _save_memory_with_db(
            memory_service, db_path, "无迁移测试", value_score=score, tier="cold"
        )
        _, tier = await feedback_service.submit(memory_id, valuable=True)
        assert tier == "cold", "价值分未达升级阈值不应迁移"

    @pytest.mark.asyncio
    async def test_get_memory_value_score_returns_correct_data(
        self, feedback_service, memory_service, db_path
    ):
        """get_memory_value_score() 应返回正确的评分数据。"""
        memory_id = await _save_memory_with_db(
            memory_service, db_path, "评分查询测试", value_score=0.7
        )
        data = await feedback_service.get_memory_value_score(memory_id)
        assert data is not None
        assert data["memory_id"] == memory_id
        assert data["value_score"] == 0.7

    @pytest.mark.asyncio
    async def test_get_memory_value_score_returns_none_for_nonexistent(self, feedback_service):
        """不存在的 memory_id 查询应返回 None。"""
        data = await feedback_service.get_memory_value_score("nonexistent-id")
        assert data is None
