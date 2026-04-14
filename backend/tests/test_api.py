"""REST API 接口集成测试：全部接口路径的正常场景和异常场景（含 Pydantic 校验）。"""

import asyncio
import os
import tempfile
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from unittest.mock import patch, MagicMock

import pytest
import pytest_asyncio
import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from air_memory.api.router import router
from air_memory.config import settings
from air_memory.db import init_db
from tests.conftest import MockSentenceTransformer


# ---------------------------------------------------------------------------
# 测试应用 Fixture
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def test_app(tmp_path):
    """创建测试专用 FastAPI 应用，注入真实服务（使用 Mock 模型和临时路径）。"""
    db_path = str(tmp_path / "test_api.db")
    chroma_path = str(tmp_path / "test_chroma")
    os.makedirs(chroma_path, exist_ok=True)

    # 覆盖路径配置
    settings.DB_PATH = db_path
    settings.CHROMA_COLD_PATH = chroma_path

    # 初始化数据库
    await init_db()

    # 创建 Mock 模型和服务
    from air_memory.memory.service import MemoryService
    from air_memory.feedback.service import FeedbackService
    from air_memory.log.service import LogService
    from air_memory.memory.tier_manager import TierManager
    from air_memory.disk.manager import DiskManager

    mock_model = MockSentenceTransformer()
    memory_svc = MemoryService(mock_model)
    feedback_svc = FeedbackService(memory_svc)
    log_svc = LogService()
    tier_mgr = TierManager(memory_svc)
    disk_mgr = DiskManager(memory_svc)

    app = FastAPI()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router)

    # 挂载服务到 app.state
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
# POST /api/v1/memories 存储记忆
# ---------------------------------------------------------------------------

