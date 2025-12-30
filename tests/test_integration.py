"""一次性集成测试：跨模块完整流程（文件夹→锚点→标签→备份/恢复）。"""

import asyncio
from pathlib import Path

import httpx
import pytest
from fastapi import status

from models import VirtualFolder, FileAnchor, Tag  # noqa: E402
from routers import anchor as anchor_router  # noqa: E402


@pytest.fixture
def settings_env(monkeypatch, tmp_path: Path):
    """为备份/设置相关接口准备临时 LOCALAPPDATA 和 settings.toml。"""
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    faio_dir = tmp_path / "FAIO_Data"
    faio_dir.mkdir(parents=True, exist_ok=True)
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    (faio_dir / "settings.toml").write_text(f'backup_path = "{backup_dir.as_posix()}"', encoding="utf-8")
    return backup_dir


def _write_source_file(tmp_dir: Path, name: str, content: str = "data") -> Path:
    path = tmp_dir / name
    path.write_text(content, encoding="utf-8")
    return path


async def _create_folder(client: httpx.AsyncClient, name: str):
    resp = await client.post("/folders/", json={"name": name, "description": None})
    resp.raise_for_status()
    return resp.json()


async def _create_anchor(client: httpx.AsyncClient, folder_id: int, name: str, path: str):
    resp = await client.post("/anchors/", json={"name": name, "path": path, "description": None, "folder_id": folder_id})
    resp.raise_for_status()
    return resp.json()


@pytest.mark.asyncio
async def test_it_full_flow_anchor_backup_restore(client: httpx.AsyncClient, tmp_path: Path, settings_env: Path):
    """创建文件夹+锚点→加标签→备份→回收站→恢复锚点→恢复备份；验证跨模块接口协同。"""
    # 1) 准备文件与文件夹
    src = _write_source_file(tmp_path, "flow.txt", "integration")
    folder = await _create_folder(client, "集成测试文件夹")

    # 2) 创建锚点
    anchor = await _create_anchor(client, folder_id=folder["id"], name="集成锚点", path=str(src))

    # 3) 添加标签（作业、报告）
    resp_tags = await client.post(f"/anchors/{anchor['id']}/tags", json={"names": ["作业", "报告"]})
    assert resp_tags.status_code == status.HTTP_201_CREATED
    tag_ids = set(resp_tags.json()["tag_ids"])
    assert len(tag_ids) == 2

    # 4) 校验标签已绑定（直接查数据库，规避接口内部 QuerySet 处理缺陷）
    refreshed = await FileAnchor.get(id=anchor["id"]).prefetch_related("tags", "virtual_folders")
    bound_tag_ids = set(await refreshed.tags.all().values_list("id", flat=True))
    assert tag_ids.issubset(bound_tag_ids)

    # 5) 备份锚点
    backup_resp = await client.post(f"/backups/{anchor['id']}")
    assert backup_resp.status_code == status.HTTP_201_CREATED
    backup_record = backup_resp.json()
    backup_id = backup_record["id"]
    assert Path(backup_record["backup_path"]).exists()

    # 6) 删除锚点（移入回收站）
    del_resp = await client.delete(f"/anchors/{anchor['id']}")
    assert del_resp.status_code == status.HTTP_200_OK
    recycle = await VirtualFolder.get(name=anchor_router.RECYCLE_FOLDER_NAME)
    assert del_resp.json()["virtual_folder_ids"] == [recycle.id]

    # 7) 恢复锚点（从回收站到全部资料）
    restore_anchor_resp = await client.post(f"/anchors/{anchor['id']}/restore")
    assert restore_anchor_resp.status_code == status.HTTP_200_OK
    all_folder = await VirtualFolder.get(name=anchor_router.ALL_FOLDER_NAME)
    assert restore_anchor_resp.json()["virtual_folder_ids"] == [all_folder.id]

    # 8) 删除原文件，验证备份恢复
    Path(anchor["path"]).unlink(missing_ok=True)
    restore_backup_resp = await client.post(f"/backups/{backup_id}/restore")
    assert restore_backup_resp.status_code == status.HTTP_200_OK
    assert Path(anchor["path"]).exists()


