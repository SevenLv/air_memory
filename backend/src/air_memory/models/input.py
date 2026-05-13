"""输入信息相关 Pydantic 数据模型。"""

from pydantic import BaseModel


class InputInfo(BaseModel):
    """输入信息条目。"""

    input_id: str
    query: str
    created_at: str


class InputMemoryLink(BaseModel):
    """输入信息与记忆的关联条目。"""

    memory_id: str
    association_score: float
    total_association_score: float


class InputDetail(BaseModel):
    """输入信息详情（含关联记忆及评分）。"""

    input_id: str
    query: str
    created_at: str
    memories: list[InputMemoryLink]


class InputsListResponse(BaseModel):
    """输入信息列表响应（含总条数，用于分页）。"""

    inputs: list[InputInfo]
    count: int   # 当前页条数
    total: int   # 符合条件的总条数
