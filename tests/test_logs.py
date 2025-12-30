"""操作日志模块 LOG-001 ~ LOG-003 用例。"""

import asyncio
from datetime import datetime, timedelta

import httpx
import pytest
from fastapi import status

from models import OperatorLog, OperatorType  # noqa: E402


async def _seed_operator_types():
    """确保存在至少一个操作类型。"""
    op_type = await OperatorType.get_or_none(name="测试操作")
    if not op_type:
        op_type = await OperatorType.create(name="测试操作", description="用于日志测试")
    return op_type


async def _create_log(op_type: OperatorType, result: str, offset_sec: int = 0):
    log = await OperatorLog.create(operator_type=op_type, result=result, time=datetime.now() + timedelta(seconds=offset_sec))
    return log


@pytest.mark.asyncio
async def test_log001_list_logs_order(client: httpx.AsyncClient):
    # LOG-001：打开设置查看日志记录，按时间倒序显示
    op_type = await _seed_operator_types()
    await _create_log(op_type, "旧日志", offset_sec=-10)
    await _create_log(op_type, "新日志", offset_sec=10)

    resp = await client.get("/logs/")
    assert resp.status_code == status.HTTP_200_OK
    logs = resp.json()
    assert len(logs) >= 2
    # 第一条应为时间较新的记录
    assert logs[0]["result"] == "新日志"
    assert logs[1]["result"] == "旧日志"


@pytest.mark.asyncio
async def test_log002_list_logs_no_pagination_error(client: httpx.AsyncClient):
    # LOG-002：在日志列表点击“下一页”（接口无分页，期望正常返回全量列表，无报错）
    resp = await client.get("/logs/")
    assert resp.status_code == status.HTTP_200_OK
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_log003_refresh_logs(client: httpx.AsyncClient):
    # LOG-003：刷新日志列表，新增日志应出现在前端列表且字段正确
    op_type = await _seed_operator_types()
    await _create_log(op_type, "刷新前日志", offset_sec=-5)
    await _create_log(op_type, "刷新后新增", offset_sec=5)

    resp = await client.get("/logs/")
    assert resp.status_code == status.HTTP_200_OK
    logs = resp.json()
    # 新增的日志存在且包含类型/描述/时间
    assert any(log["result"] == "刷新后新增" for log in logs)
    target = next(log for log in logs if log["result"] == "刷新后新增")
    assert target["operator_type_id"] == op_type.id
    assert target["operator_type_name"] == op_type.name
    assert "time" in target and target["time"]
