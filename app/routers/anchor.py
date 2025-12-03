from datetime import datetime

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from models import FileAnchor, Tag, VirtualFolder


router = APIRouter(prefix="/anchors", tags=["file-anchors"])


class AnchorCreate(BaseModel):
    """请求体：创建资料锚点。"""

    name: str = Field(..., min_length=1, max_length=255)
    path: str = Field(..., min_length=1, max_length=1024)
    description: str | None = Field(default=None)
    virtual_folder_ids: list[int] = Field(default_factory=list)
    tag_ids: list[int] = Field(default_factory=list)


class AnchorResponse(BaseModel):
    """响应体：资料锚点基础信息。"""

    id: int
    name: str
    path: str
    description: str | None = None
    is_valid: bool
    create_time: datetime
    update_time: datetime
    virtual_folder_ids: list[int]
    tag_ids: list[int]

    model_config = ConfigDict(from_attributes=True)


@router.post("/", response_model=AnchorResponse, status_code=status.HTTP_201_CREATED)
async def create_anchor(payload: AnchorCreate) -> AnchorResponse:
    """
    创建资料锚点，支持同时绑定虚拟文件夹和标签。
    - 若指定的虚拟文件夹或标签不存在，返回 404。
    """
    folder_ids = list(dict.fromkeys(payload.virtual_folder_ids))
    tag_ids = list(dict.fromkeys(payload.tag_ids))

    folders = []
    if folder_ids:
        folders = await VirtualFolder.filter(id__in=folder_ids)
        if len(folders) != len(folder_ids):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="部分虚拟文件夹不存在")

    tags = []
    if tag_ids:
        tags = await Tag.filter(id__in=tag_ids)
        if len(tags) != len(tag_ids):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="部分标签不存在")

    anchor = await FileAnchor.create(
        name=payload.name,
        path=payload.path,
        description=payload.description,
    )

    if folders:
        await anchor.virtual_folders.add(*folders)
    if tags:
        await anchor.tags.add(*tags)

    await anchor.refresh_from_db()

    return AnchorResponse(
        id=anchor.id,
        name=anchor.name,
        path=anchor.path,
        description=anchor.description,
        is_valid=anchor.is_valid,
        create_time=anchor.create_time,
        update_time=anchor.update_time,
        virtual_folder_ids=folder_ids,
        tag_ids=tag_ids,
    )
