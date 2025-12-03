from datetime import datetime

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from tortoise.exceptions import IntegrityError

from models import VirtualFolder


router = APIRouter(prefix="/folders", tags=["virtual-folders"])


class VirtualFolderCreate(BaseModel):
    """请求体：创建虚拟文件夹。"""

    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(default=None)


class VirtualFolderUpdate(BaseModel):
    """请求体：重命名/更新描述。"""

    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(default=None)


class VirtualFolderResponse(BaseModel):
    """响应体：虚拟文件夹基本信息。"""

    id: int
    name: str
    description: str | None = None
    create_time: datetime
    is_system: bool

    model_config = ConfigDict(from_attributes=True)  # 支持 ORM 数据直接转换


@router.get("/", response_model=list[VirtualFolderResponse])
async def list_virtual_folders() -> list[VirtualFolderResponse]:
    """列出全部虚拟文件夹。"""
    folders = await VirtualFolder.all().order_by("id")
    return [VirtualFolderResponse.model_validate(f) for f in folders]


@router.post("/", response_model=VirtualFolderResponse, status_code=status.HTTP_201_CREATED)
async def create_virtual_folder(payload: VirtualFolderCreate) -> VirtualFolderResponse:
    """
    创建虚拟文件夹。
    - 名称唯一；如重复返回 409。
    """
    exists = await VirtualFolder.filter(name=payload.name).exists()
    if exists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="虚拟文件夹已存在")

    try:
        folder = await VirtualFolder.create(name=payload.name, description=payload.description)
    except IntegrityError:
        # 并发场景下的重复创建保护
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="虚拟文件夹已存在")

    return folder


@router.patch("/{folder_id}", response_model=VirtualFolderResponse)
async def rename_virtual_folder(folder_id: int, payload: VirtualFolderUpdate) -> VirtualFolderResponse:
    """
    重命名虚拟文件夹并可更新描述。
    - 系统文件夹禁止修改。
    - 名称唯一；冲突返回 409。
    """
    folder = await VirtualFolder.filter(id=folder_id).first()
    if not folder:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="虚拟文件夹不存在")
    if folder.is_system:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="系统虚拟文件夹不可修改")

    if await VirtualFolder.filter(name=payload.name).exclude(id=folder_id).exists():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="虚拟文件夹名称已存在")

    folder.name = payload.name
    folder.description = payload.description
    try:
        await folder.save()
    except IntegrityError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="虚拟文件夹名称已存在")

    return folder


@router.delete("/{folder_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_virtual_folder(folder_id: int) -> None:
    """
    删除虚拟文件夹。
    - 系统文件夹禁止删除。
    """
    folder = await VirtualFolder.filter(id=folder_id).first()
    if not folder:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="虚拟文件夹不存在")
    if folder.is_system:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="系统虚拟文件夹不可删除")

    await folder.delete()
