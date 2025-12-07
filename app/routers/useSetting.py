from __future__ import annotations

import os
import tomllib  # 只能用于读取toml文件
import tomli_w  # 可以写toml文件
from pathlib import Path

from fastapi import APIRouter, HTTPException, status
import webview
from pydantic import BaseModel, Field

router = APIRouter(prefix="/settings", tags=["settings"])


def _settings_file() -> Path:
    root = Path(os.getenv("LOCALAPPDATA", Path.home())) / "AmberDay_Data"
    root.mkdir(parents=True, exist_ok=True)
    return root / "settings.toml"


def _load_settings() -> dict:
    path = _settings_file()
    if not path.exists():
        return {}
    try:
        return tomllib.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_settings(data: dict) -> None:
    path = _settings_file()
    path.write_text(tomli_w.dumps(data), encoding="utf-8")


class BackupPathResponse(BaseModel):
    backup_path: str = ""


class BackupPathUpdate(BaseModel):
    backup_path: str = Field(..., min_length=1, max_length=1024)


@router.get("/backup/path", response_model=BackupPathResponse)
def get_backup_path() -> BackupPathResponse:
    data = _load_settings()
    return BackupPathResponse(backup_path=data.get("backup_path", ""))


@router.post("/backup/path/select", response_model=BackupPathResponse)
def select_backup_path() -> BackupPathResponse:
    """
    调用 pywebview 的文件对话框选择备份目录，更新设置并返回路径。
    """
    window = webview.active_window()
    if not window:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="窗口未就绪，无法打开对话框")

    try:
        paths = window.create_file_dialog(webview.FOLDER_DIALOG)
    except Exception as exc:  # pragma: no cover - UI 相关异常
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))

    if not paths:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="未选择路径")

    chosen = paths[0]
    if not Path(chosen).is_dir():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="请选择文件夹路径")

    data = _load_settings()
    data["backup_path"] = chosen
    _save_settings(data)
    return BackupPathResponse(backup_path=chosen)
