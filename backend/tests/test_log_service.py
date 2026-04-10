"""LogService 单元测试：存储日志写入和查询日志写入。(M3-AC-10)"""

import json

import pytest
import pytest_asyncio
import aiosqlite

from air_memory.config import settings


class TestLogServiceSaveLogs:
    """测试 LogService 存储操作日志。"""

    @pytest.mark.asyncio
    async def test_log_save_writes_to_db(self, log_service, db_path):
        """log_save() 应向 save_logs 表写入一条记录。(M3-AC-10)"""
        await log_service.log_save(content="测试记忆内容", memory_id="test-id-001")

        async with aiosqlite.connect(db_path) as db:
            async with db.execute("SELECT COUNT(*) FROM save_logs") as cursor:
                count = (await cursor.fetchone())[0]

        assert count == 1

    @pytest.mark.asyncio
    async def test_log_save_memory_id_correct(self, log_service, db_path):
        """存储日志的 memory_id 字段应与操作输入一致。(M3-AC-10)"""
        memory_id = "test-memory-id-12345"
        await log_service.log_save(content="内容", memory_id=memory_id)

        async with aiosqlite.connect(db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT memory_id FROM save_logs WHERE memory_id = ?", (memory_id,)
            ) as cursor:
                row = await cursor.fetchone()

        assert row is not None
        assert row["memory_id"] == memory_id, f"memory_id 应为 {memory_id}"

    @pytest.mark.asyncio
    async def test_log_save_content_correct(self, log_service, db_path):
        """存储日志的 content 字段应与操作输入完全一致。(M3-AC-10)"""
        content = "这是一段完整的记忆内容，包含中文字符和符号！"
        await log_service.log_save(content=content, memory_id="id-001")

        async with aiosqlite.connect(db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT content FROM save_logs WHERE memory_id = ?", ("id-001",)
            ) as cursor:
                row = await cursor.fetchone()

        assert row is not None
        assert row["content"] == content, (
            f"content 字段应与输入一致，期望={content!r}，实际={row['content']!r}"
        )

    @pytest.mark.asyncio
    async def test_log_save_created_at_not_empty(self, log_service, db_path):
        """存储日志的 created_at 字段不应为空。(M3-AC-10)"""
        await log_service.log_save(content="内容", memory_id="id-002")

        async with aiosqlite.connect(db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT created_at FROM save_logs WHERE memory_id = ?", ("id-002",)
            ) as cursor:
                row = await cursor.fetchone()

        assert row is not None
        assert row["created_at"] is not None
        assert len(row["created_at"]) > 0, "created_at 不应为空"

    @pytest.mark.asyncio
    async def test_log_save_memory_deleted_default_false(self, log_service, db_path):
        """新写入的存储日志 memory_deleted 默认应为 0（False）。"""
        await log_service.log_save(content="内容", memory_id="id-003")

        async with aiosqlite.connect(db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT memory_deleted FROM save_logs WHERE memory_id = ?", ("id-003",)
            ) as cursor:
                row = await cursor.fetchone()

        assert row is not None
        assert row["memory_deleted"] == 0

    @pytest.mark.asyncio
    async def test_get_save_logs_returns_list(self, log_service, db_path):
        """get_save_logs() 应返回 SaveLog 列表。"""
        await log_service.log_save(content="查询测试", memory_id="id-100")
        logs = await log_service.get_save_logs()
        assert isinstance(logs, list)
        assert len(logs) >= 1

    @pytest.mark.asyncio
    async def test_get_save_logs_content_correct(self, log_service, db_path):
        """get_save_logs() 返回的日志 content 应与写入时一致。(M3-AC-10)"""
        content = "日志查询内容验证"
        memory_id = "id-200"
        await log_service.log_save(content=content, memory_id=memory_id)
        logs = await log_service.get_save_logs()
        target = next((l for l in logs if l.memory_id == memory_id), None)
        assert target is not None, "应能找到写入的日志"
        assert target.content == content, (
            f"查询到的 content 应与写入一致，期望={content!r}，实际={target.content!r}"
        )

    @pytest.mark.asyncio
    async def test_get_save_logs_ordered_by_id_desc(self, log_service, db_path):
        """get_save_logs() 应按 id 降序返回。"""
        await log_service.log_save(content="第一条", memory_id="id-301")
        await log_service.log_save(content="第二条", memory_id="id-302")
        logs = await log_service.get_save_logs()
        assert len(logs) >= 2
        # 最新写入的应排在前面
        assert logs[0].id > logs[1].id


