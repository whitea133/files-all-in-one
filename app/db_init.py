"""
启动时的数据库初始化辅助函数。
"""
from pathlib import Path


async def ensure_system_virtual_folders() -> None:
    """确保系统默认虚拟文件夹存在（首次启动自动创建）。"""
    from models import VirtualFolder  # 延迟导入，避免循环引用

    defaults = [
        {"name": "全部资料", "description": "系统默认文件夹"},
        {"name": "回收站", "description": "系统默认文件夹"},
    ]

    for item in defaults:
        folder, _ = await VirtualFolder.get_or_create(
            name=item["name"],
            defaults={"description": item["description"], "is_system": True},
        )
        if not folder.is_system:
            folder.is_system = True
            await folder.save()


async def ensure_operator_types() -> None:
    """初始化内置的操作类型，便于记录操作日志。"""
    from models import OperatorType  # 延迟导入，避免循环引用

    defaults = [
        {"name": "创建虚拟文件夹", "description": "POST /folders"},
        {"name": "重命名虚拟文件夹", "description": "PATCH /folders/{id}"},
        {"name": "删除虚拟文件夹", "description": "DELETE /folders/{id}"},
        {"name": "创建资料锚点", "description": "POST /anchors"},
        {"name": "移入回收站", "description": "DELETE /anchors/{id}"},
        {"name": "恢复资料锚点", "description": "POST /anchors/{id}/restore"},
        {"name": "绑定锚点文件夹", "description": "POST /anchors/{id}/bindFolders"},
        {"name": "更新锚点信息", "description": "PATCH /anchors/{id}"},
        {"name": "添加锚点标签", "description": "POST /anchors/{id}/tags"},
        {"name": "移除锚点标签", "description": "DELETE /anchors/{id}/tags/{tag_id}"},
        {"name": "删除标签", "description": "DELETE /tags/{id}"},
        {"name": "清空回收站", "description": "DELETE /folders/recycle/empty"},
        {"name": "创建备份", "description": "POST /backups/{anchor_id}"},
        {"name": "恢复备份", "description": "POST /backups/{backup_id}/restore"},
        {"name": "删除备份", "description": "DELETE /backups/{backup_id}"},
    ]

    for item in defaults:
        await OperatorType.get_or_create(
            name=item["name"],
            defaults={"description": item["description"]},
        )


async def check_anchor_paths() -> None:
    """启动时校验资料锚点路径有效性，保持 is_valid 状态同步。"""
    from models import FileAnchor  # 延迟导入，避免循环引用

    anchors = await FileAnchor.all()
    for anchor in anchors:
        exists = Path(anchor.path).expanduser().exists()
        new_valid = bool(exists)
        if anchor.is_valid != new_valid:
            anchor.is_valid = new_valid
            await anchor.save()