class TestSaveMemoryAPI:
    """测试 POST /api/v1/memories 接口。"""

    @pytest.mark.asyncio
    async def test_save_memory_success(self, client):
        """正常存储请求应返回 201 和包含 memory_id 的响应。"""
        resp = await client.post("/api/v1/memories", json={"content": "测试记忆内容"})
        assert resp.status_code == 201
        data = resp.json()
        assert "memory_id" in data
        assert data["tier"] == "hot"
        assert data["message"] == "ok"

    @pytest.mark.asyncio
    async def test_save_memory_missing_content(self, client):
        """缺少必填字段 content 应返回 422 Unprocessable Entity。(M3-AC-08)"""
        resp = await client.post("/api/v1/memories", json={})
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_save_memory_empty_content(self, client):
        """content 为空字符串（min_length=1 校验）应返回 422。(M3-AC-08)"""
        resp = await client.post("/api/v1/memories", json={"content": ""})
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_save_memory_invalid_body_type(self, client):
        """非 JSON 格式请求体应返回 422。(M3-AC-08)"""
        resp = await client.post(
            "/api/v1/memories",
            content="not json",
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_save_memory_returns_unique_ids(self, client):
        """多次存储应返回不同的 memory_id。"""
        resp1 = await client.post("/api/v1/memories", json={"content": "内容一"})
        resp2 = await client.post("/api/v1/memories", json={"content": "内容二"})
        assert resp1.status_code == 201
        assert resp2.status_code == 201
        assert resp1.json()["memory_id"] != resp2.json()["memory_id"]


# ---------------------------------------------------------------------------
# GET /api/v1/memories 查询记忆
# ---------------------------------------------------------------------------

class TestQueryMemoriesAPI:
    """测试 GET /api/v1/memories 接口。"""

    @pytest.mark.asyncio
    async def test_query_memories_success(self, client):
        """正常查询请求应返回 200 和记忆列表。"""
        await client.post("/api/v1/memories", json={"content": "查询测试内容"})
        resp = await client.get("/api/v1/memories", params={"query": "查询测试"})
        assert resp.status_code == 200
        data = resp.json()
        assert "memories" in data
        assert "count" in data
        assert "query_mode" in data

    @pytest.mark.asyncio
    async def test_query_memories_missing_query(self, client):
        """缺少必填参数 query 应返回 422。(M3-AC-08)"""
        resp = await client.get("/api/v1/memories")
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_query_memories_empty_query(self, client):
        """query 为空字符串（min_length=1 校验）应返回 422。(M3-AC-08)"""
        resp = await client.get("/api/v1/memories", params={"query": ""})
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_query_memories_top_k_out_of_range(self, client):
        """top_k > 100 应返回 422。(M3-AC-08)"""
        resp = await client.get(
            "/api/v1/memories", params={"query": "测试", "top_k": 200}
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_query_memories_fast_only_mode(self, client):
        """fast_only=True 时 query_mode 应为 'fast'。"""
        resp = await client.get(
            "/api/v1/memories",
            params={"query": "快速模式测试", "fast_only": True},
        )
        assert resp.status_code == 200
        assert resp.json()["query_mode"] == "fast"

    @pytest.mark.asyncio
    async def test_query_memories_deep_mode(self, client):
        """fast_only=False 时 query_mode 应为 'deep'。"""
        resp = await client.get(
            "/api/v1/memories",
            params={"query": "深度模式测试", "fast_only": False},
        )
        assert resp.status_code == 200
        assert resp.json()["query_mode"] == "deep"

    @pytest.mark.asyncio
    async def test_query_memories_content_in_deep_results(self, client):
        """深度查询应返回存储时的完整 content 字段。(M3-AC-09)"""
        content = "API 内容正确性测试：深度模式"
        save_resp = await client.post("/api/v1/memories", json={"content": content})
        memory_id = save_resp.json()["memory_id"]

        query_resp = await client.get(
            "/api/v1/memories",
            params={"query": "内容正确性", "fast_only": False, "top_k": 10},
        )
        assert query_resp.status_code == 200
        memories = query_resp.json()["memories"]
        target = next((m for m in memories if m["id"] == memory_id), None)
        assert target is not None, "深度查询应能找到刚存储的记忆"
        assert target["content"] == content, (
            f"查询返回的 content 应与存储输入一致，期望={content!r}，实际={target['content']!r}"
        )


# ---------------------------------------------------------------------------
# DELETE /api/v1/memories/{memory_id} 删除记忆
# ---------------------------------------------------------------------------

class TestDeleteMemoryAPI:
    """测试 DELETE /api/v1/memories/{memory_id} 接口。"""

    @pytest.mark.asyncio
    async def test_delete_memory_success(self, client):
        """正常删除请求应返回 200 和 {'message': 'ok'}。"""
        save_resp = await client.post("/api/v1/memories", json={"content": "待删除记忆"})
        memory_id = save_resp.json()["memory_id"]

        del_resp = await client.delete(f"/api/v1/memories/{memory_id}")
        assert del_resp.status_code == 200
        assert del_resp.json()["message"] == "ok"

    @pytest.mark.asyncio
    async def test_delete_nonexistent_memory(self, client):
        """删除不存在的记忆应返回 200（幂等操作）。"""
        resp = await client.delete("/api/v1/memories/nonexistent-id")
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# POST /api/v1/memories/{memory_id}/feedback 提交反馈
# ---------------------------------------------------------------------------

class TestFeedbackMemoryAPI:
    """测试 POST /api/v1/memories/{memory_id}/feedback 接口。"""

    @pytest.mark.asyncio
    async def test_feedback_memory_success(self, client):
        """正常反馈请求应返回 200 和更新后的 value_score。"""
        save_resp = await client.post("/api/v1/memories", json={"content": "反馈测试"})
        memory_id = save_resp.json()["memory_id"]
        # 等待异步日志写入
        await asyncio.sleep(0.1)

        fb_resp = await client.post(
            f"/api/v1/memories/{memory_id}/feedback",
            json={"valuable": True},
        )
        assert fb_resp.status_code == 200
        data = fb_resp.json()
        assert "memory_id" in data
        assert "value_score" in data
        assert "tier" in data

    @pytest.mark.asyncio
    async def test_feedback_memory_not_found(self, client):
        """对不存在的 memory_id 提交反馈应返回 404。"""
        resp = await client.post(
            "/api/v1/memories/nonexistent-id/feedback",
            json={"valuable": True},
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_feedback_missing_valuable(self, client):
        """缺少必填字段 valuable 应返回 422。(M3-AC-08)"""
        save_resp = await client.post("/api/v1/memories", json={"content": "反馈字段测试"})
        memory_id = save_resp.json()["memory_id"]

        resp = await client.post(f"/api/v1/memories/{memory_id}/feedback", json={})
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_feedback_invalid_valuable_type(self, client):
        """valuable 字段类型错误（传入数组类型）应返回 422。(M3-AC-08)"""
        save_resp = await client.post("/api/v1/memories", json={"content": "类型错误测试"})
        memory_id = save_resp.json()["memory_id"]

        resp = await client.post(
            f"/api/v1/memories/{memory_id}/feedback",
            json={"valuable": [1, 2, 3]},  # 数组不能转换为 bool，触发 422
        )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# GET /api/v1/memories/{memory_id}/feedback/logs 反馈日志
# ---------------------------------------------------------------------------

class TestGetFeedbackLogsAPI:
    """测试 GET /api/v1/memories/{memory_id}/feedback/logs 接口。"""

    @pytest.mark.asyncio
    async def test_get_feedback_logs_success(self, client):
        """正常请求应返回 200 和反馈日志列表。"""
        save_resp = await client.post("/api/v1/memories", json={"content": "反馈日志测试"})
        memory_id = save_resp.json()["memory_id"]
        await asyncio.sleep(0.1)

        await client.post(
            f"/api/v1/memories/{memory_id}/feedback", json={"valuable": True}
        )

        logs_resp = await client.get(f"/api/v1/memories/{memory_id}/feedback/logs")
        assert logs_resp.status_code == 200
        data = logs_resp.json()
        assert "logs" in data
        assert "count" in data

    @pytest.mark.asyncio
    async def test_get_feedback_logs_page_size_too_large(self, client):
        """page_size > 100 应返回 422。(M3-AC-08)"""
        resp = await client.get(
            "/api/v1/memories/test-id/feedback/logs",
            params={"page_size": 999},
        )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# GET /api/v1/memories/{memory_id}/value-score 价值评分
# ---------------------------------------------------------------------------

class TestGetValueScoreAPI:
    """测试 GET /api/v1/memories/{memory_id}/value-score 接口。"""

    @pytest.mark.asyncio
    async def test_get_value_score_success(self, client):
        """正常请求应返回 200 和价值评分数据。"""
        save_resp = await client.post("/api/v1/memories", json={"content": "价值评分查询测试"})
        memory_id = save_resp.json()["memory_id"]
        await asyncio.sleep(0.1)

        vs_resp = await client.get(f"/api/v1/memories/{memory_id}/value-score")
        assert vs_resp.status_code == 200
        data = vs_resp.json()
        assert data["memory_id"] == memory_id
        assert "value_score" in data
        assert "tier" in data
        assert "feedback_count" in data

    @pytest.mark.asyncio
    async def test_get_value_score_not_found(self, client):
        """查询不存在的 memory_id 价值评分应返回 404。"""
        resp = await client.get("/api/v1/memories/nonexistent-id/value-score")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# GET /api/v1/logs/save 存储日志
# ---------------------------------------------------------------------------

class TestGetSaveLogsAPI:
    """测试 GET /api/v1/logs/save 接口。"""

    @pytest.mark.asyncio
    async def test_get_save_logs_success(self, client):
        """正常请求应返回 200 和日志列表。"""
        resp = await client.get("/api/v1/logs/save")
        assert resp.status_code == 200
        data = resp.json()
        assert "logs" in data
        assert "count" in data

    @pytest.mark.asyncio
    async def test_get_save_logs_after_save(self, client):
        """存储记忆后，日志列表应包含对应记录。"""
        content = "存储后日志验证"
        await client.post("/api/v1/memories", json={"content": content})
        await asyncio.sleep(0.1)  # 等待异步日志写入

        resp = await client.get("/api/v1/logs/save")
        assert resp.status_code == 200
        logs = resp.json()["logs"]
        assert any(l["content"] == content for l in logs), "存储日志应包含刚写入的内容"

    @pytest.mark.asyncio
    async def test_save_logs_response_has_is_garbled_field(self, client):
        """存储日志 API 响应中每条记录应包含 is_garbled 字段。"""
        content = "测试 is_garbled 字段"
        await client.post("/api/v1/memories", json={"content": content})
        await asyncio.sleep(0.1)

        resp = await client.get("/api/v1/logs/save")
        assert resp.status_code == 200
        logs = resp.json()["logs"]
        assert len(logs) > 0
        assert "is_garbled" in logs[0], "API 响应应包含 is_garbled 字段"
        assert logs[0]["is_garbled"] is False, "正常中文内容的 is_garbled 应为 False"


# ---------------------------------------------------------------------------
# GET /api/v1/logs/query 查询日志
# ---------------------------------------------------------------------------

class TestGetQueryLogsAPI:
    """测试 GET /api/v1/logs/query 接口。"""

    @pytest.mark.asyncio
    async def test_get_query_logs_success(self, client):
        """正常请求应返回 200 和日志列表。"""
        resp = await client.get("/api/v1/logs/query")
        assert resp.status_code == 200
        data = resp.json()
        assert "logs" in data
        assert "count" in data

    @pytest.mark.asyncio
    async def test_get_query_logs_after_query(self, client):
        """执行查询后，查询日志应包含对应记录。"""
        query_text = "查询后日志验证文本"
        await client.get("/api/v1/memories", params={"query": query_text})
        await asyncio.sleep(0.1)

        resp = await client.get("/api/v1/logs/query")
        logs = resp.json()["logs"]
        assert any(l["query"] == query_text for l in logs), "查询日志应包含该查询条件"


# ---------------------------------------------------------------------------
# GET /api/v1/admin/tier-stats 分级统计
# ---------------------------------------------------------------------------

class TestAdminTierStatsAPI:
    """测试 GET /api/v1/admin/tier-stats 接口。"""

    @pytest.mark.asyncio
    async def test_get_tier_stats_success(self, client):
        """正常请求应返回 200 和分级统计数据。"""
        resp = await client.get("/api/v1/admin/tier-stats")
        assert resp.status_code == 200
        data = resp.json()
        assert "hot_count" in data
        assert "cold_count" in data
        assert "hot_memory_mb" in data
        assert "memory_budget_mb" in data

    @pytest.mark.asyncio
    async def test_tier_stats_cold_count_increases_after_save(self, client):
        """存储记忆后 cold_count 应增加。"""
        stats_before = (await client.get("/api/v1/admin/tier-stats")).json()
        await client.post("/api/v1/memories", json={"content": "统计测试记忆"})
        stats_after = (await client.get("/api/v1/admin/tier-stats")).json()
        assert stats_after["cold_count"] > stats_before["cold_count"]


# ---------------------------------------------------------------------------
# GET /api/v1/admin/disk-stats 磁盘统计
# ---------------------------------------------------------------------------

class TestAdminDiskStatsAPI:
    """测试 GET /api/v1/admin/disk-stats 接口。"""

    @pytest.mark.asyncio
    async def test_get_disk_stats_success(self, client):
        """正常请求应返回 200 和磁盘统计数据。"""
        resp = await client.get("/api/v1/admin/disk-stats")
        assert resp.status_code == 200
        data = resp.json()
        assert "disk_used_gb" in data
        assert "disk_budget_gb" in data
        assert "disk_trigger_gb" in data
        assert "disk_safe_gb" in data
