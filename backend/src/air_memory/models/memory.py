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


class MemoryManageItem(BaseModel):
    """记忆管理列表条目。"""

    id: int
    memory_id: str
    content: str
    created_at: str
    memory_deleted: bool
    is_garbled: bool = False
    value_score: float


class MemoryManageListResponse(BaseModel):
    """记忆管理列表响应（含总条数，用于分页）。"""

    logs: list[MemoryManageItem]
    count: int
    total: int


class MemoryDetailResponse(BaseModel):
    """记忆详情响应。"""

    id: int
    memory_id: str
    content: str
    created_at: str
    memory_deleted: bool
    is_garbled: bool = False
    value_score: float
    tier: str
    feedback_count: int
    value_updated_at: str
    message: str = "ok"


class DeleteMemoryResponse(BaseModel):
    """删除记忆响应。"""

    message: str = "ok"
