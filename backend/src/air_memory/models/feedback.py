"""反馈相关 Pydantic 数据模型。"""

from pydantic import BaseModel


class FeedbackLog(BaseModel):
    """反馈日志条目。"""

    id: int
    memory_id: str
    valuable: bool
    created_at: str


class FeedbackLogsResponse(BaseModel):
    """反馈日志响应。"""

    logs: list[FeedbackLog]
    count: int
