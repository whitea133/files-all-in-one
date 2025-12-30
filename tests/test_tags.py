"""资料标签模块 TAG-001 ~ TAG-004 用例。"""

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
    resp.raise_for_status()
    return resp.json()


@pytest.mark.asyncio
async def test_tag001_add_tag(client: httpx.AsyncClient):
    # TAG-001：为锚点添加标签（可新建）
    folder = await _create_folder(client, "操作系统")
    anchor = await _create_anchor(client, folder_id=folder["id"], name="操作系统锚点", path="/tmp/os.txt")

    resp = await client.post(f"/anchors/{anchor['id']}/tags", json={"names": ["操作系统"]})
    assert resp.status_code == status.HTTP_201_CREATED
    data = resp.json()
    assert "操作系统" in [t.name for t in await Tag.filter(id__in=data["tag_ids"])]
    # use_count >=1
    tag = await Tag.get(name="操作系统")
    assert tag.use_count >= 1


@pytest.mark.asyncio
async def test_tag002_remove_tag(client: httpx.AsyncClient):
    # TAG-002：为锚点移除标签
    folder = await _create_folder(client, "操作系统")
    anchor = await _create_anchor(client, folder_id=folder["id"], name="移除标签锚点", path="/tmp/os.txt")
    resp_add = await client.post(f"/anchors/{anchor['id']}/tags", json={"names": ["待完成"]})
    tag_id = resp_add.json()["tag_ids"][0]

    resp = await client.delete(f"/anchors/{anchor['id']}/tags/{tag_id}")
    assert resp.status_code == status.HTTP_200_OK
    assert tag_id not in resp.json()["tag_ids"]
    tag = await Tag.get(id=tag_id)
    assert tag.use_count >= 0


@pytest.mark.asyncio
async def test_tag003_delete_tag_with_binding(client: httpx.AsyncClient):
    # TAG-003：删除标签（存在绑定关系），解除所有锚点绑定
    folder = await _create_folder(client, "操作系统")
    anchor = await _create_anchor(client, folder_id=folder["id"], name="绑定标签锚点", path="/tmp/os.txt")
    resp_add = await client.post(f"/anchors/{anchor['id']}/tags", json={"names": ["操作系统"]})
    tag_id = resp_add.json()["tag_ids"][0]

    resp = await client.delete(f"/tags/{tag_id}")
    assert resp.status_code == status.HTTP_204_NO_CONTENT
    assert not await Tag.filter(id=tag_id).exists()
    # 确认锚点解绑
    reloaded = await FileAnchor.get(id=anchor["id"]).prefetch_related("tags")
    assert len(await reloaded.tags.all()) == 0


@pytest.mark.asyncio
async def test_tag004_delete_tag_without_binding(client: httpx.AsyncClient):
    # TAG-004：删除标签（无绑定），直接从标签列表移除
    tag = await Tag.create(name="临时标签")
    resp = await client.delete(f"/tags/{tag.id}")
    assert resp.status_code == status.HTTP_204_NO_CONTENT
    assert not await Tag.filter(id=tag.id).exists()
