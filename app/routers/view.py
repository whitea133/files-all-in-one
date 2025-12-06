from fastapi import APIRouter
import webview

"""
前端点击后，触发 pywebview 创建子窗口的后端路由文件，打开对应的子窗口。
注意：需要在 webview.start 之后调用，否则无法创建窗口。
"""

router = APIRouter(prefix="/windows", tags=["windows"])


@router.get("/setting")
def open_setting_window():
    """
    打开“设置”子窗口，加载前端的 /setting 页面。
    """
    # 静态版
    # default_url = "http://localhost:8000/setting"
    # 开发版（如需改用前端 dev server，取消下一行注释）
    default_url = "http://localhost:5173/static/setting"

    window_url = default_url
    webview.create_window("设置", url=window_url, width=900, height=640, resizable=True)
    return {"status": "ok", "url": window_url}
