"""公共测试基建：路径注入、内存数据库、异步客户端。"""

import pathlib
import sys

import httpx
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport
from tortoise import Tortoise

ROOT = pathlib.Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "app"

# 兼容业务代码中的顶层导入（models、routers.* 等）
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import models  # noqa: E402
from routers import folder as folder_router  # noqa: E402


SYSTEM_FOLDERS = [
    {"name": "全部资料", "description": "系统默认", "is_system": True},
    {"name": "回收站", "description": "系统默认", "is_system": True},
]


async def _prepare_db() -> None:
    await Tortoise.init(db_url="sqlite://:memory:", modules={"models": ["models"]})
    await Tortoise.generate_schemas()
    await models.VirtualFolder.bulk_create([models.VirtualFolder(**row) for row in SYSTEM_FOLDERS])


@pytest_asyncio.fixture
async def client():
    await _prepare_db()

    app = FastAPI()
    app.include_router(folder_router.router)

    async with httpx.AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        follow_redirects=True,
    ) as async_client:
        yield async_client

    await Tortoise.close_connections()
