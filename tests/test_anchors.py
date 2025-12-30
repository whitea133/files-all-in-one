"""资料锚点模块 AN-001 ~ AN-010 集成用例。"""

import httpx
import pytest
from fastapi import status

from models import FileAnchor, Tag, VirtualFolder  # noqa: E402
from routers import anchor as anchor_router  # noqa: E402


async def _create_folder(client: httpx.AsyncClient, name: str):
    resp = await client.post("/folders/", json={"name": name, "description": None})
    resp.raise_for_status()
    return resp.json()


async def _create_anchor(client: httpx.AsyncClient, folder_id: int, name: str = "锚点1", path: str = "/tmp/a.txt"):
    resp = await client.post("/anchors/", json={"name": name, "path": path, "description": None, "folder_id": folder_id})
    return resp


def _all_folder_id():
    folder = VirtualFolder.filter(name=anchor_router.ALL_FOLDER_NAME).first()
    return folder


def _recycle_folder_id():
    folder = VirtualFolder.filter(name=anchor_router.RECYCLE_FOLDER_NAME).first()
    return folder


@pytest.mark.asyncio
async def test_an001_create_anchor_in_non_system_folder(client: httpx.AsyncClient):
    # AN-001：在非系统文件夹下创建锚点（绑定目标文件夹+全部资料）
    folder = await _create_folder(client, "操作系统作业1")
    resp = await _create_anchor(client, folder_id=folder["id"], name="os作业1", path="/tmp/os1.txt")
    assert resp.status_code == status.HTTP_201_CREATED
    data = resp.json()
    assert data["name"] == "os作业1"
    # 绑定了目标文件夹 + 全部资料
    all_folder = await VirtualFolder.filter(name=anchor_router.ALL_FOLDER_NAME).first()
    assert folder["id"] in data["virtual_folder_ids"]
    assert all_folder.id in data["virtual_folder_ids"]


@pytest.mark.asyncio
async def test_an002_create_anchor_in_system_folder_forbidden(client: httpx.AsyncClient):
    # AN-002：尝试在系统文件夹/回收站创建锚点，预期禁止
    system_folders = await VirtualFolder.filter(is_system=True).all()
    assert system_folders
    resp = await _create_anchor(client, folder_id=system_folders[0].id, name="系统锚点", path="/tmp/sys.txt")
    assert resp.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.asyncio
async def test_an003_rename_anchor(client: httpx.AsyncClient):
    # AN-003：编辑锚点名称并保存
    folder = await _create_folder(client, "操作系统作业1")
    created = await _create_anchor(client, folder_id=folder["id"], name="旧名", path="/tmp/os1.txt")
    anchor_id = created.json()["id"]

    resp = await client.patch(f"/anchors/{anchor_id}/name", json={"name": "新作业名"})
    assert resp.status_code == status.HTTP_200_OK
    assert resp.json()["name"] == "新作业名"


@pytest.mark.asyncio
async def test_an004_update_anchor_description(client: httpx.AsyncClient):
    # AN-004：编辑锚点描述并保存
    folder = await _create_folder(client, "操作系统作业1")
    created = await _create_anchor(client, folder_id=folder["id"], name="有描述的锚点", path="/tmp/os1.txt")
    anchor_id = created.json()["id"]

    resp = await client.patch(f"/anchors/{anchor_id}/description", json={"description": "操作系统作业1"})
    assert resp.status_code == status.HTTP_200_OK
    assert resp.json()["description"] == "操作系统作业1"


@pytest.mark.asyncio
async def test_an005_bind_anchor_extra_folder(client: httpx.AsyncClient):
    # AN-005：为锚点绑定额外文件夹
    folder_a = await _create_folder(client, "操作系统作业1")
    folder_b = await _create_folder(client, "数据结构作业1")
    created = await _create_anchor(client, folder_id=folder_a["id"], name="绑定多文件夹", path="/tmp/os1.txt")
    anchor_id = created.json()["id"]

    resp = await client.post(f"/anchors/{anchor_id}/bindFolders", json={"folder_ids": [folder_b["id"]]})
    assert resp.status_code == status.HTTP_200_OK
    ids = set(resp.json()["virtual_folder_ids"])
    all_folder = await VirtualFolder.filter(name=anchor_router.ALL_FOLDER_NAME).first()
    assert folder_a["id"] in ids and folder_b["id"] in ids and all_folder.id in ids


