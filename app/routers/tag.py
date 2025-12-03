from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict

from models import FileAnchor, Tag, VirtualFolder
from routers.anchor import AnchorResponse

router = APIRouter(prefix="/tags", tags=["tags"])


class TagResponse(BaseModel):
    id: int
    name: str
    use_count: int
    create_time: datetime

    model_config = ConfigDict(from_attributes=True)


@router.get("/", response_model=list[TagResponse])
async def list_tags() -> list[TagResponse]:
    """输出全部标签列表。"""
    tags = await Tag.all().order_by("id")
    return [TagResponse.model_validate(t) for t in tags]


@router.get("/popular", response_model=list[TagResponse])
async def list_tags_by_usage() -> list[TagResponse]:
    """按 use_count 从高到低输出标签列表。"""
    tags = await Tag.all().order_by("-use_count", "id")
    return [TagResponse.model_validate(t) for t in tags]


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag(tag_id: int) -> None:
    """
    删除标签，并解除所有锚点绑定。
    """
    tag = await Tag.filter(id=tag_id).first()
    if not tag:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="标签不存在")

    await tag.file_anchors.clear()
    await tag.delete()


@router.get("/anchors", response_model=list[AnchorResponse])
async def list_anchors_by_tags(
    tag_names: list[str] = Query(..., description="标签名称列表，多个标签间为 AND 关系"),
    folder_id: int = Query(..., description="当前所在虚拟文件夹 ID"),
) -> list[AnchorResponse]:
    """
    按多标签 + 文件夹过滤资料锚点（AND 关系：必须同时包含所有指定标签）。
    标签不存在则返回空列表。
    """
    folder = await VirtualFolder.filter(id=folder_id).first()
    if not folder:
        raise HTTPException(status_code=404, detail="虚拟文件夹不存在")

    names = [n.strip() for n in tag_names if n.strip()]
    if not names:
        raise HTTPException(status_code=400, detail="标签名称不能为空")

    tags = await Tag.filter(name__in=names)
    if len(tags) != len(names):
        return []

    anchors = await FileAnchor.filter(virtual_folders__id=folder_id)
    for tag in tags:
        anchors = anchors.filter(tags__id=tag.id)
    anchors = await anchors.distinct()

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
