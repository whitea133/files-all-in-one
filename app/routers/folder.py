from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field
from tortoise.exceptions import IntegrityError

from models import FileAnchor, Tag, VirtualFolder
from utils.operation_log import log_operation
from routers.anchor import AnchorResponse


router = APIRouter(prefix="/folders", tags=["virtual-folders"])
RECYCLE_FOLDER_NAME = "回收站"


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
async def list_virtual_folders(keyword: str | None = Query(default=None, min_length=1, max_length=255)) -> list[VirtualFolderResponse]:
    """
    列出虚拟文件夹，可按名称模糊查询。
    """
    qs = VirtualFolder.all()
    if keyword:
        qs = qs.filter(name__icontains=keyword)
    folders = await qs.order_by("id")
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

    await log_operation("创建虚拟文件夹", f"创建虚拟文件夹「{folder.name}」")

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
    old_name = folder.name

    if await VirtualFolder.filter(name=payload.name).exclude(id=folder_id).exists():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="虚拟文件夹名称已存在")

    folder.name = payload.name
    folder.description = payload.description
    try:
        await folder.save()
    except IntegrityError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="虚拟文件夹名称已存在")

    await log_operation(
        "重命名虚拟文件夹",
        f"将虚拟文件夹「{old_name}」重命名为「{folder.name}」",
    )

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

    await log_operation("删除虚拟文件夹", f"删除虚拟文件夹「{folder.name}」")
    await folder.delete()

# -----------虚拟文件夹与资料锚点相关操作-----------
@router.get("/{folder_id}/anchors", response_model=list[AnchorResponse])
async def list_folder_anchors(folder_id: int) -> list[AnchorResponse]:
    """
    列出指定虚拟文件夹下的所有资料锚点。
    """
    folder = await VirtualFolder.filter(id=folder_id).first()
    if not folder:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="虚拟文件夹不存在")

    anchors = await FileAnchor.filter(virtual_folders__id=folder_id).distinct()

    results: list[AnchorResponse] = []
    for anchor in anchors:
        folder_ids = await anchor.virtual_folders.all().values_list("id", flat=True)
        tag_ids = await anchor.tags.all().values_list("id", flat=True)
        results.append(
            AnchorResponse(
                id=anchor.id,
                name=anchor.name,
                path=anchor.path,
                description=anchor.description,
                is_valid=anchor.is_valid,
                create_time=anchor.create_time,
                update_time=anchor.update_time,
                virtual_folder_ids=list(folder_ids),
                tag_ids=list(tag_ids),
            )
        )

    return results


@router.delete("/recycle/empty", status_code=status.HTTP_204_NO_CONTENT)
async def empty_recycle_bin() -> None:
    """
    清空回收站：永久删除回收站中的所有资料锚点。
    """
    recycle_folder = await VirtualFolder.filter(name=RECYCLE_FOLDER_NAME).first()
    if not recycle_folder:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="回收站不存在")

    anchors = await FileAnchor.filter(virtual_folders__id=recycle_folder.id).distinct()
    deleted_count = len(anchors)
    for anchor in anchors:
        tags = await anchor.tags.all()
        for tag in tags:
            if tag.use_count > 0:
                tag.use_count -= 1
                await tag.save()
        await anchor.delete()

    await log_operation("清空回收站", f"清空回收站，永久删除 {deleted_count} 个锚点")
