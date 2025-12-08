from datetime import datetime

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict

from models import OperatorLog


router = APIRouter(prefix="/logs", tags=["operator-logs"])


class OperatorLogResponse(BaseModel):
    id: int
    operator_type_id: int
    operator_type_name: str
    operator_type_description: str | None = None
    result: str
    time: datetime

    model_config = ConfigDict(from_attributes=True)


@router.get("/", response_model=list[OperatorLogResponse])
async def list_operator_logs() -> list[OperatorLogResponse]:
    """列出全部操作日志，按时间倒序。"""
    logs = await OperatorLog.all().prefetch_related("operator_type").order_by("-time")

    results: list[OperatorLogResponse] = []
    for log in logs:
        op_type = log.operator_type
        results.append(
            OperatorLogResponse(
                id=log.id,
                operator_type_id=op_type.id if op_type else 0,
                operator_type_name=op_type.name if op_type else "",
                operator_type_description=op_type.description if op_type else None,
                result=log.result,
                time=log.time,
            )
        )
    return results
