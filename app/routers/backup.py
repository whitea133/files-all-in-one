from __future__ import annotations

import os
import shutil
import time
from pathlib import Path
from typing import List

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from models import BackupRecord, FileAnchor


router = APIRouter(prefix="/backups", tags=["backups"])


def _settings_file() -> Path:
    root = Path(os.getenv("LOCALAPPDATA", Path.home())) / "AmberDay_Data"
    root.mkdir(parents=True, exist_ok=True)
    return root / "settings.toml"


def _load_backup_dir() -> Path:
    path = _settings_file()
    if not path.exists():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="备份路径未配置")
    try:
        import tomllib
    except ImportError as exc:  # pragma: no cover - 仅防御
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    backup_path = data.get("backup_path")
    if not backup_path:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="备份路径未配置")
    return Path(backup_path)


class BackupRecordResponse(BaseModel):
    id: int
    file_anchor_id: int
    file_anchor_name: str
    file_anchor_path: str
    backup_path: str
    backup_time: str

    @classmethod
    def from_model(cls, rec: BackupRecord) -> "BackupRecordResponse":
        anchor = rec.file_anchor
        return cls(
            id=rec.id,
            file_anchor_id=anchor.id,
            file_anchor_name=anchor.name,
            file_anchor_path=anchor.path,
            backup_path=rec.backup_path,
            backup_time=rec.backup_time.isoformat() if rec.backup_time else "",
        )


@router.get("/", response_model=List[BackupRecordResponse])
async def list_backups() -> List[BackupRecordResponse]:
    records = await BackupRecord.all().prefetch_related("file_anchor").order_by("-backup_time")
    return [BackupRecordResponse.from_model(rec) for rec in records]


@router.get("/by-anchor/{anchor_id}", response_model=List[BackupRecordResponse])
async def list_backups_by_anchor(anchor_id: int) -> List[BackupRecordResponse]:
    records = (
        await BackupRecord.filter(file_anchor_id=anchor_id)
        .prefetch_related("file_anchor")
        .order_by("-backup_time")
    )
    return [BackupRecordResponse.from_model(rec) for rec in records]




@router.post("/{anchor_id}", response_model=BackupRecordResponse, status_code=status.HTTP_201_CREATED)
async def backup_anchor(anchor_id: int) -> BackupRecordResponse:
    anchor = await FileAnchor.filter(id=anchor_id).first()
    if not anchor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="资料锚点不存在")

    source = Path(anchor.path).expanduser()
    if not source.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="资料文件不存在")

    backup_dir = _load_backup_dir()
    backup_dir.mkdir(parents=True, exist_ok=True)

    dest_dir = backup_dir / str(anchor.id)
    dest_dir.mkdir(parents=True, exist_ok=True)

    ts = int(time.time())
    dest_path = dest_dir / f"{source.stem}-{ts}{source.suffix}"

    try:
        shutil.copy2(source, dest_path)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"备份失败: {exc}")

    rec = await BackupRecord.create(file_anchor=anchor, backup_path=str(dest_path))
    return BackupRecordResponse.from_model(rec)


@router.post("/{backup_id}/restore", response_model=BackupRecordResponse)
async def restore_backup(backup_id: int) -> BackupRecordResponse:
    rec = await BackupRecord.filter(id=backup_id).prefetch_related("file_anchor").first()
    if not rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="备份记录不存在")

    backup_path = Path(rec.backup_path).expanduser()
    if not backup_path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="备份文件不存在")

    anchor = rec.file_anchor
    target = Path(anchor.path).expanduser()
    if target.exists():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="目标文件已存在，取消恢复以避免覆盖")

    target.parent.mkdir(parents=True, exist_ok=True)

    try:
        shutil.copy2(backup_path, target)
        anchor.is_valid = True
        await anchor.save()
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"恢复失败: {exc}")

    # 刷新记录以返回最新 anchor 信息
    await rec.fetch_related("file_anchor")
    return BackupRecordResponse.from_model(rec)


@router.delete("/{backup_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_backup(backup_id: int) -> None:
    rec = await BackupRecord.filter(id=backup_id).first()
    if not rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="备份记录不存在")

    backup_path = Path(rec.backup_path).expanduser()
    try:
        if backup_path.exists():
            backup_path.unlink()
    except Exception:
        # 如果文件删除失败，不影响记录删除，避免阻塞
        pass

    await rec.delete()