class TestLogServiceQueryLogs:
    """测试 LogService 查询操作日志。"""

    @pytest.mark.asyncio
    async def test_log_query_writes_to_db(self, log_service, db_path):
        """log_query() 应向 query_logs 表写入一条记录。(M3-AC-10)"""
        await log_service.log_query(query="搜索内容", results=[], fast_only=False)

        async with aiosqlite.connect(db_path) as db:
            async with db.execute("SELECT COUNT(*) FROM query_logs") as cursor:
                count = (await cursor.fetchone())[0]

        assert count == 1

    @pytest.mark.asyncio
    async def test_log_query_query_field_correct(self, log_service, db_path):
        """查询日志的 query 字段应与操作输入一致。(M3-AC-10)"""
        query_text = "深度学习模型推理"
        await log_service.log_query(query=query_text, results=[], fast_only=False)

        async with aiosqlite.connect(db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT query FROM query_logs WHERE query = ?", (query_text,)
            ) as cursor:
                row = await cursor.fetchone()

        assert row is not None
        assert row["query"] == query_text

    @pytest.mark.asyncio
    async def test_log_query_fast_only_field_correct(self, log_service, db_path):
        """查询日志的 fast_only 字段应与操作输入一致。(M3-AC-10)"""
        await log_service.log_query(query="快速查询测试", results=[], fast_only=True)

        async with aiosqlite.connect(db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT fast_only FROM query_logs WHERE query = ?", ("快速查询测试",)
            ) as cursor:
                row = await cursor.fetchone()

        assert row is not None
        assert row["fast_only"] == 1, "fast_only=True 应存储为 1"

    @pytest.mark.asyncio
    async def test_log_query_results_serialized(self, log_service, db_path):
        """查询日志的 results 应以 JSON 字符串存储。(M3-AC-10)"""
        results = [{"id": "abc", "content": "内容", "similarity": 0.9}]
        await log_service.log_query(query="结果序列化测试", results=results, fast_only=False)

        async with aiosqlite.connect(db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT results FROM query_logs WHERE query = ?", ("结果序列化测试",)
            ) as cursor:
                row = await cursor.fetchone()

        assert row is not None
        parsed = json.loads(row["results"])
        assert len(parsed) == 1
        assert parsed[0]["id"] == "abc"
        assert parsed[0]["content"] == "内容"

    @pytest.mark.asyncio
    async def test_log_query_created_at_not_empty(self, log_service, db_path):
        """查询日志的 created_at 字段不应为空。(M3-AC-10)"""
        await log_service.log_query(query="时间戳测试", results=[], fast_only=False)

        async with aiosqlite.connect(db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT created_at FROM query_logs WHERE query = ?", ("时间戳测试",)
            ) as cursor:
                row = await cursor.fetchone()

        assert row is not None
        assert row["created_at"] is not None
        assert len(row["created_at"]) > 0

    @pytest.mark.asyncio
    async def test_get_query_logs_returns_list(self, log_service, db_path):
        """get_query_logs() 应返回 QueryLog 列表。"""
        await log_service.log_query(query="列表查询测试", results=[], fast_only=False)
        logs = await log_service.get_query_logs()
        assert isinstance(logs, list)
        assert len(logs) >= 1

    @pytest.mark.asyncio
    async def test_get_query_logs_fields_correct(self, log_service, db_path):
        """get_query_logs() 返回的日志各字段应与写入时一致。(M3-AC-10)"""
        query_text = "字段正确性验证查询"
        await log_service.log_query(query=query_text, results=[{"id": "x"}], fast_only=True)
        logs = await log_service.get_query_logs()
        target = next((l for l in logs if l.query == query_text), None)
        assert target is not None
        assert target.query == query_text
        assert target.fast_only is True

    @pytest.mark.asyncio
    async def test_get_query_logs_ordered_by_id_desc(self, log_service, db_path):
        """get_query_logs() 应按 id 降序返回。"""
        await log_service.log_query(query="第一次查询", results=[], fast_only=False)
        await log_service.log_query(query="第二次查询", results=[], fast_only=False)
        logs = await log_service.get_query_logs()
        assert len(logs) >= 2
        assert logs[0].id > logs[1].id