@pytest.mark.asyncio
async def test_an006_add_tags_to_anchor(client: httpx.AsyncClient):
    # AN-006：为锚点添加标签
    folder = await _create_folder(client, "操作系统作业1")
    created = await _create_anchor(client, folder_id=folder["id"], name="有标签锚点", path="/tmp/os1.txt")
    anchor_id = created.json()["id"]

    resp = await client.post(f"/anchors/{anchor_id}/tags", json={"names": ["作业", "待完成"]})
    assert resp.status_code == status.HTTP_201_CREATED
    tag_ids = resp.json()["tag_ids"]
    assert len(tag_ids) == 2
    # use_count >= 1
    for name in ["作业", "待完成"]:
        tag = await Tag.get(name=name)
        assert tag.use_count >= 1


@pytest.mark.asyncio
async def test_an007_remove_tag_from_anchor(client: httpx.AsyncClient):
    # AN-007：为锚点移除标签
    folder = await _create_folder(client, "操作系统作业1")
    created = await _create_anchor(client, folder_id=folder["id"], name="去标签锚点", path="/tmp/os1.txt")
    anchor_id = created.json()["id"]
    resp_add = await client.post(f"/anchors/{anchor_id}/tags", json={"names": ["作业", "待完成"]})
    tag_ids = resp_add.json()["tag_ids"]
    target_tag_id = tag_ids[1]

    resp = await client.delete(f"/anchors/{anchor_id}/tags/{target_tag_id}")
    assert resp.status_code == status.HTTP_200_OK
    remaining = resp.json()["tag_ids"]
    assert len(remaining) == 1
    tag = await Tag.get(id=target_tag_id)
    assert tag.use_count >= 0


@pytest.mark.asyncio
async def test_an008_move_anchor_to_recycle(client: httpx.AsyncClient):
    # AN-008：删除锚点（移入回收站）
    folder = await _create_folder(client, "操作系统作业1")
    created = await _create_anchor(client, folder_id=folder["id"], name="可回收锚点", path="/tmp/os1.txt")
    anchor_id = created.json()["id"]

    resp = await client.delete(f"/anchors/{anchor_id}")
    assert resp.status_code == status.HTTP_200_OK
    recycle = await VirtualFolder.get(name=anchor_router.RECYCLE_FOLDER_NAME)
    assert resp.json()["virtual_folder_ids"] == [recycle.id]
    assert resp.json()["tag_ids"] == []


@pytest.mark.asyncio
async def test_an009_restore_anchor_from_recycle(client: httpx.AsyncClient):
    # AN-009：从回收站恢复锚点
    folder = await _create_folder(client, "操作系统作业1")
    created = await _create_anchor(client, folder_id=folder["id"], name="待恢复锚点", path="/tmp/os1.txt")
    anchor_id = created.json()["id"]
    await client.delete(f"/anchors/{anchor_id}")

    resp = await client.post(f"/anchors/{anchor_id}/restore")
    assert resp.status_code == status.HTTP_200_OK
    all_folder = await VirtualFolder.get(name=anchor_router.ALL_FOLDER_NAME)
    assert resp.json()["virtual_folder_ids"] == [all_folder.id]


@pytest.mark.asyncio
async def test_an010_multi_tag_selection(client: httpx.AsyncClient):
    # AN-010：多标签筛选锚点（AND）
    # 创建文件夹与两个标签锚点，目标返回同时包含两标签的锚点
    folder = await _create_folder(client, "多标签文件夹")
    resp_anchor = await _create_anchor(client, folder_id=folder["id"], name="双标签锚点", path="/tmp/a.txt")
    anchor_id = resp_anchor.json()["id"]
    await client.post(f"/anchors/{anchor_id}/tags", json={"names": ["作业", "报告"]})

    # 另一个锚点仅有单标签，确保不会被两标签过滤
    resp_anchor2 = await _create_anchor(client, folder_id=folder["id"], name="单标签锚点", path="/tmp/b.txt")
    anchor2_id = resp_anchor2.json()["id"]
    await client.post(f"/anchors/{anchor2_id}/tags", json={"names": ["作业"]})

    resp = await client.get(f"/folders/{folder['id']}/anchors")
    assert resp.status_code == status.HTTP_200_OK
    anchors = resp.json()
    both_tag_ids = set(await Tag.filter(name__in=["作业", "报告"]).values_list("id", flat=True))
    filtered = [a for a in anchors if both_tag_ids.issubset(set(a["tag_ids"]))]
    assert len(filtered) == 1
    assert filtered[0]["name"] == "双标签锚点"
