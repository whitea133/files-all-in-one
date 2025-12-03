from datetime import datetime

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from models import FileAnchor, Tag, VirtualFolder


router = APIRouter(prefix="/anchors", tags=["file-anchors"])
ALL_FOLDER_NAME = "全部资料"
RECYCLE_FOLDER_NAME = "回收站"


class AnchorCreate(BaseModel):
    """请求体：创建资料锚点。"""

    name: str = Field(..., min_length=1, max_length=255)
    path: str = Field(..., min_length=1, max_length=1024)
    description: str | None = Field(default=None)
    folder_id: int = Field(..., description="锚点所属的实际虚拟文件夹（不可为“全部资料”）")


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
    创建资料锚点。
    - 必须指定一个实际文件夹（不可选择“全部资料”），创建时自动同时绑定“全部资料”与该文件夹。
    - 创建时不携带标签，标签需后续单独绑定。
    - 若指定的虚拟文件夹不存在，返回 404。
    """
    target_folder = await VirtualFolder.filter(id=payload.folder_id).first()
    if not target_folder:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="虚拟文件夹不存在")
    if target_folder.name == ALL_FOLDER_NAME or target_folder.is_system:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不能在“全部资料”或系统文件夹下直接创建锚点")

    all_folder, _ = await VirtualFolder.get_or_create(
        name=ALL_FOLDER_NAME,
        defaults={"description": "系统默认文件夹", "is_system": True},
    )

    anchor = await FileAnchor.create(
        name=payload.name,
        path=payload.path,
        description=payload.description,
    )

    await anchor.virtual_folders.add(all_folder, target_folder)

    await anchor.refresh_from_db()

    bound_folder_ids = [all_folder.id, target_folder.id]

    return AnchorResponse(
        id=anchor.id,
        name=anchor.name,
        path=anchor.path,
        description=anchor.description,
        is_valid=anchor.is_valid,
        create_time=anchor.create_time,
        update_time=anchor.update_time,
        virtual_folder_ids=bound_folder_ids,
        tag_ids=[],
    )


@router.delete("/{anchor_id}", response_model=AnchorResponse)
async def move_anchor_to_recycle(anchor_id: int) -> AnchorResponse:
    """
    “删除”资料锚点：将其移动到回收站，仅保留回收站关联，避免物理删除。
    - 若锚点不存在，返回 404。
    - 删除状态通过关联回收站文件夹判断，不改 is_valid（is_valid 仅代表路径有效性）。
    """
    anchor = await FileAnchor.filter(id=anchor_id).first()
    if not anchor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="资料锚点不存在")

    recycle_folder, _ = await VirtualFolder.get_or_create(
        name=RECYCLE_FOLDER_NAME,
        defaults={"description": "系统默认文件夹", "is_system": True},
    )

    # 解绑标签并回收 use_count
    tags = await anchor.tags.all()
    for tag in tags:
        if tag.use_count > 0:
            tag.use_count -= 1
            await tag.save()

    await anchor.virtual_folders.clear()
    await anchor.virtual_folders.add(recycle_folder)
    await anchor.tags.clear()
    await anchor.refresh_from_db()

    return AnchorResponse(
        id=anchor.id,
        name=anchor.name,
        path=anchor.path,
        description=anchor.description,
        is_valid=anchor.is_valid,
        create_time=anchor.create_time,
        update_time=anchor.update_time,
        virtual_folder_ids=[recycle_folder.id],
        tag_ids=[],
    )


class AnchorRestore(BaseModel):
    """请求体：从回收站恢复锚点。"""

    folder_id: int = Field(..., description="恢复后所属的实际虚拟文件夹（不可为“全部资料”/系统文件夹）")


@router.post("/{anchor_id}/restore", response_model=AnchorResponse)
async def restore_anchor(anchor_id: int, payload: AnchorRestore) -> AnchorResponse:
    """
    从回收站恢复资料锚点：
    - 必须当前在回收站，否则返回 400。
    - 恢复时自动绑定“全部资料”与目标文件夹，标签保持为空。
    """
    anchor = await FileAnchor.filter(id=anchor_id).first()
    if not anchor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="资料锚点不存在")

    recycle_folder, _ = await VirtualFolder.get_or_create(
        name=RECYCLE_FOLDER_NAME,
        defaults={"description": "系统默认文件夹", "is_system": True},
    )
    in_recycle = await anchor.virtual_folders.filter(id=recycle_folder.id).exists()
    if not in_recycle:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="锚点不在回收站")

    target_folder = await VirtualFolder.filter(id=payload.folder_id).first()
    if not target_folder:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="虚拟文件夹不存在")
    if target_folder.name == ALL_FOLDER_NAME or target_folder.is_system:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不能恢复到“全部资料”或系统文件夹")

    all_folder, _ = await VirtualFolder.get_or_create(
        name=ALL_FOLDER_NAME,
        defaults={"description": "系统默认文件夹", "is_system": True},
    )

    await anchor.virtual_folders.clear()
    await anchor.virtual_folders.add(all_folder, target_folder)
    await anchor.refresh_from_db()

    return AnchorResponse(
        id=anchor.id,
        name=anchor.name,
        path=anchor.path,
        description=anchor.description,
        is_valid=anchor.is_valid,
        create_time=anchor.create_time,
        update_time=anchor.update_time,
        virtual_folder_ids=[all_folder.id, target_folder.id],
        tag_ids=[],
    )


class AnchorBindFolders(BaseModel):
    """请求体：为锚点新增绑定的虚拟文件夹。"""

    folder_ids: list[int] = Field(..., min_length=1, description="待绑定的虚拟文件夹 ID 列表（不可包含系统/全部/回收站）")


@router.post("/{anchor_id}/bindFolders", response_model=AnchorResponse)
async def bind_anchor_folders(anchor_id: int, payload: AnchorBindFolders) -> AnchorResponse:
    """
    为资料锚点新增虚拟文件夹绑定（追加，不移除已有绑定）。
    - 不可绑定系统文件夹/“全部资料”/“回收站”。
    - 锚点如果在回收站，需先恢复再绑定。
    """
    anchor = await FileAnchor.filter(id=anchor_id).first()
    if not anchor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="资料锚点不存在")

    recycle_folder = await VirtualFolder.get_or_none(name=RECYCLE_FOLDER_NAME)
    if recycle_folder and await anchor.virtual_folders.filter(id=recycle_folder.id).exists():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="锚点在回收站，需先恢复后再绑定文件夹")

    folder_ids = list(dict.fromkeys(payload.folder_ids))
    targets = await VirtualFolder.filter(id__in=folder_ids)
    if len(targets) != len(folder_ids):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="部分虚拟文件夹不存在")

    invalid_targets = [f.name for f in targets if f.is_system or f.name in (ALL_FOLDER_NAME, RECYCLE_FOLDER_NAME)]
    if invalid_targets:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"不可绑定系统文件夹: {', '.join(invalid_targets)}")

    all_folder, _ = await VirtualFolder.get_or_create(
        name=ALL_FOLDER_NAME,
        defaults={"description": "系统默认文件夹", "is_system": True},
    )

    await anchor.virtual_folders.add(*targets)
    # 确保仍绑定“全部资料”
    if not await anchor.virtual_folders.filter(id=all_folder.id).exists():
        await anchor.virtual_folders.add(all_folder)

    await anchor.refresh_from_db()
    bound_folder_ids = await anchor.virtual_folders.all().values_list("id", flat=True)
    tag_ids = await anchor.tags.all().values_list("id", flat=True)

    return AnchorResponse(
        id=anchor.id,
        name=anchor.name,
        path=anchor.path,
        description=anchor.description,
        is_valid=anchor.is_valid,
        create_time=anchor.create_time,
        update_time=anchor.update_time,
        virtual_folder_ids=list(bound_folder_ids),
        tag_ids=list(tag_ids),
    )


class AnchorUpdate(BaseModel):
    """请求体：更新资料锚点名称/描述。"""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None


class AnchorAddTags(BaseModel):
    """请求体：为资料锚点添加标签。"""

    names: list[str] = Field(..., min_length=1, description="要添加的标签名称列表（去重后处理）")


@router.patch("/{anchor_id}", response_model=AnchorResponse)
async def update_anchor(anchor_id: int, payload: AnchorUpdate) -> AnchorResponse:
    """
    更新资料锚点名称与描述，并刷新更新时间。
    """
    anchor = await FileAnchor.filter(id=anchor_id).first()
    if not anchor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="资料锚点不存在")

    if payload.name is not None:
        anchor.name = payload.name
    if payload.description is not None:
        anchor.description = payload.description

    await anchor.save()
    await anchor.refresh_from_db()

    folder_ids = await anchor.virtual_folders.all().values_list("id", flat=True)
    tag_ids = await anchor.tags.all().values_list("id", flat=True)

    return AnchorResponse(
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

# --------------资料锚点与标签相关操作--------------
@router.post("/{anchor_id}/tags", response_model=AnchorResponse, status_code=status.HTTP_201_CREATED)
async def add_tags_to_anchor(anchor_id: int, payload: AnchorAddTags) -> AnchorResponse:
    """
    为资料锚点添加标签：
    - 已存在的直接绑定，不存在的先创建后绑定。
    - 返回锚点最新的标签列表。
    """
    anchor = await FileAnchor.filter(id=anchor_id).first()
    if not anchor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="资料锚点不存在")

    names = list(dict.fromkeys([n.strip() for n in payload.names if n.strip()]))
    if not names:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="标签名称不能为空")

    existing_tags = await anchor.tags.all().values_list("id", flat=True)
    existing_tag_ids = set(existing_tags)

    existing = await Tag.filter(name__in=names)
    existing_map = {t.name: t for t in existing}

    to_create = [n for n in names if n not in existing_map]
    created: list[Tag] = []
    for name in to_create:
        tag = await Tag.create(name=name)
        created.append(tag)

    to_bind = [tag for tag in list(existing_map.values()) + created if tag.id not in existing_tag_ids]

    if to_bind:
        await anchor.tags.add(*to_bind)
        for tag in to_bind:
            tag.use_count += 1
            await tag.save()

    await anchor.refresh_from_db()

    tag_ids = await anchor.tags.all().values_list("id", flat=True)
    folder_ids = await anchor.virtual_folders.all().values_list("id", flat=True)

    return AnchorResponse(
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


@router.delete("/{anchor_id}/tags/{tag_id}", response_model=AnchorResponse)
async def remove_tag_from_anchor(anchor_id: int, tag_id: int) -> AnchorResponse:
    """
    从资料锚点解除指定标签绑定，并将标签 use_count 减 1（不低于 0）。
    """
    anchor = await FileAnchor.filter(id=anchor_id).first()
    if not anchor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="资料锚点不存在")

    tag = await Tag.filter(id=tag_id).first()
    if not tag:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="标签不存在")

    bound = await anchor.tags.filter(id=tag_id).exists()
    if not bound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="锚点未绑定该标签")

    await anchor.tags.remove(tag)
    if tag.use_count > 0:
        tag.use_count -= 1
        await tag.save()

    await anchor.refresh_from_db()

    tag_ids = await anchor.tags.all().values_list("id", flat=True)
    folder_ids = await anchor.virtual_folders.all().values_list("id", flat=True)

    return AnchorResponse(
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
