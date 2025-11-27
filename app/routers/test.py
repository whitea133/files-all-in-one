from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

# 创建一个APIRouter实例，用于定义API的路由
router = APIRouter()

# 初始化Jinja2Templates实例，指定模板文件的目录
templates = Jinja2Templates(directory='templates')

# 定义根路径的GET请求处理函数
# 返回index.html模板，同时传入一个空的request对象
@router.get("/")
async def get():
    # 使用TemplateResponse方法渲染index.html模板，并传递一个空的request对象
    return templates.TemplateResponse("index.html", {"request": {}})

# 定义/test路径的GET请求处理函数
# 在控制台打印"test"，并返回"test"作为HTTP响应
@router.get("/test")
async def test():
    # 在控制台中打印 "test"
    print("test")
    # 返回 "test" 作为响应
    return "test"
