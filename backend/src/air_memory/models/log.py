"""日志相关 Pydantic 数据模型。"""

from pydantic import BaseModel


class SaveLog(BaseModel):
    """存储操作日志条目。"""

    id: int
    memory_id: str
    content: str
    created_at: str
    memory_deleted: bool
    total_association_score: float | None = None  # 替代 value_score
    is_garbled: bool = False


class SaveLogsResponse(BaseModel):
    """存储操作日志响应。"""

    logs: list[SaveLog]
    count: int


class QueryLog(BaseModel):
    """查询操作日志条目。"""

    id: int
    input_id: str | None = None
    query: str
    results: str
    created_at: str


class QueryLogsResponse(BaseModel):
    """查询操作日志响应。"""

    logs: list[QueryLog]
    count: int
