"""
fastAPI 应用主模块
"""

# 导入必要的模块
from contextlib import asynccontextmanager
from importlib import import_module  # 动态导入模块
from pathlib import Path  # 操作文件路径
from pkgutil import iter_modules  # 遍历包中的模块

from fastapi import FastAPI, APIRouter  # 创建FastAPI应用和API路由
from fastapi.middleware.cors import CORSMiddleware  # 跨域支持
from fastapi.staticfiles import StaticFiles  # 提供静态文件服务
from fastapi.responses import FileResponse
from tortoise.contrib.fastapi import register_tortoise  # 集成Tortoise ORM
from DBsettings import TORTOISE_ORM  # 数据库配置
from loguru import logger  # 记录日志
import os

from db_init import ensure_system_virtual_folders, check_anchor_paths


@asynccontextmanager
async def lifespan(app: FastAPI):
    """使用 lifespan 取代已弃用的 startup 事件。"""
    await ensure_system_virtual_folders()
    await check_anchor_paths()
    yield


# 创建FastAPI应用实例（使用 lifespan）
app = FastAPI(lifespan=lifespan)

# 跨域配置（前端 dev 服务）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 配置Tortoise ORM，使用Sqlite数据库
register_tortoise(
    app,
    config=TORTOISE_ORM,
    generate_schemas=True,  # 启动时自动生成数据库表结构。只在开发环境使用，生产环境请使用迁移工具
    add_exception_handlers=True,  # 添加异常处理器。只在开发环境使用。
)

# 挂载静态文件目录，使得可以通过/static/访问静态资源
static_file_abspath = os.path.join(os.path.dirname(__file__), "static")
print(static_file_abspath)
app.mount("/static", StaticFiles(directory=static_file_abspath), name="static")

@app.get("/")
def index():
    return FileResponse(f"{static_file_abspath}/index.html")

# 前端 SPA 路由回退（history 模式下，直接访问前端路由时返回 index.html）
@app.get("/setting")
@app.get("/about")
def spa_entry():
    return FileResponse(f"{static_file_abspath}/index.html")

# 定义一个字典用于缓存已导入的模块，避免重复导入
_imported_modules = {}

def register_routers(package_name='routers'):
    """
    自动注册指定包下的所有API路由。

    参数:
        package_name (str): 包含API路由的包名，默认为'routers'
    """
    # 获取当前文件所在目录，并拼接上包名得到包的实际路径
    package_dir = Path(__file__).resolve().parent / package_name

    # 记录正在注册路由的日志信息
    logger.info(f"正在注册路由，包目录: {package_dir}")

    try:
        # 遍历包中的所有模块
        for (_, module_name, _) in iter_modules([str(package_dir)]):
            # 如果模块已经导入过，则直接使用缓存中的模块
            if module_name in _imported_modules:
                module = _imported_modules[module_name]
            else:
                # 否则动态导入模块并缓存
                module = import_module(f"{package_name}.{module_name}")
                _imported_modules[module_name] = module

            # 记录成功导入模块的日志信息
            logger.debug(f"导入模块: {module_name}")

            # 尝试从模块中获取名为'router'的对象
            router = getattr(module, 'router', None)

            # 如果获取到的对象是APIRouter实例，则将其注册到FastAPI应用中
            if isinstance(router, APIRouter):
                app.include_router(router)
                logger.debug(f"已注册路由: {module_name}")
            else:
                # 如果未找到有效的APIRouter实例，记录警告日志
                logger.warning(f"模块 {module_name} 没有找到有效的 APIRouter 实例")
    except Exception as e:
        # 如果发生任何异常，记录错误日志
        logger.error(f"注册路由时发生错误: {e}")

# 调用函数注册所有路由
register_routers()

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app)
