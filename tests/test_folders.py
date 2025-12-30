"""虚拟文件夹模块 VF-001 ~ VF-011 用例，按测试用例表编写。"""

import httpx
import pytest
from fastapi import status

from models import FileAnchor, VirtualFolder  # noqa: E402
from routers.folder import RECYCLE_FOLDER_NAME  # noqa: E402


async def _create_folder(client: httpx.AsyncClient, name: str, description: str | None = None):
    return await client.post("/folders/", json={"name": name, "description": description})


@pytest.mark.asyncio
async def test_vf001_create_default_named_folder(client: httpx.AsyncClient):
    # VF-001：点击“创建文件夹”自动生成默认名称
    resp = await _create_folder(client, "新建文件夹1")
    assert resp.status_code == status.HTTP_201_CREATED
    assert resp.json()["name"] == "新建文件夹1"


@pytest.mark.asyncio
async def test_vf002_rename_new_folder(client: httpx.AsyncClient):
    # VF-002：重命名新建文件夹 -> 工作资料
    created = await _create_folder(client, "新建文件夹1")
    folder_id = created.json()["id"]

    resp = await client.patch(f"/folders/{folder_id}", json={"name": "工作资料", "description": None})
    assert resp.status_code == status.HTTP_200_OK
    assert resp.json()["name"] == "工作资料"


@pytest.mark.asyncio
async def test_vf003_rename_empty_name(client: httpx.AsyncClient):
    # VF-003：重命名为空
    created = await _create_folder(client, "空名测试")
    folder_id = created.json()["id"]

    resp = await client.patch(f"/folders/{folder_id}", json={"name": "", "description": None})
    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    # 名称保持不变
    current = await client.get("/folders/")
    names = {item["id"]: item["name"] for item in current.json()}
    assert names[folder_id] == "空名测试"


@pytest.mark.asyncio
async def test_vf004_rename_to_existing_name_conflict(client: httpx.AsyncClient):
    # VF-004：重命名为已存在名称
    await _create_folder(client, "已有文件夹A")
    created_b = await _create_folder(client, "已有文件夹B")
    folder_b = created_b.json()["id"]

    resp = await client.patch(f"/folders/{folder_b}", json={"name": "已有文件夹A", "description": None})
    assert resp.status_code == status.HTTP_409_CONFLICT
    # 名称保持不变
    current = await client.get("/folders/")
    names = {item["id"]: item["name"] for item in current.json()}
    assert names[folder_b] == "已有文件夹B"


@pytest.mark.asyncio
async def test_vf005_rename_system_folder_forbidden(client: httpx.AsyncClient):
    # VF-005：尝试修改系统文件夹名称（全部资料/回收站）
    lst = await client.get("/folders/")
    system_id = next(item["id"] for item in lst.json() if item["is_system"])

    resp = await client.patch(f"/folders/{system_id}", json={"name": "重命名系统", "description": None})
    assert resp.status_code == status.HTTP_403_FORBIDDEN
    # 系统文件夹仍存在且为系统标记
    current = await client.get("/folders/")
    assert any(item["id"] == system_id and item["is_system"] for item in current.json())


@pytest.mark.asyncio
async def test_vf006_delete_non_system_folder(client: httpx.AsyncClient):
    # VF-006：删除非系统文件夹（学习资料）
    created = await _create_folder(client, "学习资料")
    folder_id = created.json()["id"]

    resp = await client.delete(f"/folders/{folder_id}")
    assert resp.status_code == status.HTTP_204_NO_CONTENT

    names = [item["name"] for item in (await client.get("/folders/")).json()]
    assert "学习资料" not in names


@pytest.mark.asyncio
async def test_vf007_delete_system_folder_forbidden(client: httpx.AsyncClient):
    # VF-007：尝试删除系统文件夹（全部资料/回收站）
    lst = await client.get("/folders/")
    system_id = next(item["id"] for item in lst.json() if item["is_system"])

    resp = await client.delete(f"/folders/{system_id}")
    assert resp.status_code == status.HTTP_403_FORBIDDEN
    current = await client.get("/folders/")
    assert any(item["id"] == system_id and item["is_system"] for item in current.json())


@pytest.mark.asyncio
async def test_vf008_search_hit(client: httpx.AsyncClient):
    # VF-008：搜索文件夹（关键词：工作）
    await _create_folder(client, "工作分类A")

    resp = await client.get("/folders/", params={"keyword": "工作"})
    assert resp.status_code == status.HTTP_200_OK
    assert any("工作" in item["name"] for item in resp.json())


@pytest.mark.asyncio
async def test_vf009_search_miss(client: httpx.AsyncClient):
    # VF-009：搜索不存在的文件夹（关键词：不存在）
    resp = await client.get("/folders/", params={"keyword": "不存在的关键字"})
    assert resp.status_code == status.HTTP_200_OK
    assert resp.json() == []


@pytest.mark.asyncio
async def test_vf010_empty_recycle_bin(client: httpx.AsyncClient):
    # VF-010：清空回收站
    recycle_folder = await VirtualFolder.filter(name=RECYCLE_FOLDER_NAME).first()
    if not recycle_folder:
        recycle_folder = await VirtualFolder.create(name=RECYCLE_FOLDER_NAME, is_system=True, description="系统默认")

    # 创建一个锚点放入回收站
    anchor = await FileAnchor.create(name="回收站锚点", path="/tmp/a.txt", description=None)
    await anchor.virtual_folders.add(recycle_folder)

    # 清空回收站
    resp = await client.delete("/folders/recycle/empty")
    assert resp.status_code == status.HTTP_204_NO_CONTENT

    # 回收站中不应再有锚点
    anchors_left = await FileAnchor.filter(virtual_folders__id=recycle_folder.id).count()
    assert anchors_left == 0


@pytest.mark.asyncio
async def test_vf011_list_folder_anchors(client: httpx.AsyncClient):
    # VF-011：点击指定虚拟文件夹，列出该文件夹下所有的资料锚点
    folder = await VirtualFolder.create(name="锚点文件夹", is_system=False)
    anchor = await FileAnchor.create(name="锚点A", path="/tmp/a.txt", description=None)
    await anchor.virtual_folders.add(folder)

    resp = await client.get(f"/folders/{folder.id}/anchors")
    assert resp.status_code == status.HTTP_200_OK
    body = resp.json()
    assert len(body) == 1
    assert body[0]["name"] == "锚点A"
    assert folder.id in body[0]["virtual_folder_ids"]
    assert body[0]["tag_ids"] == []
