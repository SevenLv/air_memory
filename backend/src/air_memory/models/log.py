"""日志相关 Pydantic 数据模型。"""

from pydantic import BaseModel


class SaveLog(BaseModel):
    """存储操作日志条目。"""

    id: int
    memory_id: str
    content: str
    created_at: str
    memory_deleted: bool


class SaveLogsResponse(BaseModel):
    """存储操作日志响应。"""

    logs: list[SaveLog]
    count: int


class QueryLog(BaseModel):
    """查询操作日志条目。"""

    id: int
    query: str
    results: str
    fast_only: bool
    created_at: str


class QueryLogsResponse(BaseModel):
    """查询操作日志响应。"""

    logs: list[QueryLog]
    count: int
