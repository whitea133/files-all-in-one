"""
pywebview JS 接口桥接。
"""

from typing import Any

import webview


class Bridge:
    """
    提供给前端调用的 JS API。
    - open_file_dialog: 调起系统文件选择器，返回选中的文件路径列表。
    """

    def open_file_dialog(self, folder_id: int | None = None) -> dict[str, Any]:
        """
        打开系统文件选择对话框。

        Args:
            folder_id: 选中文件后可供前端使用的上下文（如目标虚拟文件夹 id），此处仅原样返回。

        Returns:
            dict: {
                "files": ["/abs/path/file1", ...],
                "folder_id": folder_id
            }
        """
        window = webview.active_window()
        if not window:
            return {"files": [], "folder_id": folder_id, "error": "window_not_ready"}

        try:
            file_paths = window.create_file_dialog(
                webview.OPEN_DIALOG,
                allow_multiple=True,
                file_types=("All files (*.*)",),
            )
        except Exception as exc:  # pragma: no cover - UI 相关异常
            return {"files": [], "folder_id": folder_id, "error": str(exc)}

        return {
            "files": file_paths or [],
            "folder_id": folder_id,
        }
