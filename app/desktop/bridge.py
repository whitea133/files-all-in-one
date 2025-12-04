"""
pywebview JS 接口桥接。
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import webview


class Bridge:
    """
    提供给前端调用的 JS API。
    - open_file_dialog: 调起系统文件选择器，返回选中的文件路径列表。
    - open_file: 使用系统默认程序打开文件。
    """

    def open_file_dialog(self, folder_id: int | None = None) -> dict[str, Any]:
        """
        打开系统文件选择对话框。
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

    def open_file(self, path: str) -> dict[str, Any]:
        """
        使用系统默认程序打开文件。
        """
        if not path:
            return {"success": False, "error": "empty_path"}

        p = Path(path).expanduser()
        if not p.exists():
            return {"success": False, "error": "not_found"}
        if not p.is_file():
            return {"success": False, "error": "not_file"}

        try:
            if sys.platform.startswith("win"):
                os.startfile(p)  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(p)])
            else:
                subprocess.Popen(["xdg-open", str(p)])
            return {"success": True}
        except Exception as exc:  # pragma: no cover - 平台相关异常
            return {"success": False, "error": str(exc)}
