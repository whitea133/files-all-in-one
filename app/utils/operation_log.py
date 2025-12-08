"""
操作日志写入工具，避免在各路由重复创建 OperatorLog。
"""
from loguru import logger


async def log_operation(type_name: str, result: str) -> None:
    """记录一次操作日志，不影响主流程。

    :param type_name: OperatorType.name，用于定位操作类型
    :param result: 本次操作的结果描述（可简要包含 ID/路径等信息）
    """
    # 延迟导入以避免循环依赖
    from models import OperatorLog, OperatorType

    try:
        opt_type = await OperatorType.get_or_none(name=type_name)
        if not opt_type:
            return
        await OperatorLog.create(operator_type=opt_type, result=result)
    except Exception as exc:  # noqa: BLE001 - 日志失败不阻断主流程
        logger.warning("记录操作日志失败: {} => {}", type_name, exc)
