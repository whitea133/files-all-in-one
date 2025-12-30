"""系统设置模块 ST-001 ~ ST-003 用例。"""

import os
from pathlib import Path

import httpx
import pytest
from fastapi import status


@pytest.fixture
def settings_env(monkeypatch, tmp_path: Path):
    # 将 LOCALAPPDATA 指向临时目录，供 settings 路由读写 settings.toml
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    return tmp_path


@pytest.mark.asyncio
async def test_st001_get_backup_path(client: httpx.AsyncClient, settings_env: Path):
    # ST-001：进入设置页，查看备份设置
    settings_dir = Path(settings_env) / "FAIO_Data"
    settings_dir.mkdir(parents=True, exist_ok=True)
    backup_dir = settings_env / "backup_conf"
    backup_dir.mkdir(parents=True, exist_ok=True)
    (settings_dir / "settings.toml").write_text(f'backup_path = "{backup_dir.as_posix()}"', encoding="utf-8")

    resp = await client.get("/settings/backup/path")
    assert resp.status_code == status.HTTP_200_OK
    assert resp.json()["backup_path"] == backup_dir.as_posix()


@pytest.mark.asyncio
async def test_st002_select_valid_backup_path(client: httpx.AsyncClient, settings_env: Path, monkeypatch):
    # ST-002：在备份设置中，选择有效备份路径
    chosen_dir = settings_env / "chosen_backup"
    chosen_dir.mkdir(parents=True, exist_ok=True)

    class FakeWindow:
        def create_file_dialog(self, dialog_type):
            return [chosen_dir.as_posix()]

    monkeypatch.setenv("LOCALAPPDATA", str(settings_env))
    monkeypatch.setattr("routers.useSetting.webview.active_window", lambda: FakeWindow())

    resp = await client.post("/settings/backup/path/select")
    assert resp.status_code == status.HTTP_200_OK
    assert resp.json()["backup_path"] == chosen_dir.as_posix()

    # 再次读取确保配置已更新
    resp_get = await client.get("/settings/backup/path")
    assert resp_get.json()["backup_path"] == chosen_dir.as_posix()


@pytest.mark.asyncio
async def test_st003_select_invalid_backup_path(client: httpx.AsyncClient, settings_env: Path, monkeypatch):
    # ST-003：备份设置中，未选择/无效路径 -> 保存失败，不更改配置
    monkeypatch.setenv("LOCALAPPDATA", str(settings_env))

    class FakeWindowEmpty:
        def create_file_dialog(self, dialog_type):
            return None  # 模拟未选择

    # 先写入一个有效路径，确保失败时不会被覆盖
    settings_dir = settings_env / "FAIO_Data"
    settings_dir.mkdir(parents=True, exist_ok=True)
    valid_dir = settings_env / "valid_backup"
    valid_dir.mkdir(parents=True, exist_ok=True)
    (settings_dir / "settings.toml").write_text(f'backup_path = "{valid_dir.as_posix()}"', encoding="utf-8")

    monkeypatch.setattr("routers.useSetting.webview.active_window", lambda: FakeWindowEmpty())

    resp = await client.post("/settings/backup/path/select")
    assert resp.status_code == status.HTTP_400_BAD_REQUEST

    # 配置仍为原有效路径
    resp_get = await client.get("/settings/backup/path")
    assert resp_get.json()["backup_path"] == valid_dir.as_posix()
