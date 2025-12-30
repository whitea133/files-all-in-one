"""备份与恢复模块 BK-001 ~ BK-007 用例。"""

import os
import tempfile
from pathlib import Path

import httpx
import pytest
from fastapi import status

from models import BackupRecord, FileAnchor  # noqa: E402


async def _create_anchor(client: httpx.AsyncClient, name: str, path: str):
    folder_resp = await client.post("/folders/", json={"name": "备份文件夹", "description": None})
    folder_resp.raise_for_status()
    folder_id = folder_resp.json()["id"]
    resp = await client.post("/anchors/", json={"name": name, "path": path, "description": None, "folder_id": folder_id})
    return resp


@pytest.fixture(autouse=True)
def mock_backup_path(monkeypatch, tmp_path):
    # 将 LOCALAPPDATA 指向临时目录，写入 settings.toml 指定备份路径
    fake_root = tmp_path / "FAIO_Data"
    fake_root.mkdir(parents=True, exist_ok=True)
    settings_file = fake_root / "settings.toml"
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    settings_file.write_text(f'backup_path = "{backup_dir.as_posix()}"', encoding="utf-8")
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    yield backup_dir


def _write_source_file(tmp_dir: Path, name: str, content: str = "data") -> Path:
    path = tmp_dir / name
    path.write_text(content, encoding="utf-8")
    return path


@pytest.mark.asyncio
async def test_bk001_backup_success(client: httpx.AsyncClient, tmp_path: Path):
    # BK-001：创建备份（文件存在）
    src = _write_source_file(tmp_path, "os作业1.txt")
    resp = await _create_anchor(client, name="操作系统作业1", path=str(src))
    anchor = resp.json()

    backup_resp = await client.post(f"/backups/{anchor['id']}")
    assert backup_resp.status_code == status.HTTP_201_CREATED
    record = backup_resp.json()
    assert record["file_anchor_id"] == anchor["id"]
    assert Path(record["backup_path"]).exists()


@pytest.mark.asyncio
async def test_bk002_backup_path_not_configured(client: httpx.AsyncClient, monkeypatch, tmp_path: Path):
    # BK-002：备份路径未配置（删除 settings.toml）
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    settings = Path(tmp_path) / "FAIO_Data" / "settings.toml"
    if settings.exists():
        settings.unlink()
    resp = await _create_anchor(client, name="操作系统作业2", path=str(_write_source_file(tmp_path, "os2.txt")))
    anchor = resp.json()

    backup_resp = await client.post(f"/backups/{anchor['id']}")
    assert backup_resp.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.asyncio
async def test_bk003_backup_missing_file(client: httpx.AsyncClient, tmp_path: Path):
    # BK-003：创建备份（文件不存在）
    missing = tmp_path / "missing.txt"
    resp = await _create_anchor(client, name="缺失文件锚点", path=str(missing))
    anchor = resp.json()

    backup_resp = await client.post(f"/backups/{anchor['id']}")
    assert backup_resp.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_bk004_restore_file_not_found(client: httpx.AsyncClient, tmp_path: Path):
    # BK-004：恢复备份（目标不存在但备份文件缺失 => 404）
    src = _write_source_file(tmp_path, "restore-missing.txt")
    resp = await _create_anchor(client, name="备份后删除文件", path=str(src))
    anchor = resp.json()
    backup = await client.post(f"/backups/{anchor['id']}")
    backup_id = backup.json()["id"]

    # 删除备份文件
    Path(backup.json()["backup_path"]).unlink()
    restore_resp = await client.post(f"/backups/{backup_id}/restore")
    assert restore_resp.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_bk005_restore_success(client: httpx.AsyncClient, tmp_path: Path):
    # BK-005：恢复备份（文件不存在，备份存在）
    src = _write_source_file(tmp_path, "restore-ok.txt")
    resp = await _create_anchor(client, name="可恢复锚点", path=str(src))
    anchor = resp.json()
    backup = await client.post(f"/backups/{anchor['id']}")
    backup_id = backup.json()["id"]

    # 删除原文件，确保不存在
    Path(anchor["path"]).unlink()
    restore_resp = await client.post(f"/backups/{backup_id}/restore")
    assert restore_resp.status_code == status.HTTP_200_OK
    # 文件恢复到原路径
    assert Path(anchor["path"]).exists()


@pytest.mark.asyncio
async def test_bk006_delete_backup_record(client: httpx.AsyncClient, tmp_path: Path):
    # BK-006：删除备份（有备份记录）
    src = _write_source_file(tmp_path, "del-backup.txt")
    resp = await _create_anchor(client, name="删除备份锚点", path=str(src))
    anchor = resp.json()
    backup = await client.post(f"/backups/{anchor['id']}")
    backup_id = backup.json()["id"]

    del_resp = await client.delete(f"/backups/{backup_id}")
    assert del_resp.status_code == status.HTTP_204_NO_CONTENT
    assert not await BackupRecord.filter(id=backup_id).exists()


@pytest.mark.asyncio
async def test_bk007_delete_backup_record_missing_file(client: httpx.AsyncClient, tmp_path: Path):
    # BK-007：删除备份记录（文件缺失也能删除）
    src = _write_source_file(tmp_path, "del-backup-missing.txt")
    resp = await _create_anchor(client, name="备份文件丢失", path=str(src))
    anchor = resp.json()
    backup = await client.post(f"/backups/{anchor['id']}")
    backup_id = backup.json()["id"]
    # 删除备份文件
    Path(backup.json()["backup_path"]).unlink()

    del_resp = await client.delete(f"/backups/{backup_id}")
    assert del_resp.status_code == status.HTTP_204_NO_CONTENT
    assert not await BackupRecord.filter(id=backup_id).exists()
