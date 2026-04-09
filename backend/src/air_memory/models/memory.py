"""记忆相关 Pydantic 数据模型。"""

from pydantic import BaseModel, Field


class MemorySaveRequest(BaseModel):
    """存储记忆请求。"""

    content: str = Field(..., min_length=1, description="记忆内容")


class MemorySaveResponse(BaseModel):
    """存储记忆响应。"""

    memory_id: str
    tier: str
    message: str = "ok"


class Memory(BaseModel):
    """记忆条目。"""

    id: str
    content: str
    similarity: float
    value_score: float
    tier: str
    created_at: str


class MemoryQueryResponse(BaseModel):
    """查询记忆响应。"""

    memories: list[Memory]
    count: int
    query_mode: str


class MemoryFeedbackRequest(BaseModel):
    """提交记忆价值反馈请求。"""

    valuable: bool = Field(..., description="是否有价值")


class MemoryFeedbackResponse(BaseModel):
    """提交记忆价值反馈响应。"""

    memory_id: str
    value_score: float
    tier: str
    message: str = "ok"


class MemoryValueScore(BaseModel):
    """记忆价值评分。"""

    memory_id: str
    value_score: float
    tier: str
    feedback_count: int


class DeleteMemoryResponse(BaseModel):
    """删除记忆响应。"""

    message: str = "ok"
