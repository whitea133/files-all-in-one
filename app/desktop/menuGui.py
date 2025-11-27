import webview
import webview.menu as wm

def create_SettingWin():
    """
        弹出设置页面，提供用户进行相关设置
    """
    settingWin = webview.create_window(
        '设置',
        html='<h1>设置页面</h1><p>这里是设置内容。</p>',
        width=400,
        height=300,
        resizable=False,
        frameless=False,
    )
    return settingWin

def create_AboutWin():
    """
        弹出关于页面，展示开发者信息
    """
    aboutWin = webview.create_window(
        '关于',
        html='<h1>关于本应用</h1><p>开发者: Your Name</p>',
        width=400,
        height=300,
        resizable=False,
        frameless=False,
    )
    return aboutWin

def do_nothing():
    pass

def open_file_dialog():
    active_window = webview.active_window()
    active_window.create_file_dialog(webview.SAVE_DIALOG, directory='/', save_filename='test.file')

topMenu = [
    wm.Menu(
        '编辑', 
        [
            wm.MenuAction('设置', create_SettingWin),
            wm.Menu(
                'Random',
                [
                    wm.MenuAction('测试按钮1', do_nothing),
                    wm.MenuAction('打开文件', open_file_dialog),
                ],
            ),
            wm.MenuSeparator(), # MenuSeparator只是占位符，等待其他功能替换
        ],
        
    ),
    wm.Menu('帮助', [wm.MenuAction('开发者信息', create_AboutWin)]),

]

if __name__ == '__main__':
    window_1 = webview.create_window(
        'Application Menu Example', html='<h1>welcome to test</h1>'
    )

    webview.start(menu=topMenu)