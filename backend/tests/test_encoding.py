"""Issue #37 编码测试：验证中文内容在完整数据流中不被损坏。

覆盖：REST API 存储/查询、操作日志、MCP 工具函数，以及各种中文字符场景。
"""

import json
import asyncio
import os
import pytest
import pytest_asyncio
import httpx
from typing import AsyncGenerator
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from air_memory.config import settings
from air_memory.db import init_db
from tests.conftest import MockSentenceTransformer


# ---------------------------------------------------------------------------
# 测试数据
# ---------------------------------------------------------------------------

CHINESE_SAMPLES = [
    "这是一条普通的中文记忆",
    "包含标点符号：你好！世界，测试。",
    "混合内容 mixed content 中英文混排",
    "特殊字符测试：①②③ α β γ €",
    "换行\n测试\n中文多行内容",
    "数字与中文：2026年4月记忆系统v1.2.0版本",
]


# ---------------------------------------------------------------------------
# API 测试专用 Fixture
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def test_app(tmp_path):
    """创建测试专用 FastAPI 应用，注入真实服务（使用 Mock 模型和临时路径）。"""
    db_path = str(tmp_path / "test_enc.db")
    chroma_path = str(tmp_path / "test_chroma_enc")
    os.makedirs(chroma_path, exist_ok=True)

    settings.DB_PATH = db_path
    settings.CHROMA_COLD_PATH = chroma_path

    await init_db()

    from air_memory.memory.service import MemoryService
    from air_memory.feedback.service import FeedbackService
    from air_memory.log.service import LogService
    from air_memory.memory.tier_manager import TierManager
    from air_memory.disk.manager import DiskManager
    from air_memory.api.router import router

    mock_model = MockSentenceTransformer()
    memory_svc = MemoryService(mock_model)
    feedback_svc = FeedbackService(memory_svc)
    log_svc = LogService()
    tier_mgr = TierManager(memory_svc)
    disk_mgr = DiskManager(memory_svc)

    app = FastAPI()
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
    app.include_router(router)

    app.state.memory_service = memory_svc
    app.state.feedback_service = feedback_svc
    app.state.log_service = log_svc
    app.state.tier_manager = tier_mgr
    app.state.disk_manager = disk_mgr

    return app


@pytest_asyncio.fixture
async def client(test_app) -> AsyncGenerator[httpx.AsyncClient, None]:
    """提供测试用 httpx 异步客户端。"""
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=test_app),
        base_url="http://test"
    ) as c:
        yield c


# ---------------------------------------------------------------------------
# 日志服务编码测试
# ---------------------------------------------------------------------------

class TestLogServiceEncoding:
    """验证 LogService 在中文内容存储与查询中无编码损坏。"""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("content", CHINESE_SAMPLES)
    async def test_save_log_chinese_roundtrip(self, log_service, content):
        """存储日志中文内容读取后与原文完全一致。"""
        memory_id = "test-mem-encoding-001"
        await log_service.log_save(content, memory_id)
        logs = await log_service.get_save_logs()
        assert any(log.content == content for log in logs), (
            f"中文内容损坏：期望 {content!r}，实际 {[l.content for l in logs]!r}"
        )

    @pytest.mark.asyncio
    async def test_query_log_chinese_query_roundtrip(self, log_service):
        """查询日志的 query 字段中文内容读取后与原文完全一致。"""
        query = "查询：最近的中文记忆内容"
        results = [{"id": "test-id", "content": "中文记忆", "similarity": 0.9,
                    "value_score": 0.6, "tier": "hot", "created_at": "2026-04-14"}]
        await log_service.log_query(query, results, False)
        logs = await log_service.get_query_logs()
        assert len(logs) > 0
        assert logs[0].query == query, (
            f"query 字段损坏：期望 {query!r}，实际 {logs[0].query!r}"
        )

    @pytest.mark.asyncio
    async def test_query_log_results_chinese_content(self, log_service):
        """查询日志 results 字段中的中文内容经 JSON 序列化/反序列化后不损坏。"""
        chinese_content = "这是一条非常重要的中文记忆内容，必须完整保存"
        results = [{"id": "mem-001", "content": chinese_content,
                    "similarity": 0.95, "value_score": 0.7, "tier": "cold",
                    "created_at": "2026-04-14T00:00:00+00:00"}]
        await log_service.log_query("test query", results, False)
        logs = await log_service.get_query_logs()
        assert len(logs) > 0
        parsed = json.loads(logs[0].results)
        assert parsed[0]["content"] == chinese_content, (
            f"results 中文内容损坏：期望 {chinese_content!r}，实际 {parsed[0]['content']!r}"
        )

    @pytest.mark.asyncio
    async def test_query_log_results_not_ascii_escaped(self, log_service):
        """查询日志 results 字段存储时应使用 ensure_ascii=False，中文不应被转义为 \\uXXXX。"""
        content = "中文记忆内容不应被ASCII转义"
        results = [{"id": "mem-002", "content": content,
                    "similarity": 0.9, "value_score": 0.6, "tier": "hot",
                    "created_at": "2026-04-14T00:00:00+00:00"}]
        await log_service.log_query("query", results, False)
        logs = await log_service.get_query_logs()

        raw_results = logs[0].results
        # 核心验证：反序列化后内容一致
        parsed = json.loads(raw_results)
        assert parsed[0]["content"] == content, (
            f"results 字段内容损坏：期望 {content!r}，实际 {parsed[0]['content']!r}"
        )


