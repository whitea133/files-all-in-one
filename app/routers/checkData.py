from pathlib import Path

from fastapi import APIRouter, HTTPException, status

from models import FileAnchor, VirtualFolder


router = APIRouter(prefix="/check", tags=["check"])


@router.post("/{folder_id}/anchors")
async def check_folder_anchors(folder_id: int):
    """
    检查指定虚拟文件夹下的资料锚点路径是否存在，更新 is_valid 状态并返回结果列表。
    """
    folder = await VirtualFolder.filter(id=folder_id).first()
    if not folder:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="虚拟文件夹不存在")

    anchors = await FileAnchor.filter(virtual_folders__id=folder_id).all()
    results = []
    for anchor in anchors:
        exists = Path(anchor.path).expanduser().exists()
        if anchor.is_valid != exists:
            anchor.is_valid = exists
            await anchor.save()
        results.append({"id": anchor.id, "path": anchor.path, "is_valid": anchor.is_valid})

    return {"folder_id": folder_id, "anchors": results}
