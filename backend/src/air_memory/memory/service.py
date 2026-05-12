"""记忆存储服务模块，维护热层/冷层 ChromaDB 存储与查询。"""

import asyncio
import uuid
from datetime import datetime, timezone

import aiosqlite
import chromadb
import numpy as np
from sentence_transformers import SentenceTransformer

from air_memory.config import settings
from air_memory.models.memory import Memory


def _now_iso() -> str:
    """返回当前 UTC 时间的 ISO 8601 字符串。"""
    return datetime.now(timezone.utc).isoformat()


def _in_placeholders(ids: list[str]) -> str:
    """生成 SQL IN 子句所需的参数占位符字符串（如 '?,?,?'）。

    占位符只包含 '?' 字符，不含任何用户数据，配合参数化查询使用，安全无注入风险。
    """
    return ",".join("?" * len(ids))


class MemoryService:
    """记忆存储和查询的核心业务逻辑服务。"""

    def __init__(self, model: SentenceTransformer) -> None:
        self._model = model
        # 热层：EphemeralClient（纯内存）
        self._hot_client = chromadb.EphemeralClient()
        self._hot_col = self._hot_client.get_or_create_collection(
            settings.HOT_COLLECTION
        )
        # 冷层：PersistentClient（磁盘持久化）
        self._cold_client = chromadb.PersistentClient(path=settings.CHROMA_COLD_PATH)
        self._cold_col = self._cold_client.get_or_create_collection(
            settings.COLD_COLLECTION
        )

    # ------------------------------------------------------------------
    # 公共接口
    # ------------------------------------------------------------------

    async def save(self, content: str) -> str:
        """存储一条记忆，初始同时存入热层和冷层，返回 memory_id。"""
        memory_id = str(uuid.uuid4())
        embedding = await asyncio.to_thread(self._encode, content)
        created_at = _now_iso()
        metadata = {"created_at": created_at, "tier": "hot"}
        # 冷层（持久化存储，始终保有完整数据）
        await asyncio.to_thread(
            self._cold_col.add,
            ids=[memory_id],
            documents=[content],
            embeddings=[embedding],
            metadatas=[metadata],
        )
        # 热层（内存快速访问，新记忆默认可被快速查询）
        await asyncio.to_thread(
            self._hot_col.add,
            ids=[memory_id],
            documents=[content],
            embeddings=[embedding],
            metadatas=[metadata],
        )
        return memory_id

    async def query(
        self, query: str, top_k: int
    ) -> tuple[str, list[Memory]]:
        """统一溢出填充配额检索，返回 (input_id, memories)。

        配额策略：
        1. 生成 input_id，存入 input_infos
        2. 查询 input_memory_links 找到关联记忆（最多5条，按 total_association_score DESC）
        3. 热层 HNSW 搜索：quota = max(3, 8 - 关联实际数)
        4. 冷层 HNSW 搜索：quota = max(2, 10 - 关联数 - 热层实际数)
        5. 合并去重后总数 ≤ top_k (最大10)
        """
        input_id = str(uuid.uuid4())
        now = _now_iso()

        # 1. 存入 input_infos
        async with aiosqlite.connect(settings.DB_PATH) as db:
            await db.execute(
                "INSERT INTO input_infos (input_id, query, created_at) VALUES (?, ?, ?)",
                (input_id, query, now),
            )
            await db.commit()

        # 获取查询向量
        embedding = await asyncio.to_thread(self._encode, query)

        # 2. 查询关联记忆（有历史关联评分的记忆，最多5条）
        associated_memories = await self._get_associated_memories(embedding)

        # 3. 热层搜索
        hot_quota = max(3, 8 - len(associated_memories))
        exclude_ids = {m.id for m in associated_memories}
        hot_memories = await asyncio.to_thread(
            self._query_col_excluding,
            self._hot_col,
            embedding,
            hot_quota,
            exclude_ids,
        )

        # 4. 冷层搜索
        cold_quota = max(2, 10 - len(associated_memories) - len(hot_memories))
        exclude_ids = {m.id for m in associated_memories} | {m.id for m in hot_memories}
        cold_memories = await asyncio.to_thread(
            self._query_col_excluding,
            self._cold_col,
            embedding,
            cold_quota,
            exclude_ids,
        )

        # 5. 合并，限制 top_k（最大10）
        effective_top_k = min(top_k, 10)
        all_memories = (associated_memories + hot_memories + cold_memories)[:effective_top_k]

        # 批量填充 total_association_score（非 associated 来源的记忆）
        if all_memories:
            non_assoc_ids = [m.id for m in all_memories if m.source != "associated"]
            if non_assoc_ids:
                scores = await self._get_total_association_scores(non_assoc_ids)
                for m in all_memories:
                    if m.source != "associated" and m.id in scores:
                        m.total_association_score = scores[m.id]

        return input_id, all_memories

    async def delete(self, memory_id: str) -> None:
        """从热层和冷层同时删除指定记忆。"""
        await asyncio.to_thread(self._safe_delete, self._hot_col, memory_id)
        await asyncio.to_thread(self._safe_delete, self._cold_col, memory_id)

    async def promote(self, memory_id: str, value_score: float | None = None) -> None:
        """将记忆从冷层迁移到热层。value_score 参数保留用于向后兼容（不再使用）。"""
        try:
            result = await asyncio.to_thread(
                self._cold_col.get,
                ids=[memory_id],
                include=["documents", "embeddings", "metadatas"],
            )
        except Exception:
            return
        if not result["ids"]:
            return

        metadata = dict(result["metadatas"][0])
        metadata["tier"] = "hot"

        await asyncio.to_thread(
            self._hot_col.upsert,
            ids=[memory_id],
            documents=result["documents"],
            embeddings=result["embeddings"],
            metadatas=[metadata],
        )

    async def demote(self, memory_id: str, value_score: float | None = None) -> None:
        """将记忆从热层移除（降级至冷层）。value_score 参数保留用于向后兼容（不再使用）。"""
        try:
            result = await asyncio.to_thread(
                self._cold_col.get,
                ids=[memory_id],
                include=["documents", "embeddings", "metadatas"],
            )
        except Exception:
            pass
        else:
            if result["ids"]:
                metadata = dict(result["metadatas"][0])
                metadata["tier"] = "cold"
                await asyncio.to_thread(
                    self._cold_col.upsert,
                    ids=[memory_id],
                    documents=result["documents"],
                    embeddings=result["embeddings"],
                    metadatas=[metadata],
                )
        await asyncio.to_thread(self._safe_delete, self._hot_col, memory_id)

    async def load_hot_from_cold(
        self, memory_id: str, value_score: float | None = None
    ) -> None:
        """从冷层加载指定记忆到热层（TierManager 启动时调用）。"""
        await self.promote(memory_id)

    async def is_hot(self, memory_id: str) -> bool:
        """检查指定记忆是否在热层。"""
        result = await asyncio.to_thread(self._hot_col.get, ids=[memory_id])
        return bool(result["ids"])

    def get_hot_count(self) -> int:
        """返回热层当前记忆数量。"""
        return self._hot_col.count()

    def get_cold_count(self) -> int:
        """返回冷层当前记忆数量。"""
        return self._cold_col.count()

    def get_hot_memory_mb(self) -> float:
        """估算热层内存占用（MB），每条记忆约 2KB。"""
        return self.get_hot_count() * 2 / 1024

    def get_all_cold_ids(self) -> list[str]:
        """返回冷层所有记忆 ID。"""
        result = self._cold_col.get()
        return result["ids"]

    def get_all_hot_ids(self) -> list[str]:
        """返回热层所有记忆 ID。"""
        result = self._hot_col.get()
        return result["ids"]

    def get_cold_metadata(self, memory_ids: list[str]) -> list[dict]:
        """批量获取冷层记忆的元数据。"""
        if not memory_ids:
            return []
        result = self._cold_col.get(
            ids=memory_ids,
            include=["metadatas"],
        )
        return result["metadatas"]

    # ------------------------------------------------------------------
    # 私有辅助方法
    # ------------------------------------------------------------------

    def _encode(self, text: str) -> list[float]:
        """将文本编码为向量（阻塞操作，应在线程中调用）。"""
        return self._model.encode(text, convert_to_numpy=True).tolist()

    async def _get_associated_memories(
        self, query_embedding: list[float]
    ) -> list[Memory]:
        """从 SQLite 获取关联评分最高的记忆，并从 ChromaDB 获取内容。"""
        async with aiosqlite.connect(settings.DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT memory_id, COALESCE(SUM(association_score), 0) AS total_score"
                " FROM input_memory_links GROUP BY memory_id"
                " ORDER BY total_score DESC LIMIT 5"
            ) as cursor:
                rows = await cursor.fetchall()

        if not rows:
            return []

        associated_ids = [row["memory_id"] for row in rows]
        scores = {row["memory_id"]: float(row["total_score"]) for row in rows}

        memories = await asyncio.to_thread(
            self._fetch_by_ids_with_similarity,
            associated_ids,
            query_embedding,
            scores,
        )
        return memories

    def _fetch_by_ids_with_similarity(
        self,
        memory_ids: list[str],
        query_embedding: list[float],
        associated_scores: dict[str, float],
    ) -> list[Memory]:
        """从热层/冷层按 ID 获取记忆，计算与查询向量的相似度。"""
        memories = []
        q_emb = np.array(query_embedding, dtype=np.float32)
        remaining = list(memory_ids)

        for col, tier_name in [(self._hot_col, "hot"), (self._cold_col, "cold")]:
            if not remaining:
                break
            try:
                result = col.get(
                    ids=remaining,
                    include=["documents", "embeddings", "metadatas"],
                )
            except Exception:
                continue

            found_ids = set(result["ids"])
            for i, mid in enumerate(result["ids"]):
                emb = result["embeddings"][i]
                m_emb = np.array(emb, dtype=np.float32)
                norm = np.linalg.norm(q_emb) * np.linalg.norm(m_emb)
                if norm > 1e-8:
                    similarity = float(np.dot(q_emb, m_emb) / norm)
                    similarity = round(max(0.0, min(1.0, similarity)), 4)
                else:
                    similarity = 0.0
                meta = result["metadatas"][i]
                total_score = associated_scores.get(mid, 0.0)
                memories.append(
                    Memory(
                        id=mid,
                        content=result["documents"][i],
                        similarity=similarity,
                        total_association_score=total_score,
                        association_score=total_score,
                        source="associated",
                        tier=tier_name,
                        created_at=str(meta.get("created_at", "")),
                    )
                )
            remaining = [mid for mid in remaining if mid not in found_ids]

        return memories

    async def _get_total_association_scores(
        self, memory_ids: list[str]
    ) -> dict[str, float]:
        """批量查询记忆的 total_association_score。"""
        if not memory_ids:
            return {}
        ph = _in_placeholders(memory_ids)
        async with aiosqlite.connect(settings.DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                f"SELECT memory_id, COALESCE(SUM(association_score), 0) AS total_score"
                f" FROM input_memory_links WHERE memory_id IN ({ph})"
                f" GROUP BY memory_id",
                memory_ids,
            ) as cursor:
                rows = await cursor.fetchall()
        return {row["memory_id"]: float(row["total_score"]) for row in rows}

    @staticmethod
    def _query_col(
        col: chromadb.Collection, embedding: list[float], top_k: int
    ) -> list[Memory]:
        """在指定 ChromaDB 集合中执行 ANN 向量搜索。"""
        count = col.count()
        if count == 0:
            return []
        n = min(top_k, count)
        result = col.query(
            query_embeddings=[embedding],
            n_results=n,
            include=["documents", "distances", "metadatas"],
        )
        source = "hot" if col.name.startswith("hot") else "cold"
        memories = []
        for i, mem_id in enumerate(result["ids"][0]):
            distance = result["distances"][0][i]
            similarity = round(1.0 / (1.0 + distance), 4)
            meta = result["metadatas"][0][i]
            memories.append(
                Memory(
                    id=mem_id,
                    content=result["documents"][0][i],
                    similarity=similarity,
                    total_association_score=0.0,
                    association_score=0.0,
                    source=source,
                    tier="hot" if source == "hot" else "cold",
                    created_at=str(meta.get("created_at", "")),
                )
            )
        return memories

    @staticmethod
    def _query_col_excluding(
        col: chromadb.Collection,
        embedding: list[float],
        top_k: int,
        exclude_ids: set[str],
    ) -> list[Memory]:
        """在集合中搜索，排除指定 ID 后返回 top_k 条结果。"""
        count = col.count()
        if count == 0:
            return []
        # 多查一些以便排除后仍有足够结果
        fetch_n = min(top_k + len(exclude_ids), count)
        result = col.query(
            query_embeddings=[embedding],
            n_results=fetch_n,
            include=["documents", "distances", "metadatas"],
        )
        source = "hot" if col.name.startswith("hot") else "cold"
        memories = []
        for i, mem_id in enumerate(result["ids"][0]):
            if mem_id in exclude_ids:
                continue
            if len(memories) >= top_k:
                break
            distance = result["distances"][0][i]
            similarity = round(1.0 / (1.0 + distance), 4)
            meta = result["metadatas"][0][i]
            memories.append(
                Memory(
                    id=mem_id,
                    content=result["documents"][0][i],
                    similarity=similarity,
                    total_association_score=0.0,
                    association_score=0.0,
                    source=source,
                    tier="hot" if source == "hot" else "cold",
                    created_at=str(meta.get("created_at", "")),
                )
            )
        return memories

    @staticmethod
    def _safe_delete(col: chromadb.Collection, memory_id: str) -> None:
        """尝试从集合中删除记忆，若不存在则忽略。"""
        try:
            col.delete(ids=[memory_id])
        except Exception:
            pass