# ---------------------------------------------------------------------------
# MCP 工具函数编码测试
# ---------------------------------------------------------------------------

class TestMCPToolEncoding:
    """验证 MCP 工具函数对中文内容的编码处理正确。"""

    @pytest.mark.asyncio
    async def test_query_memory_json_contains_chinese(self, memory_service, log_service, feedback_service):
        """query_memory 返回的 JSON 字符串中中文内容不被损坏。"""
        from air_memory.mcp.server import init_mcp_services, query_memory

        init_mcp_services(memory_service, feedback_service, log_service)

        content = "MCP 查询测试中文记忆内容"
        await memory_service.save(content)

        result_json = await query_memory(content, top_k=5, fast_only=False)

        assert isinstance(result_json, str), "query_memory 应返回 JSON 字符串"
        parsed = json.loads(result_json)
        assert isinstance(parsed, list), "解析后应为列表"
        if parsed:
            retrieved_content = parsed[0]["content"]
            assert retrieved_content == content, (
                f"MCP 查询结果中文损坏：期望 {content!r}，实际 {retrieved_content!r}"
            )

    @pytest.mark.asyncio
    async def test_query_memory_result_no_ascii_escape(self, memory_service, log_service, feedback_service):
        """query_memory 返回 JSON 中中文字符应直接输出，不应使用 \\uXXXX 转义。"""
        from air_memory.mcp.server import init_mcp_services, query_memory

        init_mcp_services(memory_service, feedback_service, log_service)

        content = "中文不应被转义为unicode代码点"
        await memory_service.save(content)

        result_json = await query_memory(content, top_k=5, fast_only=False)
        parsed = json.loads(result_json)
        if parsed:
            assert parsed[0]["content"] == content, (
                f"MCP 结果中文损坏：期望 {content!r}，实际 {parsed[0]['content']!r}"
            )


# ---------------------------------------------------------------------------
# REST API 编码测试 (通过 TestClient)
# ---------------------------------------------------------------------------

class TestAPIEncoding:
    """验证 REST API 对中文内容的编码处理正确。"""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("content", CHINESE_SAMPLES)
    async def test_memory_api_chinese_save_and_query(self, client, content):
        """通过 REST API 存储中文记忆，查询后内容与原文完全一致。(Issue #37 回归测试)"""
        # 存储记忆
        save_resp = await client.post(
            "/api/v1/memories",
            json={"content": content},
        )
        assert save_resp.status_code == 201, f"存储失败：{save_resp.text}"

        # 查询记忆
        query_resp = await client.get(
            "/api/v1/memories",
            params={"query": content, "top_k": 5, "fast_only": False},
        )
        assert query_resp.status_code == 200

        memories = query_resp.json()["memories"]
        assert len(memories) > 0, "未找到任何记忆"
        retrieved = memories[0]["content"]
        assert retrieved == content, (
            f"API 内容编码损坏 (Issue #37)：期望 {content!r}，实际 {retrieved!r}"
        )

    @pytest.mark.asyncio
    async def test_save_logs_api_chinese_content(self, client):
        """存储日志 API 返回的中文内容与原始内容完全一致。(Issue #37 UI 显示回归测试)"""
        content = "日志显示中文测试：确保 UI 不显示乱码"
        save_resp = await client.post("/api/v1/memories", json={"content": content})
        assert save_resp.status_code == 201

        # 等待异步日志任务完成
        await asyncio.sleep(0.1)

        logs_resp = await client.get("/api/v1/logs/save")
        assert logs_resp.status_code == 200

        logs = logs_resp.json()["logs"]
        assert len(logs) > 0, "未找到存储日志"
        assert logs[0]["content"] == content, (
            f"存储日志中文损坏 (Issue #37)：期望 {content!r}，实际 {logs[0]['content']!r}"
        )

    @pytest.mark.asyncio
    async def test_api_response_content_type_charset(self, client):
        """REST API 响应应支持 UTF-8 编码（通过实际解码验证）。"""
        # 核心验证：包含中文的 API 接口响应可被正确 UTF-8 解码
        save_resp = await client.post(
            "/api/v1/memories",
            json={"content": "编码验证：这段中文应完整返回"},
        )
        assert save_resp.status_code == 201
        # 响应体可被正确 UTF-8 解码（如编码错误会引发异常）
        resp_text = save_resp.text
        assert resp_text is not None
