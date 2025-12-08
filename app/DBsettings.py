"""
Tortoise ORM 配置模块
"""

TORTOISE_ORM = {
    "connections": {
        "default": "sqlite://Faio.db"  # 如果还要再接别的库，再写一行即可
    },
    "apps": {
        "models": {
            "models": ["models"],          # 你的模型所在包（可 list 多个）,aerich.models 用于迁移
            "default_connection": "default",
        }
    },
    "use_tz": False,        # 是否强制存 UTC；看项目需求
    "timezone": "Asia/Shanghai",  # 本地时区，不配默认系统时区
}