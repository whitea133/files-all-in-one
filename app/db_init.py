"""
启动时的数据库初始化辅助函数。
"""

async def ensure_system_virtual_folders() -> None:
    """
    确保系统默认虚拟文件夹存在（首次启动自动创建）。
    """
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
