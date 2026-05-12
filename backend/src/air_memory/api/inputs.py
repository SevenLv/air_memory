"""输入信息相关 REST API 路由。"""

from fastapi import APIRouter, HTTPException, Query, Request

from air_memory.models.input import InputDetail, InputsListResponse

router = APIRouter(prefix="/inputs", tags=["inputs"])


@router.get("", response_model=InputsListResponse)
async def list_inputs(
    request: Request,
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页条数"),
    start_time: str | None = Query(default=None, description="开始时间（ISO 8601）"),
    end_time: str | None = Query(default=None, description="结束时间（ISO 8601）"),
):
    """分页查询输入信息列表。"""
    feedback_svc = request.app.state.feedback_service
    inputs, total = await feedback_svc.list_inputs(
        page=page,
        page_size=page_size,
        start_time=start_time,
        end_time=end_time,
    )
    return InputsListResponse(inputs=inputs, count=len(inputs), total=total)


@router.get("/{input_id}", response_model=InputDetail)
async def get_input_detail(
    input_id: str,
    request: Request,
):
    """查询输入信息详情（含关联记忆及评分）。"""
    feedback_svc = request.app.state.feedback_service
    detail = await feedback_svc.get_input_detail(input_id)
    if detail is None:
        raise HTTPException(status_code=404, detail=f"输入信息不存在：{input_id}")
    return detail
