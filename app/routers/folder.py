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


class VirtualFolderResponse(BaseModel):
    """响应体：虚拟文件夹基本信息。"""

    id: int
    name: str
    description: str | None = None
    create_time: datetime

    model_config = ConfigDict(from_attributes=True)  # 支持 ORM 数据直接转换


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