"""测试公共 Fixture：提供临时目录、Mock 模型、数据库初始化等基础设施。"""

import asyncio
import os
import tempfile
import uuid
from typing import AsyncGenerator, Generator
from unittest.mock import MagicMock

import numpy as np
import pytest
import pytest_asyncio
import aiosqlite

from air_memory.config import settings
from air_memory.db import init_db


# ---------------------------------------------------------------------------
# Mock SentenceTransformer
# ---------------------------------------------------------------------------

class MockSentenceTransformer:
    """轻量级 Mock 模型，以随机向量替代真实 Embedding，避免加载大型模型。"""

    def encode(self, text: str, convert_to_numpy: bool = False) -> np.ndarray:
        """返回固定维度 384 的确定性向量（基于文本哈希，相同文本返回相同向量）。

        使用 `abs(hash(text)) % (2**32)` 作为随机种子，原因: numpy 的 `default_rng`
        要求种子值为 0 ≤ seed < 2**32 的无符号 32 位整数，而 Python hash() 可能返回
        负数，因此需要先取绝对值再对 2**32 取模以确保范围合法。
        """
        rng = np.random.default_rng(abs(hash(text)) % (2**32))
        vec = rng.random(384).astype(np.float32)
        # 归一化，避免距离值异常
        vec = vec / (np.linalg.norm(vec) + 1e-8)
        return vec


# ---------------------------------------------------------------------------
# 环境与路径 Fixture
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def tmp_dir() -> Generator[str, None, None]:
    """提供 session 级别的临时目录，测试结束后自动清理。"""
    with tempfile.TemporaryDirectory() as d:
        yield d


@pytest.fixture(autouse=True)
def override_settings(tmp_path) -> Generator[None, None, None]:
    """每个测试用例使用独立的临时数据路径和集合名称，避免测试间数据污染。

    注意：ChromaDB 1.x EphemeralClient 在同一进程内共享内存存储，因此需要
    为每个测试使用唯一的集合名称以避免状态污染。
    """
    db_path = str(tmp_path / "test_logs.db")
    chroma_path = str(tmp_path / "test_chroma_cold")
    os.makedirs(chroma_path, exist_ok=True)

    # 生成唯一的集合名称，避免 EphemeralClient 共享状态
    test_suffix = uuid.uuid4().hex[:8]
    hot_collection = f"hot_test_{test_suffix}"
    cold_collection = f"cold_test_{test_suffix}"

    # 保存原始配置
    original_db = settings.DB_PATH
    original_chroma = settings.CHROMA_COLD_PATH
    original_hot_col = settings.HOT_COLLECTION
    original_cold_col = settings.COLD_COLLECTION

    # 覆盖全局 settings
    settings.DB_PATH = db_path
    settings.CHROMA_COLD_PATH = chroma_path
    settings.HOT_COLLECTION = hot_collection
    settings.COLD_COLLECTION = cold_collection

    yield

    # 恢复原始配置
    settings.DB_PATH = original_db
    settings.CHROMA_COLD_PATH = original_chroma
    settings.HOT_COLLECTION = original_hot_col
    settings.COLD_COLLECTION = original_cold_col


# ---------------------------------------------------------------------------
# 数据库 Fixture
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def db_path(tmp_path) -> str:
    """初始化测试用 SQLite 数据库，返回路径。"""
    path = str(tmp_path / "test_logs.db")
    settings.DB_PATH = path
    await init_db()
    return path


# ---------------------------------------------------------------------------
# 服务 Fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_model() -> MockSentenceTransformer:
    """返回轻量级 Mock Embedding 模型。"""
    return MockSentenceTransformer()


@pytest_asyncio.fixture
async def memory_service(db_path: str, mock_model: MockSentenceTransformer):
    """初始化 MemoryService，使用 Mock 模型和临时 ChromaDB。"""
    from air_memory.memory.service import MemoryService
    svc = MemoryService(mock_model)
    return svc


@pytest_asyncio.fixture
async def log_service(db_path: str):
    """初始化 LogService，使用临时 SQLite。"""
    from air_memory.log.service import LogService
    return LogService()


@pytest_asyncio.fixture
async def feedback_service(memory_service, db_path: str):
    """初始化 FeedbackService，依赖 MemoryService 和临时 SQLite。"""
    from air_memory.feedback.service import FeedbackService
    return FeedbackService(memory_service)


@pytest_asyncio.fixture
async def tier_manager(memory_service, db_path: str):
    """初始化 TierManager，依赖 MemoryService。"""
    from air_memory.memory.tier_manager import TierManager
    return TierManager(memory_service)


@pytest_asyncio.fixture
async def disk_manager(memory_service, db_path: str):
    """初始化 DiskManager，依赖 MemoryService。"""
    from air_memory.disk.manager import DiskManager
    return DiskManager(memory_service)


# ---------------------------------------------------------------------------
# 辅助函数
# ---------------------------------------------------------------------------

async def insert_memory_value(db_path: str, memory_id: str, value_score: float,
                               tier: str = "cold", created_at: str = None,
                               feedback_count: int = 0) -> None:
    """向 memory_values 表插入测试数据。"""
    from datetime import datetime, timezone
    if created_at is None:
        created_at = datetime.now(timezone.utc).isoformat()
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            "INSERT OR REPLACE INTO memory_values"
            " (memory_id, value_score, tier, feedback_count, created_at, updated_at)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (memory_id, value_score, tier, feedback_count, created_at, created_at),
        )
        await db.commit()
