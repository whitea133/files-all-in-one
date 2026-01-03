from fastapi import APIRouter
import webview

"""
前端点击后，触发 pywebview 创建子窗口的后端路由文件，打开对应的子窗口。
注意：需要在 webview.start 之后调用，否则无法创建窗口。
"""

router = APIRouter(prefix="/windows", tags=["windows"])
_setting_window = None  # 控制只能打开一个设置窗口，单例控制


@router.get("/setting")
def open_setting_window():
    """
    打开“设置”子窗口，加载前端的 /setting 页面。
    """
    # 静态版
    default_url = "http://localhost:8000/setting"
    # 开发版（如需改用前端 dev server，取消下一行注释）
    # default_url = "http://localhost:5173/static/setting"

    window_url = default_url

    global _setting_window
    if _setting_window:
        try:
            _setting_window.restore()
            _setting_window.focus()
        except Exception:
            pass
        return {"status": "ok", "url": window_url, "existing": True}

    _setting_window = webview.create_window("设置", url=window_url, width=900, height=740, x=450, y=120,
                                            resizable=False, on_top=True)
    print("窗口位置: ", webview.screens[0])

    def _on_closed():
        global _setting_window
        _setting_window = None

    _setting_window.events.closed += _on_closed # 注册函数，当窗口被关闭时自动触发回调函数_on_closed

    
    return {"status": "ok", "url": window_url}
