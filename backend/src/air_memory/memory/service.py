"""记忆存储服务模块，维护热层/冷层 ChromaDB 存储与查询。"""

import asyncio
import uuid
from datetime import datetime, timezone

import chromadb
from sentence_transformers import SentenceTransformer

from air_memory.config import settings
from air_memory.models.memory import Memory


def _now_iso() -> str:
    """返回当前 UTC 时间的 ISO 8601 字符串。"""
    return datetime.now(timezone.utc).isoformat()


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
        """存储一条记忆，初始存入冷层，返回 memory_id。"""
        memory_id = str(uuid.uuid4())
        embedding = await asyncio.to_thread(self._encode, content)
        created_at = _now_iso()
        await asyncio.to_thread(
            self._cold_col.add,
            ids=[memory_id],
            documents=[content],
            embeddings=[embedding],
            metadatas=[{"created_at": created_at, "value_score": settings.INITIAL_VALUE_SCORE}],
        )
        return memory_id

    async def query(
        self, query: str, top_k: int, fast_only: bool
    ) -> list[Memory]:
        """查询记忆。fast_only=True 仅查热层；False 同时查热层和冷层并合并去重。"""
        embedding = await asyncio.to_thread(self._encode, query)

        if fast_only:
            results = await asyncio.to_thread(self._query_col, self._hot_col, embedding, top_k)
            return results

        # 并发查询热层和冷层
        hot_task = asyncio.to_thread(self._query_col, self._hot_col, embedding, top_k)
        cold_task = asyncio.to_thread(self._query_col, self._cold_col, embedding, top_k)
        hot_results, cold_results = await asyncio.gather(hot_task, cold_task)

        # 合并去重：以 id 为键，优先保留热层结果（热层相似度更可靠）
        merged: dict[str, Memory] = {}
        for mem in hot_results:
            merged[mem.id] = mem
        for mem in cold_results:
            if mem.id not in merged:
                merged[mem.id] = mem

        # 按相似度降序排列，取 top_k
        sorted_results = sorted(merged.values(), key=lambda m: m.similarity, reverse=True)
        return sorted_results[:top_k]

    async def delete(self, memory_id: str) -> None:
        """从热层和冷层同时删除指定记忆。"""
        await asyncio.to_thread(self._safe_delete, self._hot_col, memory_id)
        await asyncio.to_thread(self._safe_delete, self._cold_col, memory_id)

    async def promote(self, memory_id: str, value_score: float) -> None:
        """将记忆从冷层迁移到热层。"""
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
        metadata["value_score"] = value_score

        await asyncio.to_thread(
            self._hot_col.upsert,
            ids=[memory_id],
            documents=result["documents"],
            embeddings=result["embeddings"],
            metadatas=[metadata],
        )

    async def demote(self, memory_id: str, value_score: float) -> None:
        """将记忆从热层移除（降级至冷层；冷层始终存有完整数据）。"""
        try:
            result = await asyncio.to_thread(
                self._cold_col.get,
                ids=[memory_id],
                include=["metadatas"],
            )
        except Exception:
            pass
        else:
            if result["ids"]:
                metadata = dict(result["metadatas"][0])
                metadata["value_score"] = value_score
                await asyncio.to_thread(
                    self._cold_col.upsert,
                    ids=[memory_id],
                    metadatas=[metadata],
                )
        await asyncio.to_thread(self._safe_delete, self._hot_col, memory_id)

    async def load_hot_from_cold(self, memory_id: str, value_score: float) -> None:
        """从冷层加载指定记忆到热层（TierManager 启动时调用）。"""
        await self.promote(memory_id, value_score)

    def get_hot_count(self) -> int:
        """返回热层当前记忆数量。"""
        return self._hot_col.count()

    def get_cold_count(self) -> int:
        """返回冷层当前记忆数量。"""
        return self._cold_col.count()

    def get_hot_memory_mb(self) -> float:
        """估算热层内存占用（MB），每条记忆约 2KB。"""
        return self.get_hot_count() * 2 / 1024

    # ------------------------------------------------------------------
    # 私有辅助方法
    # ------------------------------------------------------------------

    def _encode(self, text: str) -> list[float]:
        """将文本编码为向量（阻塞操作，应在线程中调用）。"""
        return self._model.encode(text, convert_to_numpy=True).tolist()

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
        memories = []
        for i, mem_id in enumerate(result["ids"][0]):
            distance = result["distances"][0][i]
            # ChromaDB 默认使用 squared L2 距离；使用 1/(1+d) 将距离映射为 [0,1] 相似度分数
            similarity = round(1.0 / (1.0 + distance), 4)
            meta = result["metadatas"][0][i]
            memories.append(
                Memory(
                    id=mem_id,
                    content=result["documents"][0][i],
                    similarity=similarity,
                    value_score=float(meta.get("value_score", 0.5)),
                    tier="hot" if col.name == settings.HOT_COLLECTION else "cold",
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
