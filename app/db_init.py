"""
启动时的数据库初始化辅助函数。
"""
from pathlib import Path


async def ensure_system_virtual_folders() -> None:
    """确保系统默认虚拟文件夹存在（首次启动自动创建）。"""
    from models import VirtualFolder  # 延迟导入，避免循环

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


async def check_anchor_paths() -> None:
    """启动时校验资料锚点路径有效性，保持 is_valid 状态同步。"""
    from models import FileAnchor  # 延迟导入，避免循环

    anchors = await FileAnchor.all()
    for anchor in anchors:
        exists = Path(anchor.path).expanduser().exists()
        new_valid = bool(exists)
        if anchor.is_valid != new_valid:
            anchor.is_valid = new_valid
            await anchor.save()
