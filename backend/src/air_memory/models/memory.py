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
    total_association_score: float = 0.0  # 所有 input_memory_links 关联分之和
    association_score: float = 0.0        # 本次输入与该记忆的关联分
    source: str = "hot"                   # "associated" / "hot" / "cold"
    tier: str
    created_at: str


class MemoryQueryResponse(BaseModel):
    """查询记忆响应。"""

    input_id: str
    memories: list[Memory]
    count: int


class MemoryFeedbackRequest(BaseModel):
    """提交记忆价值反馈请求。"""

    input_id: str = Field(..., description="触发本次反馈的查询 input_id")
    valuable: bool = Field(..., description="是否有价值")


class MemoryFeedbackResponse(BaseModel):
    """提交记忆价值反馈响应。"""

    memory_id: str
    message: str = "ok"


class DeleteMemoryResponse(BaseModel):
    """删除记忆响应。"""

    message: str = "ok"
