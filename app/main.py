"""FastAPI 应用入口"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import init_db
from app.templates import templates
from app.routers import test_cases, test_plans, test_plan_items, import_export


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动时初始化数据库"""
    await init_db()
    yield


app = FastAPI(
    title=settings.APP_TITLE,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# 静态文件
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


# ── 全局异常处理 ──
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP 异常处理"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"data": None, "message": exc.detail, "errors": [exc.detail]},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """通用异常处理"""
    import traceback
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"data": None, "message": "服务器内部错误", "errors": [str(exc)]},
    )


# ── 注册 API 路由 ──
app.include_router(test_cases.router)
app.include_router(test_cases.page_router)
app.include_router(test_plans.router)
app.include_router(test_plans.page_router)
app.include_router(test_plan_items.router)
app.include_router(import_export.router)
app.include_router(import_export.page_router)


# ── 首页仪表盘 ──
@app.get("/app/", response_class=HTMLResponse)
async def home_page(request: Request):
    """首页仪表盘"""
    return templates.TemplateResponse(request, "pages/dashboard.html", {})


@app.get("/")
async def root():
    """根路径重定向到首页"""
    return RedirectResponse(url="/app/", status_code=302)