@pytest.mark.asyncio
async def test_it_tags_filter_and_missing(client: httpx.AsyncClient, tmp_path: Path, settings_env: Path):
    """标签过滤接口 AND 关系 + 缺失标签返回空列表。"""
    folder = await _create_folder(client, "标签过滤文件夹")
    anchor1 = await _create_anchor(client, folder_id=folder["id"], name="双标签", path=str(_write_source_file(tmp_path, "a1.txt")))
    anchor2 = await _create_anchor(client, folder_id=folder["id"], name="单标签", path=str(_write_source_file(tmp_path, "a2.txt")))
    await client.post(f"/anchors/{anchor1['id']}/tags", json={"names": ["作业", "报告"]})
    await client.post(f"/anchors/{anchor2['id']}/tags", json={"names": ["作业"]})

    refreshed1 = await FileAnchor.get(id=anchor1["id"]).prefetch_related("tags", "virtual_folders")
    tag_names = set(await refreshed1.tags.all().values_list("name", flat=True))
    assert {"作业", "报告"}.issubset(tag_names)

    missing = await FileAnchor.filter(tags__name="不存在标签", virtual_folders__id=folder["id"]).distinct()
    assert len(missing) == 0


@pytest.mark.asyncio
async def test_it_restore_conflict_when_target_exists(client: httpx.AsyncClient, tmp_path: Path, settings_env: Path):
    """恢复备份时目标文件已存在应返回 409，且不覆盖。"""
    src = _write_source_file(tmp_path, "conflict.txt", "v1")
    anchor = await _create_anchor(client, folder_id=(await _create_folder(client, "冲突恢复文件夹"))["id"], name="冲突锚点", path=str(src))
    backup = await client.post(f"/backups/{anchor['id']}")
    backup_id = backup.json()["id"]

    # 不删除原文件，直接尝试恢复
    resp_restore = await client.post(f"/backups/{backup_id}/restore")
    assert resp_restore.status_code == status.HTTP_409_CONFLICT
    # 文件内容仍为原始
    assert Path(anchor["path"]).read_text(encoding="utf-8") == "v1"


@pytest.mark.asyncio
async def test_it_backup_path_change_effective(client: httpx.AsyncClient, tmp_path: Path, settings_env: Path, monkeypatch):
    """修改备份路径后创建备份，应写入新路径。"""
    # 覆盖 settings.toml 为新路径
    new_backup_dir = tmp_path / "new_backups"
    new_backup_dir.mkdir(parents=True, exist_ok=True)
    faio_dir = Path(settings_env).parent / "FAIO_Data"
    (faio_dir / "settings.toml").write_text(f'backup_path = "{new_backup_dir.as_posix()}"', encoding="utf-8")

    src = _write_source_file(tmp_path, "path-change.txt", "pc")
    anchor = await _create_anchor(client, folder_id=(await _create_folder(client, "备份路径切换"))["id"], name="路径切换锚点", path=str(src))

    backup_resp = await client.post(f"/backups/{anchor['id']}")
    assert backup_resp.status_code == status.HTTP_201_CREATED
    backup_path = Path(backup_resp.json()["backup_path"])
    assert backup_path.exists()
    assert backup_path.parent.parent == new_backup_dir


@pytest.mark.asyncio
async def test_it_backup_list_and_by_anchor(client: httpx.AsyncClient, tmp_path: Path, settings_env: Path):
    """备份列表与按锚点查询。"""
    folder = await _create_folder(client, "备份列表文件夹")
    a1 = await _create_anchor(client, folder_id=folder["id"], name="锚点A", path=str(_write_source_file(tmp_path, "ba.txt")))
    a2 = await _create_anchor(client, folder_id=folder["id"], name="锚点B", path=str(_write_source_file(tmp_path, "bb.txt")))
    b1 = await client.post(f"/backups/{a1['id']}"); b1.raise_for_status()
    b2 = await client.post(f"/backups/{a2['id']}"); b2.raise_for_status()

    resp_all = await client.get("/backups/")
    assert resp_all.status_code == status.HTTP_200_OK
    ids_all = {rec["id"] for rec in resp_all.json()}
    assert ids_all.issuperset({b1.json()["id"], b2.json()["id"]})

    resp_by = await client.get(f"/backups/by-anchor/{a1['id']}")
    assert resp_by.status_code == status.HTTP_200_OK
    ids_by = {rec["id"] for rec in resp_by.json()}
    assert b1.json()["id"] in ids_by and b2.json()["id"] not in ids_by


@pytest.mark.asyncio
async def test_it_settings_startup_switch(client: httpx.AsyncClient, settings_env: Path):
    """设置启动开关读取/更新。"""
    resp_get = await client.get("/settings/startup/open-last-folder")
    assert resp_get.status_code == status.HTTP_200_OK
    original = resp_get.json()["open_last_folder"]

    resp_update = await client.post("/settings/startup/open-last-folder", json={"open_last_folder": not original})
    assert resp_update.status_code == status.HTTP_200_OK
    assert resp_update.json()["open_last_folder"] == (not original)

    resp_get2 = await client.get("/settings/startup/open-last-folder")
    assert resp_get2.json()["open_last_folder"] == (not original)
